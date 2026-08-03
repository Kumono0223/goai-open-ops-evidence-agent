---
name: open-ops-evidence-agent
description: "GOAI Boundless Agents 候选项目：对本地工业运营数据执行可复现的异常核验、任务分解和行动闭环。"
version: 0.2.0
---

# Open Ops Evidence Agent

面向真实工业运营流程的本地 Agent Demo。它不做泛聊天，而是把 CSV 观测转成“输入指纹—工具证据—事件草案—人工批准”闭环。

## Contract

- Validate `date,machine,downtime_hours,defects`.
- Record the input SHA-256 and method/policy versions.
- Cite deterministic evidence IDs in every proposed incident.
- Export JSON/Markdown without executing production actions.
- Stop at the human-approval gate.
