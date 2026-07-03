# Codex CLI Limitation Report

Status update:

> Superseded. `codex-cli-verified-flags.md` records the independent npm Codex
> CLI (`codex-cli 0.139.0`) and the flags needed for the Codex-native driver.
> This report remains as the historical explanation for why the MSIX desktop
> `codex.exe` path is not a usable automation target.

## Goal

Build a Codex-native one-command Mentor Loop driver:

```text
mentor-loop <task description>
```

The apprentice step must run as a separate non-interactive Codex process on a
cheap model, with exact CLI flags verified against the locally installed Codex
version before implementation.

## Checked Locally

### WindowsApps Codex executable

`Get-Command codex` found:

```text
C:\Program Files\WindowsApps\OpenAI.Codex_26.608.1337.0_x64__2p2nqsd0c76g0\app\resources\codex.exe
```

But direct execution failed:

```text
codex --version
Program 'codex.exe' failed to run: Access is denied

codex --help
Program 'codex.exe' failed to run: Access is denied

codex exec --help
Program 'codex.exe' failed to run: Access is denied
```

Because of this, the installed Codex CLI flags could not be verified.

### npm / npx fallback

PowerShell shims were blocked by execution policy:

```text
npm.ps1 cannot be loaded because running scripts is disabled on this system
npx.ps1 cannot be loaded because running scripts is disabled on this system
```

Calling `npm.cmd` / `npx.cmd` directly did not produce a usable Codex CLI:

```text
npm list -g --depth=0
ENOENT: no such file or directory, lstat 'C:\Users\<user>\AppData\Roaming\npm'

npx --yes @openai/codex --help
request to https://registry.npmjs.org/@openai%2fcodex failed
EACCES
```

## Decision

Stop before building the Codex-native driver.

The goal explicitly says:

> verify the exact CLI flags (exec mode, model override, working dir) against
> the locally installed codex version first -- do not guess flags.

It also says:

> If the installed codex version cannot run a second non-interactive instance
> with a different model, STOP and report the exact limitation instead of
> building a workaround framework.

Current limitation:

> The local environment exposes a Codex desktop `codex.exe`, but direct CLI
> execution is denied, so `codex exec`, model override, and working-directory
> flags cannot be verified from this shell.

## Not Built

- No Codex driver script.
- No config file with guessed command templates.
- No model router.
- No provider registry.
- No generic adapter layer.
- No Claude Code port.

## Unblocked Next Step

Run these in a shell where Codex CLI is executable:

```text
codex --version
codex --help
codex exec --help
```

The required facts to capture are:

- non-interactive execution command,
- prompt input method,
- model override flag,
- working-directory flag,
- whether edits are allowed in the target repo,
- whether exit codes and logs are reliable enough for the driver.

Only after those are verified should `mentor-loop <task>` be implemented.
