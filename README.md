# Token Smart Suite

**省掉无效消耗，不省掉该做的工作。**

把三个各自解决一部分问题的省 Token 技能，合成**一个**技能：按「时间」分成三层，同一时刻只用得到一层。

| 层 | 解决的问题 | 进入条件 | 参考文件 |
| --- | --- | --- | --- |
| ① **活跃期** | 无关读取、重复检查、过度编排、过程播报 | 默认层，任何任务 | `references/live-discipline.md` |
| ② **存留期** | 旧历史越堆越大，任务越来越慢 | 任务变慢／加载失败／要回看旧原话 | `references/history-coldstore.md`（动存储时再读 `legacy-adapter.md`） |
| ③ **演进期** | 同样的活反复摸索，经验留不下来 | 要夜间／离线自优化、复盘过去会话 | `references/sleep-cycle.md` |

三层合起来是一条完整链路：**当下怎么少花 → 旧的怎么存 → 长期怎么收敛**。

## 为什么合并，而不是三个技能

单个技能各自的说明都不大，但**三个技能同时被扫描、被加载**时，路由成本和上下文占用会叠加。合并后：

- `SKILL.md` 只有一份，**约 3 KB**，是纯路由表 + 常驻铁律，不含细节；
- 三层细节全部拆进 `references/`，**只有触发到那一层才读那一份**，且一次只读一份；
- 合并后新增的共享原则（诚实边界、按需加载本身）不重复计费。

也就是说——**合并反而比三个分开更省**，这也是本技能自己的方法论。

```
skills/token-smart/
├── SKILL.md                     ← 唯一入口：路由 + 铁律（~3 KB）
├── agents/openai.yaml
├── references/
│   ├── live-discipline.md       层① 八条纪律展开
│   ├── history-coldstore.md     层② 整理流程 + 按需检索
│   ├── legacy-adapter.md        层② 存储适配合同（只在真要动存储时读）
│   ├── sleep-cycle.md           层③ 离线收敛周期与命令
│   ├── onboarding.md / .en.md   安装说明
└── scripts/
    ├── cold_history.py          层② 冷档案索引/检索/导出（标准库，不改活跃任务）
    └── test_cold_history.py     自检
```

## 安装

需要 Git 和 Python 3。

**让 AI 代装**，把这句话发给你的编码助手（把目标换成实际工具）：

> 请从 `https://github.com/Zeno-Zhu/token-smart-suite` 克隆并阅读安装说明，为我的 Codex 安装 Token Smart，使用默认按需模式，不添加常驻规则；安装后把三层原理和使用体感简要告诉我。

**手动安装**：

```sh
git clone https://github.com/Zeno-Zhu/token-smart-suite.git
cd token-smart-suite
python install.py --target codex      # 或 --target claude
```

默认目录 `~/.agents/skills/token-smart`（Codex）与 `~/.claude/skills/token-smart`（Claude Code）。首次安装会打印简短说明；普通任务不再重复。

### 装到别的宿主

安装器默认只认 Codex 和 Claude Code 两套目录。要让 **WorkBuddy** 也能发现这个技能，用 `--skills-dir` 指到它的用户级技能目录：

```sh
python install.py --target codex --skills-dir ~/.workbuddy/skills
```

两者互不干扰，都是**用户级、跨项目**生效，不是项目级。

**Windows / Git Bash 注意**：`--skills-dir` 现在同时接受原生路径（`C:/Users/me/skills`）和 Git Bash 风格（`/c/Users/me/skills`），后者会被自动映射到对应盘符。早期版本会把 `/c/...` 当成相对路径、装进 `C:\c\...`，这一版已修。

### 从旧版升级

如果你装过独立的 `token-smart`，先卸载再装新版（安装器遇到文件不一致会拒绝覆盖，这是有意的）：

```sh
# 在旧的 token-smart-skill 仓库目录里
python install.py --target codex --uninstall
# 再在本仓库目录里
python install.py --target codex
```

### 按需还是常驻

| 模式 | 怎么用 | 会改变什么 |
| --- | --- | --- |
| 按需（默认） | Codex 输入 `$token-smart`；Claude Code 输入 `/token-smart`，或说"这次按 Token Smart 来" | 只安装技能，不加持久指令 |
| 常驻（可选） | 安装命令加 `--activate` | 往对应指令文件追加一段短规则，供后续会话读取 |

