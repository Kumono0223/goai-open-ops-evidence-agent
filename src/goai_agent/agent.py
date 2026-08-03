"""Deterministic industrial-operations evidence agent for the GOAI demo."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.local_productivity_skill.analyzer import analyze_csv, profile_csv


METHOD_VERSION = "2026.08-evidence-v2"
POLICY_VERSION = "ops-review-policy-1.0"
REQUIRED_COLUMNS = ("date", "machine", "downtime_hours", "defects")


@dataclass(frozen=True)
class ReviewPolicy:
    z_threshold: float = 2.0
    critical_z: float = 2.5
    critical_downtime_hours: float = 6.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": POLICY_VERSION,
            "z_threshold": self.z_threshold,
            "critical_z": self.critical_z,
            "critical_downtime_hours": self.critical_downtime_hours,
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_and_validate(path: Path) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in fields]
        if missing:
            raise ValueError(f"missing required columns: {', '.join(missing)}")
        rows = [dict(row) for row in reader]
    if not rows:
        raise ValueError("CSV must contain at least one observation")

    issues: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=2):
        for column in ("date", "machine"):
            if not (row.get(column) or "").strip():
                issues.append({"row": index, "column": column, "issue": "missing_value"})
        for column in ("downtime_hours", "defects"):
            try:
                value = float((row.get(column) or "").strip())
                if value < 0:
                    issues.append({"row": index, "column": column, "issue": "negative_value"})
            except ValueError:
                issues.append({"row": index, "column": column, "issue": "not_numeric"})
    return rows, issues


def _trend_evidence(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_period: dict[str, float] = defaultdict(float)
    for row in rows:
        try:
            by_period[row["date"]] += float(row["downtime_hours"])
        except (KeyError, ValueError):
            continue
    periods = sorted(by_period)
    series = [{"period": period, "downtime_hours": round(by_period[period], 4)} for period in periods]
    if len(series) < 2:
        return {"series": series, "latest_delta_hours": None, "latest_delta_percent": None}
    previous, latest = series[-2], series[-1]
    delta = latest["downtime_hours"] - previous["downtime_hours"]
    percent = None if previous["downtime_hours"] == 0 else delta / previous["downtime_hours"] * 100
    return {
        "series": series,
        "latest_delta_hours": round(delta, 4),
        "latest_delta_percent": None if percent is None else round(percent, 2),
    }


def _incident_id(digest: str, machine: str, date: str) -> str:
    value = hashlib.sha256(f"{digest}:{machine}:{date}:downtime_hours".encode("utf-8")).hexdigest()
    return f"INC-{value[:10].upper()}"


def _build_incidents(
    anomaly: dict[str, Any], digest: str, policy: ReviewPolicy
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evidence: list[dict[str, Any]] = []
    incidents: list[dict[str, Any]] = []
    for index, item in enumerate(anomaly.get("anomalies", []), start=1):
        row = item.get("row", {})
        machine = str(row.get("machine", "unknown"))
        date = str(row.get("date", "unknown"))
        downtime = float(item.get("value", 0))
        defects = float(row.get("defects", 0) or 0)
        z_score = float(item.get("z_score", 0))
        evidence_id = f"EV-{index:03d}"
        severity = (
            "critical"
            if abs(z_score) >= policy.critical_z or downtime >= policy.critical_downtime_hours
            else "high"
        )
        risk_score = min(100, round(20 + abs(z_score) * 18 + downtime * 4 + defects * 1.5))
        evidence.append(
            {
                "evidence_id": evidence_id,
                "kind": "statistical_outlier",
                "machine": machine,
                "period": date,
                "metric": "downtime_hours",
                "observed": downtime,
                "z_score": z_score,
                "threshold": policy.z_threshold,
                "source_row": row,
            }
        )
        incidents.append(
            {
                "incident_id": _incident_id(digest, machine, date),
                "machine": machine,
                "period": date,
                "severity": severity,
                "risk_score": risk_score,
                "state": "proposed",
                "decision": "human_approval_required",
                "evidence_refs": [evidence_id],
                "proposed_actions": [
                    {
                        "action": "核对对应时间窗的维护工单、传感器日志和排产变更",
                        "owner_role": "值班工程师",
                        "state": "awaiting_human_approval",
                    },
                    {
                        "action": "确认异常可复现后创建维护工单，并在下一周期验证",
                        "owner_role": "设备负责人",
                        "state": "blocked_until_review",
                    },
                ],
            }
        )
    return evidence, incidents


def run_workflow(
    csv_path: str | Path, *, policy: ReviewPolicy | None = None
) -> dict[str, Any]:
    """Run the evidence workflow without performing any production-side action."""

    active_policy = policy or ReviewPolicy()
    path = Path(csv_path)
    rows, data_issues = _read_and_validate(path)
    digest = _sha256(path)
    profile = profile_csv(path)
    anomaly = analyze_csv(
        path,
        "找出 downtime_hours 异常设备",
        z_threshold=active_policy.z_threshold,
    )
    trend = analyze_csv(path, "按 date 看 downtime_hours 趋势")
    trend_evidence = _trend_evidence(rows)
    evidence, incidents = _build_incidents(anomaly, digest, active_policy)

    if trend_evidence["series"]:
        evidence.append(
            {
                "evidence_id": f"EV-{len(evidence) + 1:03d}",
                "kind": "period_trend",
                "metric": "downtime_hours",
                **trend_evidence,
            }
        )

    findings = list(anomaly.get("findings", [])) + list(trend.get("findings", []))
    if trend_evidence["latest_delta_percent"] is not None:
        findings.append(
            "最近周期停机时长环比 "
            f"{trend_evidence['latest_delta_percent']:+.2f}%（{trend_evidence['latest_delta_hours']:+.2f} 小时）。"
        )

    return {
        "agent": "open-ops-evidence-agent",
        "methodology_version": METHOD_VERSION,
        "policy": active_policy.as_dict(),
        "input_evidence": {
            "file_name": path.name,
            "sha256": digest,
            "bytes": path.stat().st_size,
            "rows": len(rows),
            "required_columns": list(REQUIRED_COLUMNS),
            "data_quality_issues": data_issues,
        },
        "workflow": [
            {"step": "ingest", "state": "completed", "evidence": "input_evidence.sha256"},
            {"step": "profile", "state": "completed", "evidence": "profile"},
            {"step": "detect", "state": "completed", "evidence": "evidence"},
            {"step": "propose", "state": "completed", "evidence": "incidents"},
            {"step": "approve_and_execute", "state": "blocked", "reason": "human_review_required"},
        ],
        "profile": profile,
        "tool_calls": [
            {"tool": "profile_csv", "status": "completed"},
            {"tool": "analyze_csv", "query": "找出 downtime_hours 异常设备", "status": "completed"},
            {"tool": "analyze_csv", "query": "按 date 看 downtime_hours 趋势", "status": "completed"},
        ],
        "evidence": evidence,
        "incidents": incidents,
        "findings": findings,
        "priority_machines": [incident["machine"] for incident in incidents],
        "human_review_required": True,
        "production_actions_executed": False,
        "limitations": [
            "z-score 是小样本统计启发式，不构成设备根因诊断。",
            "示例数据为合成数据；真实部署前必须接入权限、审计和工单系统。",
            "Agent 只提出行动草案，不会自动停机、派单或更改生产系统。",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    input_info = report["input_evidence"]
    lines = [
        "# Open Ops Evidence Report",
        "",
        f"- Method: `{report['methodology_version']}`",
        f"- Policy: `{report['policy']['version']}`",
        f"- Input: `{input_info['file_name']}`",
        f"- SHA-256: `{input_info['sha256']}`",
        f"- Rows: {input_info['rows']}",
        "- Production actions executed: **No**",
        "",
        "## Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in report["findings"])
    lines.extend(["", "## Proposed incidents", ""])
    if not report["incidents"]:
        lines.append("- No incident met the configured review threshold.")
    for incident in report["incidents"]:
        lines.append(
            f"- `{incident['incident_id']}` · {incident['machine']} · "
            f"{incident['severity']} · risk {incident['risk_score']} · {incident['decision']}"
        )
    lines.extend(["", "## Safety boundary", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="GOAI Open Ops Evidence Agent")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--z-threshold", type=float, default=2.0)
    parser.add_argument("--output-json")
    parser.add_argument("--output-markdown")
    args = parser.parse_args()
    report = run_workflow(args.csv, policy=ReviewPolicy(z_threshold=args.z_threshold))
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output_json:
        Path(args.output_json).write_text(payload + "\n", encoding="utf-8")
    if args.output_markdown:
        Path(args.output_markdown).write_text(render_markdown(report), encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
