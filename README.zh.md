# mentor-loop-engine

[English](README.md) · **中文**

> **项目状态（2026-07-10）：保留的研究原型；已不再作为默认系统架构。** CLI、测试、
> 实验和报告继续作为证据与可复用组件保留。本仓库没有活跃产品路线；后续只修有真实证据的
> 缺陷，或按明确选择复用组件。回滚基线为 annotated tag
> `mentor-loop-v2-preserved-20260710`。

| 论断 / 承诺 | 关账状态 | 证据边界内的结论 |
| --- | --- | --- |
| 确定性引擎、证据链以及 fail-closed 的 package/runtime 检查 | **completed** | 保留基线上 206 个单元测试与 package verifier 通过 |
| 可审计性和对已观察故障的定点预防 | **partially answered** | 作者实跑抓到真故障并形成闸；没有第三方 engine 冷启动 |
| A′ 预登记指标能测出预期的复利效应 | **falsified** | 指标结构上产不出目标信号；见 postmortem |
| 对便宜模型结果提升、成本优势或判断复利的进一步产品级验证 | **not pursued** | 过去的作者实跑不足以形成可信 baseline / 成本结论；本仓不作产品论断 |

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

在保留的 v2 产品线内，它们是**姊妹，不是版本**——两者没有互相取代；但整条产品线已不再是默认架构。
历史或明确复用时：在 Claude Code 会话里干活 → 用技能；需要可脚本化命令行或非 Claude 驱动 →
用这个引擎。

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

## 诚实的现状：一个能用的工具，和一个已经关账的研究计划

上面这些都是**能跑、有测试、你今天就能用的机制**。产生这些机制的研究计划现已关账，不再把未完成
验证暗示成产品义务。它当时的问题是：这样打包判断，是否会让便宜模型表现得*更接近*强模型，以及
架构师层的收益是否会随着决策台账增长而**复利**。

**已确立（就在本仓库，跑一遍就能验证）：** 回路端到端能跑、产出完整产物集；那两个门是有测试
触发的真确定性代码；护栏/上报/架构师回路的往返按声明行为；206 个测试通过、打包自检为绿。

**最终研究处置：**

- 预登记的 A′ **测量设计已被证伪**：harness 在结构上无法产出目标指标。因此该 pilot 的结果是
  **uninformative**，对底层“复利”论断的正反方向都提供零证据。
- 便宜模型结果提升、成本优势和判断复利这些底层论断仍是**未证实，而非已证伪**。过去的数据点由作者
  自己运行、样本很小，且学徒切片大多来自作者已验证的执行；没有可信的“便宜模型单干”基线、成本测量，
  也没有独立第三方对引擎的运行。
- 后续产品级验证**不再推进**。这里没有剩余的 `n ≈ 8` 义务，也没有活跃路线图。请把它视为纪律工具和
  案例研究，而不是成本套利。若要恢复研究，必须另作明确决策并建立新的测量契约。

历史原始序列保存在目标仓库的 `.mentor-loop/decisions.md`。完整的 A′ postmortem（包括两次独立裁决如何
发现无效指标）见 [docs/aprime-postmortem.md](docs/aprime-postmortem.md)。

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
