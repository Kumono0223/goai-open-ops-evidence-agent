---
domain:
- AutoML
tags:
- Agent
- Industrial Operations
datasets:
  evaluation: []
  test: []
  train: []
models: []
deployspec:
  entry_file: web/index.html
license: MIT License
---

# Open Ops Evidence Agent

GOAI `Boundless Agents / 无界应用` 候选作品：一个本地优先、证据优先、人工把关的工业运维 Agent。输入设备观测 CSV，输出数据指纹、统计证据、事件优先级、行动草案和完整审计轨迹；不会自动停机、派单或修改生产系统。

## 为什么不是普通 CSV 报表

Agent 执行一个可验证的任务闭环：

1. 校验输入契约，记录文件 SHA-256、行数和数据质量问题；
2. 调用确定性 profile、异常检测和周期趋势工具；
3. 将每个异常转成带 `evidence_id` 的证据；
4. 生成确定性 `incident_id`、严重度、风险分数与责任角色；
5. 在 `approve_and_execute` 节点强制停止，等待人工批准；
6. 导出 JSON/Markdown 证据包，供复盘、答辩或后续系统接入。

方法版本为 `2026.08-evidence-v2`，策略版本为 `ops-review-policy-1.0`。

## 快速验证

```powershell
python -m unittest discover -s tests -v
python -m src.goai_agent.agent --csv examples/maintenance.csv `
  --output-json evidence-report.json `
  --output-markdown evidence-report.md
```

预期结果：识别 `M-02` 为 `critical` 待复核事件，输入指纹为 `e6701c0e…`，最近周期停机时长环比 `+167.50%`，并明确 `production_actions_executed=false`。

无需后端的交互式演示位于 `web/index.html`，可直接在浏览器打开。页面不加载外部脚本、不发送网络请求，可调整 z-score 阈值并下载完整 JSON 证据包。

## 项目结构

- `src/goai_agent`：证据编排、事件单、审计轨迹、Markdown 导出；
- `src/local_productivity_skill`：可复用 CSV profile/趋势/Top-N/z-score 工具与本地 HTTP 接口；
- `web`：自包含静态 Demo；
- `examples`：合成维护数据和运营数据；
- `tests`：Agent 契约、确定性、安全门槛和 Web 交付测试；
- `ARCHITECTURE.md`、`PRESENTATION.md`、`SUBMISSION.md`：架构与参赛材料。

## 安全、数据和许可

- 示例全部为合成数据，不含真实设备、员工或客户信息。
- z-score 只提供统计复核信号，不是根因诊断、预测性维护结论或生产控制指令。
- 真实部署前必须接入身份权限、数据分级、审计日志、CMMS/工单审批和回滚机制。
- Python 与 Web Demo 均只使用标准库/浏览器原生能力；项目代码采用 MIT License。

## 迭代路线

复赛阶段可接入企业授权知识库、CMMS 沙箱、事件时间线、因果假设评审和基于角色的批准；保持“模型可替换、工具确定性、证据可追溯、生产动作人工批准”的基本原则。
