from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.local_productivity_skill.analyzer import analyze_csv, profile_csv


def run_workflow(csv_path: str | Path) -> dict[str, Any]:
    profile = profile_csv(csv_path)
    anomaly = analyze_csv(csv_path, "找出 downtime_hours 异常设备")
    trend = analyze_csv(csv_path, "按 date 看 downtime_hours 趋势")
    findings = list(anomaly.get("findings", [])) + list(trend.get("findings", []))
    devices = [item.get("row", {}).get("machine") for item in anomaly.get("anomalies", []) if item.get("row", {}).get("machine")]
    actions = [
        "由值班工程师复核异常设备对应时间窗的工单与传感器日志。",
        "若异常可复现，建立维护工单并在下一周期重新导出数据验证。",
        "保留输入 CSV、指标口径和 z-score 阈值，避免只凭主观印象决策。",
    ]
    return {
        "agent": "open-ops-evidence-agent",
        "input": Path(csv_path).name,
        "profile": profile,
        "evidence": {"anomaly": anomaly, "trend": trend},
        "findings": findings,
        "priority_machines": devices,
        "next_actions": actions,
        "human_review_required": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="GOAI Open Ops Evidence Agent")
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    print(json.dumps(run_workflow(args.csv), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
