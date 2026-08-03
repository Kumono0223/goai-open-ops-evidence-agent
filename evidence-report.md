# Open Ops Evidence Report

- Method: `2026.08-evidence-v2`
- Policy: `ops-review-policy-1.0`
- Input: `maintenance.csv`
- SHA-256: `e6701c0ea79e9cb04e18b254b02c46d245cfb17e68417d60af5b8fe3b91efe55`
- Rows: 9
- Production actions executed: **No**

## Findings

- 按 |z-score| >= 2.0 检测到 1 个异常值。
- downtime_hours 从首个周期到末个周期变化 7.2。
- 最近周期停机时长环比 +167.50%（+6.70 小时）。

## Proposed incidents

- `INC-5782EC6871` · M-02 · critical · risk 100 · human_approval_required

## Safety boundary

- z-score 是小样本统计启发式，不构成设备根因诊断。
- 示例数据为合成数据；真实部署前必须接入权限、审计和工单系统。
- Agent 只提出行动草案，不会自动停机、派单或更改生产系统。
