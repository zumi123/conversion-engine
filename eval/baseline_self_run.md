# Act I Baseline — τ²-Bench Retail Domain

## What I Reproduced
Ran τ²-Bench retail domain with 5 trials across 30 tasks using
openrouter/qwen/qwen3-235b-a22b as both agent and user simulator.

## Results
| Metric | Value |
|--------|-------|
| pass@1 | 0.268 |
| pass@2 | 0.120 |
| pass@3 | 0.070 |
| pass@4 | 0.047 |
| Average Reward | 0.2721 |
| Total Simulations | 150 |
| Evaluated | 147 |
| Infra Errors | 3 |

## Confidence Interval (95%)
- pass@1: 0.268 ± 0.073
- Based on 147 evaluated simulations

## vs Published Reference
| | Score |
|---|---|
| Published reference (GPT-4 class) | ~0.42 |
| This baseline (Qwen3 free tier) | 0.268 |
| Delta | -0.152 |

## Cost Per Run
- Avg cost per conversation: $0.0000 (free tier model)
- Total cost for baseline run: $0.00

## Unexpected Behavior
- 3 infrastructure errors occurred (2% of simulations)
- All terminations were user-initiated (👤 147/147)
- Agent never self-terminated any conversation
- Authentication was not checked in any simulation

## Notes
- Model used is free tier — weaker than GPT-4 class reference
- Gap vs reference expected and will be addressed in Act IV
- Will use Claude Sonnet 4.6 for sealed held-out scoring in Act V