# mentor-loop-engine

[English](README.md) · **中文**

给便宜的编码 agent 拴一根短绳。它执行强模型下的工作单，**在一个确定性的范围门里干活**（计划没列
出的文件，改动会被挡下），评审只读 diff；而且每次运行都落盘，你能精确审计到底发生了什么。

`mentor-loop-engine` 是一个小命令行，运行一套**三层代码改动回路**：

- **mentor**（强）写工作单——*Mentor Brief*——并评审 diff；
- **apprentice**（便宜）严格在工作单圈定的改动范围内执行；
- **gates**（确定性代码，不含模型判断）拿改动去对范围核查；
- **architect**（强）在改动触及某个架构决策时被咨询、其裁决被记录在案——让决策不会悄悄漂移。

引擎是**模型无关**的：它驱动一个命令行（随包配好了 `codex`），所以*强*、*便宜*、*架构师*具体是哪个
模型，由你自己指定。

## 为什么你会想装它

- **范围控制。** 一个确定性的改动范围门会挡下对任何"工作单没列出的文件"的改动——越界的改动在落地
  前就被拦住。（它约束的是*哪些文件*被改，不保证文件里的逻辑对不对——见下方"诚实的现状"。）
- **只读 diff 的评审。** 一次强模型评审只看 diff、工作单和证据，然后给出 通过 / 要改 / 停下重规划。
- **一份本地审计记录。** 工作单、学徒日志、门的输出、diff、评审、最终报告——每次运行都落在
  `.mentor-loop/runs/<id>/` 下，任何一次改动事后都能复盘。
- **护栏会上报，而不是瞎猜。** 工作单必须声明每个护栏的失败方向；一个留成 *fail-open* 的护栏，会在
  便宜模型执行**之前**被上报给架构师，裁决被记录、并在下次运行时强制执行。
- **可选的跨厂顾问。** 让一个跨厂模型在写任何代码之前先读工作单、指出师傅漏掉的地方。仅作顾问、
  默认关闭。
- **有测试覆盖。** 那两个门和各阶段都有单元测试实际触发，还有一个打包自检跑绿——是真执行，不是
  "看一眼觉得 OK"：`python -m unittest discover -s tests` 和 `python tools/verify-package.py` 都通过。

## 两种载体，同一套方法

