# Open Ops Evidence Agent

GOAI `Boundless Agents / 无界应用` 候选作品：一个本地优先的工业运维证据 Agent。输入设备/工单 CSV，自动完成数据健康检查、停机趋势、异常设备识别和下一步复核清单。

## 场景闭环

1. 运营人员导入本地导出的设备观测表。
2. Agent 检查字段、缺失值和异常值，生成可复现证据。
3. 结合趋势与异常结果，输出需要复核的设备、时间窗和建议动作。
4. 复核人员可按 JSON 报告追溯输入文件、指标口径和阈值。

## 运行

```powershell
python -m unittest discover -s tests -v
python -m src.goai_agent.agent --csv examples/maintenance.csv
```

无需云 API；上层 Agent 可通过本地 Python 模块或复用的 localhost 服务调用。示例数据为合成数据，不代表真实生产决策。

