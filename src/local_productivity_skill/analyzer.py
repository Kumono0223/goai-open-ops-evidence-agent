"""Deterministic CSV analysis primitives used by the local Skill."""

from __future__ import annotations

import csv
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


DATE_HINTS = ("date", "time", "日期", "时间", "week", "day")


def _read_rows(csv_path: str | Path) -> list[dict[str, str]]:
    path = Path(csv_path)
    if path.suffix.lower() != ".csv":
        raise ValueError("only .csv files are supported")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV must contain a header row")
        return [dict(row) for row in reader]


def _number(value: str) -> float | None:
    text = (value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _columns(rows: list[dict[str, str]]) -> list[str]:
    return list(rows[0].keys()) if rows else []


def _numeric_columns(rows: list[dict[str, str]]) -> list[str]:
    columns = _columns(rows)
    return [c for c in columns if sum(_number(r.get(c, "")) is not None for r in rows) >= max(1, len(rows) // 2)]


def _date_columns(rows: list[dict[str, str]]) -> list[str]:
    result: list[str] = []
    for column in _columns(rows):
        hint = column.lower()
        if not any(token in hint for token in DATE_HINTS):
            continue
        parsed = 0
        for row in rows[:50]:
            value = (row.get(column) or "").strip()
            if not value:
                continue
            try:
                datetime.fromisoformat(value.replace("/", "-").replace("Z", "+00:00"))
                parsed += 1
            except ValueError:
                pass
        if parsed:
            result.append(column)
    return result


def profile_csv(csv_path: str | Path) -> dict[str, Any]:
    rows = _read_rows(csv_path)
    columns = _columns(rows)
    numeric = set(_numeric_columns(rows))
    profile: list[dict[str, Any]] = []
    for column in columns:
        values = [r.get(column, "") for r in rows]
        numbers = [_number(v) for v in values]
        clean = [n for n in numbers if n is not None]
        item: dict[str, Any] = {
            "name": column,
            "kind": "numeric" if column in numeric else "categorical",
            "missing": sum(not (v or "").strip() for v in values),
            "unique": len(set(v for v in values if v)),
        }
        if clean:
            item.update({"min": min(clean), "max": max(clean), "mean": round(sum(clean) / len(clean), 4)})
        profile.append(item)
    return {"rows": len(rows), "columns": profile, "numeric_columns": sorted(numeric), "date_columns": _date_columns(rows)}


def _choose_dimension(rows: list[dict[str, str]], query: str) -> str | None:
    q = query.lower()
    numeric = set(_numeric_columns(rows))
    for column in _columns(rows):
        if column in numeric:
            continue
        if column.lower() in q:
            return column
    dates = set(_date_columns(rows))
    non_numeric = [c for c in _columns(rows) if c not in numeric and c not in dates]
    if not non_numeric:
        non_numeric = [c for c in _columns(rows) if c not in numeric]
    return non_numeric[0] if non_numeric else None


def _choose_metric(rows: list[dict[str, str]], query: str) -> str | None:
    numeric = _numeric_columns(rows)
    q = query.lower()
    for column in numeric:
        if column.lower() in q:
            return column
    preferred = ("revenue", "sales", "amount", "收入", "销售", "金额", "orders", "订单", "conversion", "转化")
    for hint in preferred:
        for column in numeric:
            if hint in column.lower():
                return column
    return numeric[0] if numeric else None


def _intent(query: str) -> str:
    q = query.lower()
    if any(token in q for token in ("异常", "离群", "anomal", "outlier")):
        return "anomaly"
    if any(token in q for token in ("趋势", "走势", "trend", "按周", "按日")):
        return "trend"
    if any(token in q for token in ("top", "最高", "最好", "排名", "排行")):
        return "top"
    return "summary"


def analyze_csv(csv_path: str | Path, query: str = "", *, z_threshold: float = 2.0) -> dict[str, Any]:
    rows = _read_rows(csv_path)
    if not rows:
        return {"intent": "summary", "metrics": {"rows": 0}, "findings": [], "recommendations": []}
    intent = _intent(query)
    metric = _choose_metric(rows, query)
    dimension = _choose_dimension(rows, query)
    result: dict[str, Any] = {"intent": intent, "source": Path(csv_path).name, "metrics": {"rows": len(rows)}, "findings": [], "recommendations": []}
    if not metric:
        result["findings"].append("没有识别到数值指标，请在 query 中指定数值列。")
        return result
    values = [(r, _number(r.get(metric, ""))) for r in rows]
    clean = [(r, n) for r, n in values if n is not None]
    result["metrics"].update({"metric": metric, "sum": round(sum(n for _, n in clean), 4), "mean": round(sum(n for _, n in clean) / len(clean), 4), "min": min(n for _, n in clean), "max": max(n for _, n in clean)})
    if intent == "top" and dimension:
        grouped: dict[str, float] = defaultdict(float)
        for row, number in clean:
            grouped[row.get(dimension, "(empty)")] += number
        result["breakdown"] = [{"group": key, "value": round(value, 4)} for key, value in sorted(grouped.items(), key=lambda item: item[1], reverse=True)[:10]]
        if result["breakdown"]:
            result["findings"].append(f"{result['breakdown'][0]['group']} 的 {metric} 最高。")
    elif intent == "trend":
        date_column = _date_columns(rows)[0] if _date_columns(rows) else dimension
        if date_column:
            grouped = defaultdict(float)
            for row, number in clean:
                grouped[row.get(date_column, "(empty)")] += number
            result["breakdown"] = [{"group": key, "value": round(value, 4)} for key, value in sorted(grouped.items())]
            if len(result["breakdown"]) >= 2:
                delta = result["breakdown"][-1]["value"] - result["breakdown"][0]["value"]
                result["findings"].append(f"{metric} 从首个周期到末个周期变化 {round(delta, 4)}。")
        else:
            result["findings"].append("没有识别到日期/周期列，无法计算趋势。")
    elif intent == "anomaly":
        mean = sum(n for _, n in clean) / len(clean)
        variance = sum((n - mean) ** 2 for _, n in clean) / len(clean)
        std = math.sqrt(variance)
        if z_threshold <= 0:
            raise ValueError("z_threshold must be positive")
        threshold = float(z_threshold)
        anomalies = [] if std == 0 else [{"row": row, "value": number, "z_score": round((number - mean) / std, 3)} for row, number in clean if abs((number - mean) / std) >= threshold]
        result["anomalies"] = anomalies
        result["findings"].append(f"按 |z-score| >= {threshold} 检测到 {len(anomalies)} 个异常值。")
    else:
        result["findings"].append(f"{metric} 平均值为 {result['metrics']['mean']}，范围 {result['metrics']['min']}–{result['metrics']['max']}。")
    result["recommendations"] = ["核对数据时间范围与缺失值，再结合业务目标决定行动。", "保留本次 query、指标口径和输入文件版本，确保复盘可复现。"]
    return result