这是**引擎**载体。它的姊妹——
[**mentor-loop skill**](https://github.com/ivalainexii/mentor-loop)——把同一套方法打包成一个
Claude Code 原生技能（`/mentor-loop <task>` + 一个子代理）。

|          | skill（`mentor-loop`）           | engine（`mentor-loop-engine`）        |
| -------- | -------------------------------- | ------------------------------------- |
| 载体     | Claude Code 技能 + 子代理        | 调用 `codex` 的 Python 命令行驱动     |
| 入口     | 会话里 `/mentor-loop <task>`     | `python tools/mentor-loop.py …`       |

它们是**姊妹，不是版本**——技能没有被这个引擎取代。**该用哪个？** 在 Claude Code 会话里干活 →
用技能；想要可脚本化的命令行、或驱动非 Claude 模型 → 用这个引擎。

## 快速上手

要求：Python 3.10+、一个工作区干净的目标 **git** 仓库、以及 `PATH` 上有 `codex` 命令行（随包的
`mentor-loop.config.json` 会调用 `codex exec`；换成你自己的模型请改它）。可复制的模板见
`mentor-loop.config.json.example`。

分阶段流程——师傅会话写 `mentor-brief.md` 和 `review.md`，引擎跑确定性阶段和便宜学徒的外部调用：

```powershell
python path\to\mentor-loop-engine\tools\mentor-loop.py init        --repo path\to\target-repo "fix <bug>"
python path\to\mentor-loop-engine\tools\mentor-loop.py brief-check  --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-engine\tools\mentor-loop.py apprentice   --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-engine\tools\mentor-loop.py gates        --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-engine\tools\mentor-loop.py snapshot     --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-engine\tools\mentor-loop.py capture-lesson --repo path\to\target-repo --run <run-id>
python path\to\mentor-loop-engine\tools\mentor-loop.py report       --repo path\to\target-repo --run <run-id>
```

当一份工作单上报了 fail-open 护栏时，架构师回路阶段会拼装咨询包、并把裁决写回台账：

```powershell
python path\to\mentor-loop-engine\tools\mentor-loop.py architect-packet --repo path\to\target-repo --run <run-id>
# 把咨询包交给一个强架构师，把它的裁决存成 .mentor-loop/runs/<run-id>/ 下的一个文件，然后：
python path\to\mentor-loop-engine\tools\mentor-loop.py architect-ratify --repo path\to\target-repo --run <run-id> --verdict <file> --ref <ref>
```

还有一条一次性 `run` 路径和一个 `--dry-run` 开关。完整手动流程见 `operator-runbook.md` 和 `quickstart.md`。

## 回路是怎么接的

```
architect（强，在决策点被咨询）  ── 对架构拍板；裁决记入台账
     │
mentor（强，每个任务）  ── 写 Mentor Brief（工作单）、评审 diff
     │
apprentice（便宜，每次运行）  ── 严格在工作单圈定的改动范围内执行
     │
gates（确定性代码）  ── 改动范围 + 运行时下限检查；不含模型判断
```

除基础回路外，引擎还带三个护栏/上报机制：**工作单诚实门**（每个护栏都必须声明失败方向 + 理由）、
**架构师上报**（fail-open/unsure 护栏在学徒执行前被上报给架构师，师傅不得自批）、以及**架构师回路
闭合**（引擎拼装咨询包、把过往决策注入后续工作单、把裁决写回台账——没有裁决就不解锁）。

## 诚实的现状：一个能用的工具，和一个开放的研究论断

上面这些都是**能跑、有测试、你今天就能用的机制**。尚未有定论的，是这个项目最初出发的那个研究
问题——而本仓库刻意把"哪个是哪个"讲清楚（如实评测自己的工具，本身就是重点之一，也是它想展示的东西）。

> **开放的问题：** 这样打包判断，是否真的让便宜模型表现得*更接近*强模型——以及架构师层的收益，
> 是否会随着它的决策台账增长而**复利**？

**已确立（就在本仓库，跑一遍就能验证）：** 回路端到端能跑、产出完整产物集；那两个门是有测试
触发的真确定性代码；护栏/上报/架构师回路的往返按声明行为；83 个测试通过、打包自检为绿。

**仍然开放（明说，免得被悄悄跳过）：**

- **"复利"论断**是一个*预登记、开放中的测量*，不是结论（见下）；它还没有干净地下降。
- 近期的零纠错数据点**偏弱**——学徒那一片几乎是被作者自己已验证的运行完全指定好的，不是独立执行。
- 所有数据点都是**作者自己跑的**：没有基线对照（便宜模型单干 vs. 全回路），也没有对这个引擎的
  独立第三方运行。
- **还没有成本测量**——请把它当作纪律工具和案例研究，不是成本套利。

### 一条提前写死的判读

这是一个**很小的、单一作者的样本（n ≈ 7）**——远不足以下任何结论，我也不会把它包装得像结论。但这条
判读是在结果出来*之前*写下的，所以事后没法悄悄改：

> 如果到 **~n = 8** 纠错率**仍未明显下降**，"复利"论断就记为一次**诚实的负结果**——卖点收窄为：判断
> 可以*配给*给一个架构师，但没能证明随台账增长而*复利*。

原始序列保存在目标仓库的 `.mentor-loop/decisions.md` 里。

## 当前限制

- **这个引擎没有经过任何第三方冷启动。** 姊妹*技能*有过一次交互式冷启动；这个引擎没有。照着这些
  文档在一台干净机器上安装/运行，是一条未经测试的路径——欢迎反馈。
- **以 Windows 为主。** 在 Windows 上开发和测试；`codex` 沙箱有真实的平台限制
  （见 `reports/codex-cli-limitation-report.md`）。
- **研究记录是原始的。** `experiments/`、`evals/`、`reports/` 是带日期的内部笔记和证据，某些地方
  已被后来的结论取代。算数的论断以*本 README* 为准；凡旧笔记读起来像更强的论断，一律以本 README 为准。

## 仓库结构

- `tools/mentor-loop.py` —— 阶段引擎（回路 + 门 + 架构师回路闭合）。
- `tools/verify-package.py` —— 发布自检（清单、门、测试、可选 zip）。
- `gates/` —— 两个确定性门（改动范围、运行时下限）。
- `tests/` —— 单元测试（`unittest discover -s tests`）。
- `*-template.md`、`subagents/`、`skills/`、`.claude/` —— 回路的提示词产物与 Claude Code 接线。
- `evals/`、`experiments/`、`reports/` —— （原始的）研究记录与证据。

## 许可证

MIT —— 见 `LICENSE`。
