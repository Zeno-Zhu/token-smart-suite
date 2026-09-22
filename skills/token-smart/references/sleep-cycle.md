# 层③ 演进期：SkillOpt-Sleep 离线收敛

给本地编码 agent 一个「睡眠周期」：按需或夜间定时，复盘过去的本地会话，把重复任务在当前技能与记忆下重跑一遍，只在**留出验证分数提升**时才提出有界修改。没有模型权重训练。

上游：`microsoft/SkillOpt`（MIT）的 `skillopt-sleep` 技能与 `skillopt_sleep` 引擎。本层只是入口与操作约定，引擎本体需另行取得该仓库。

**Codex 注意**：共享引擎**不写** `AGENTS.md`。要给 Codex 可见结果，必须显式指定 `--target-skill-path`（如 `.agents/skills/<name>/SKILL.md`）。若不希望项目 `CLAUDE.md` 作为次目标，先在 `~/.skillopt-sleep/config.json` 里设 `"evolve_memory": false`。

## 何时进入

- 用户想让 agent 从过去会话中学习、越用越好；
- 要夜间/定时或按需的 sleep / dream / 离线自优化运行；
- 要复盘过去会话、提炼重复任务；
- 要把反馈收敛进记忆或受管技能；
- 要跑 `status`、`harvest`、`dry-run`、`run`、`adopt`。

## 周期

1. **Harvest** — 按引擎配置读取本地会话转录，归一为会话摘要。
2. **Mine** — 把摘要变成带结果与可核对引用的重复 `TaskRecord`。
3. **Replay** — 在当前技能与记忆下，用选定后端重跑挖出的任务。
4. **Consolidate** — 反思失败，提出有界编辑（增/删/改）。
5. **Gate** — 默认开启：只有留出验证分提升才接受编辑。
6. **Stage** — 提案写到 `<project>/.skillopt-sleep/staging/<date>/`，**不动线上文件**。
7. **Adopt** — 显式或用户明确要求 `--auto-adopt` 时，才把暂存文件覆盖到线上并先备份原文件。

## 怎么驱动

用 shell 调内置 runner（Codex 有 shell 权限）。runner 会自动定位引擎与 Python ≥ 3.10。

```bash
export SKILLOPT_SLEEP_REPO=/path/to/SkillOpt
TARGET_SKILL=.agents/skills/example/SKILL.md
bash "$SKILLOPT_SLEEP_REPO/plugins/run-sleep.sh" status   --project "$(pwd)"
bash "$SKILLOPT_SLEEP_REPO/plugins/run-sleep.sh" harvest  --project "$(pwd)" --source codex --target-skill-path "$TARGET_SKILL"
bash "$SKILLOPT_SLEEP_REPO/plugins/run-sleep.sh" dry-run  --project "$(pwd)" --source codex --target-skill-path "$TARGET_SKILL" --backend mock
bash "$SKILLOPT_SLEEP_REPO/plugins/run-sleep.sh" run      --project "$(pwd)" --source codex --target-skill-path "$TARGET_SKILL" --backend codex --max-sessions 5 --max-tasks 3 --progress
bash "$SKILLOPT_SLEEP_REPO/plugins/run-sleep.sh" adopt    --project "$(pwd)" --legacy
```

Windows 用 `plugins\run-sleep.cmd`（CMD）或 `plugins\run-sleep.ps1`（PowerShell），同样先设 `SKILLOPT_SLEEP_REPO`。

动作：`status`、`harvest`、`dry-run`、`run`、`adopt`、`schedule`、`unschedule`。批量采纳时用可重复的 `--skill NAME` 或 `--all-skills` 选定已复核的提案，**裸 adopt 不等于"全部采纳"**。

- 默认后端 `mock`：确定性、**不花 API 预算**。
- `--backend codex` 会消耗用户 Codex 预算；留出集上的提升是该次运行的证据，不保证更广泛改善。
- `--source codex` 读 `~/.codex/archived_sessions`；档案在别处时用 `--codex-home`。
- 除非用户明确要求真实优化运行，否则**先跑 `dry-run --backend mock` 冒烟**。

其他后端：`mock` / `claude` / `codex` / `copilot` / `handoff`（产出可交互的 prompt/answer 文件）/ `azure_openai`。

常用参数：`--auto-adopt`（门通过则自动采纳，默认只暂存）、`--edit-budget N`（每晚有界编辑数，默认 4）、`--lookback-hours N`（召回窗口，默认 72）、`--json`。

定时：`schedule --project "$(pwd)" --backend codex --hour 3 --minute 17`；`unschedule --project "$(pwd)"`；`unschedule --all` 清空全部托管项。调度器只持久化 project、backend、时间、auto-adopt 开关；**不**持久化本次命令的 `--source` 与 `--target-skill-path`，所以调度前要先把 `"transcript_source": "codex"` 和绝对 `"target_skill_path"` 写进 `~/.skillopt-sleep/config.json`。没有 `crontab` 的系统会打印一行供手动安装。

配置键（`~/.skillopt-sleep/config.json`）：`preferences`（自由文本偏好）、`gate_mode`（`on` 默认 / `off` 贪心）、`gate_metric`（`hard` / `soft` / `mixed` 默认）、`gate_no_regression`（默认 `false`；设 `true` 则任一验证任务掉分即拒绝候选）、`dream_rollouts`（>1 开启多轮对比反思）、`recall_k`（>0 从档案召回相似历史任务）、`evolve_memory` / `evolve_skill`（两个目标独立开关，同一门控）。

## 操作纪律

- **Harvest 只读**：不编辑归档会话或原始转录。
- 转录采集会清理已知的密钥形状字符串、开发者指令与原始工具载荷，但**模式化脱敏不是保证**；真实后端仍会把截断后的转录/任务内容发给其提供方。敏感会话与提供方政策要先过一遍；数据边界重要时优先用已复核的 `--tasks-file` 流程。
- 原始密钥、凭据、私密用户数据和转录内容不得进入消息、日志、生成物或提交。
- **先展示验证证据，再建议采纳**。
- 生成的编辑是**提案**，不是事实来源。
- 不要手改受管的 `CLAUDE.md` 或目标技能来代替引擎的 adopt 路径——采纳是安全边界，且会先备份现有目标。
- 仓库里记录的 `brief-writer` gbrain 运行是 0.00 → 1.00，但那是**该配置下可复现的基准证据**，不是对其他技能、任务或模型的保证。