```sh
python install.py --target codex --activate
```

Codex 常驻规则写入 `$CODEX_HOME/AGENTS.md`（已有 `AGENTS.override.md` 则写后者；未设 `CODEX_HOME` 时用 `~/.codex`）。Claude Code 用 `~/.claude/CLAUDE.md`。原有内容保留，只追加独立规则块。

安装只是让宿主**能够发现**技能，不保证每轮执行。当前会话没发现它，请新开会话。

**卸载**：在原目标上运行 `--uninstall`（用过自定义 `--skills-dir` 就带上同一路径，不要同时加 `--activate`）。已修改的文件与规则块会保留。

```sh
python install.py --target codex --uninstall                              # Codex 全局
python install.py --target codex --skills-dir ~/.workbuddy/skills --uninstall   # WorkBuddy 全局
```

装了几处就要分别卸几处；卸载是**凭据式**的，只删字节与安装记录一致的文件，你手改过的内容会被保留并打印出来。

自定义位置与语言：`--skills-dir` 指定技能父目录，`--instructions` 指定常驻规则文件，`--lang en` 用英文安装说明。

## 各层怎么触发

**层① 活跃期**——不用做任何事，默认生效。想加厚说明说"这次详细展开"，想临时关掉说"这次不要按省 Token 模式"。

**层② 存留期**——任务变慢或要求瘦身时：

> 使用 $token-smart，检查这个任务的历史加载负担，保留原任务，把旧原文转为按需检索的冷档案。

只查已有档案时：

> 使用 $token-smart，从这个任务的冷档案查找之前关于"具体关键词"的原话。

冷档案查询器（Python 3.9+，仅标准库，不修改活跃任务）：

```sh
python -X utf8 scripts/cold_history.py --archive "ARCHIVE_DIR" index
python -X utf8 scripts/cold_history.py --archive "ARCHIVE_DIR" search "关键词" --limit 8
python -X utf8 scripts/cold_history.py --archive "ARCHIVE_DIR" show 24 --chars 8000
python -X utf8 scripts/cold_history.py --archive "ARCHIVE_DIR" export 24 "NEW_EXPORT_FILE"
```

档案原件命名为 `original.jsonl`；`index` 只对没有索引的新冻结档案运行，已有索引不会被覆盖。

**层③ 演进期**——需要 `microsoft/SkillOpt` 的引擎本体（本技能只带入口与操作约定）：

```sh
export SKILLOPT_SLEEP_REPO=/path/to/SkillOpt
bash "$SKILLOPT_SLEEP_REPO/plugins/run-sleep.sh" dry-run --project "$(pwd)" \
  --source codex --target-skill-path .agents/skills/example/SKILL.md --backend mock
```

默认后端 `mock`，确定性且**不花 API 预算**；`run` 默认只暂存提案，采纳是独立的安全边界。细节与所有参数见 `references/sleep-cycle.md`。

## 验证

```sh
python -m unittest discover -s tests                       # 安装器回归（8 项）
python -X utf8 skills/token-smart/scripts/test_cold_history.py   # 冷档案查询器自检
```

两项都只用临时目录里的合成数据，不读取真实任务。

## 局限（重要）

- 这是**工作方式与存储约定**，不是上下文压缩器、额度解锁或平台配置工具。
- **不承诺任何固定的节省比例**；效果取决于任务、模型、上下文和宿主的指令执行。
- 必需的专业流程、完整交付和必要测试仍须执行。减少文字不等于减少工作，也不能把省 Token 当作提前收工的理由。
- 层②涉及改写任务历史：**无法证明保真时只交付只读结果并明确说明未完成**。存储适配参考验证版本为 Codex 0.153.0 legacy JSONL，其他版本须现场验证恢复语义。
- 层③的引擎不是本仓库的一部分；留出集上的提升是该次运行的证据，不保证更广泛的改善。

## 来源与许可

本仓库是三个 MIT 项目的合并与改写：

- `q2522879285-source/token-smart-skill` —— 层①
- `q2522879285-source/codex-thread-cold-history` —— 层②（含 `cold_history.py` 与适配器合同）
- `microsoft/SkillOpt`（`skillopt-sleep`）—— 层③

采用 [MIT License](LICENSE)，沿用上游版权声明。
