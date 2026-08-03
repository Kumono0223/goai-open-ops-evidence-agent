# GOAI submission checklist

## Track and project

- Track: Boundless Agents / 无界应用
- Project: Open Ops Evidence Agent
- Target user: equipment operations and quality teams in small/medium manufacturers
- Method: `2026.08-evidence-v2`

## Initial-round deliverables

- [x] Project description and problem statement
- [x] Architecture and Agent workflow
- [x] Runnable Python demo
- [x] Self-contained browser demo
- [x] Synthetic example data
- [x] Reproducible JSON and Markdown evidence outputs
- [x] Unit/contract tests
- [x] Open-source license and dependency/IP boundary
- [x] Presentation outline
- [ ] Official registration and initial-round form submission
- [ ] Optional narrated demo video

Official registration remains blocked by the account form requiring real name, email, a new password and acceptance of competition/privacy agreements. Those identity and legal steps are intentionally not fabricated or accepted by the Agent.

## Demonstration script

1. Open `web/index.html` and keep the included nine-row synthetic dataset.
2. Run the default `|z-score| >= 2.0` policy.
3. Show the input fingerprint, `EV-001`, critical incident for `M-02`, and `+167.50%` latest-period change.
4. Open the JSON evidence and show the blocked `approve_and_execute` step.
5. Increase the threshold to `4.0` and show that no incident is proposed.
6. Explain that the Agent changes evidence and proposals, never a production system.

## Evidence of verification

Run:

```powershell
python -m unittest discover -s tests -v
python -m src.goai_agent.agent --csv examples/maintenance.csv
```

The package contains no private competition data or credentials. Example CSV files are synthetic and authored for this submission.
