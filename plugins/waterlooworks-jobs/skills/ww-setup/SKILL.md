---
name: ww-setup
description: Initialize this project by making sure every external tool the skills in `.claude/skills` need is actually installed. Use this whenever the user wants to set up, bootstrap, init, or onboard the project, or asks "are the tools/dependencies installed?", "will the skills run on this machine?", "set this repo up", or after cloning/pulling on a fresh machine. Scans the skills for their real dependencies (language runtimes, third-party Python/npm packages, command-line tools the skills shell out to like poppler, and MCP servers), checks each, auto-installs the safe ones, asks before heavy/system installs, and hands off anything that only the user can connect (like an MCP server).
---

# ww-setup

Make a freshly-cloned copy of this repo able to actually *run* its skills. The skills
call out to external tools — `python3` + `reportlab` to render cover letters, `node`
to write/validate scraped JDs, the Claude-in-Chrome MCP server to drive WaterlooWorks.
If any of those is missing, the skill fails partway through with a confusing error.
This skill finds the gaps up front and closes the ones it safely can.

## The core idea

A bundled script does the detection so you don't have to eyeball every file: it walks
the skills tree, infers each skill's real dependencies, checks what's installed, and
**classifies every missing one** by how it should be installed. Your job is to run that
script and then act on each class according to the policy below.

## Step 1 — Detect and classify

Run the checker from the repo root. Use `--json` so you can act on the result
programmatically; run it without `--json` first if you want to show the user a readable
table.

```bash
python3 .claude/skills/ww-setup/scripts/check_skill_deps.py --root .claude/skills --json
```

Each missing dependency comes back with a `class` field that tells you exactly how to
handle it:

| `class`  | What it is | What to do |
|----------|-----------|------------|
| `light`  | A user-level Python package (e.g. `reportlab`) | **Auto-install, no need to ask.** |
| `heavy`  | A language runtime or global npm package — needs Homebrew/sudo/system change | **Confirm with the user, then run.** |
| `user`   | An MCP server / external connection (e.g. Claude in Chrome) | **You can't install it from the CLI — hand it to the user with the setup hint.** |

The script exits `0` when all CLI-installable deps are satisfied (MCP/user deps don't
fail the check), `1` when something needs action. Installed items report `class: null`
and `installed: true` — skip those.

## Step 2 — Install the safe ones automatically (`light`)

For every `pip_packages` entry with `installed: false`, run its `install_cmd`. These are
ordinary user-space package installs with no system side effects, so the user already
opted into "just do it" — don't stop to ask. The script gives you the exact command,
which already maps import names to the correct pip name (e.g. `yaml` → `pyyaml`):

```bash
python3 -m pip install <install-name>
```

If `pip install` fails because the environment is externally managed (PEP 668, common on
Homebrew Python), retry with `python3 -m pip install --user <name>`, and if that also
fails, surface the error and the suggested command to the user rather than forcing it.

## Step 3 — Confirm before heavy/system installs (`heavy`)

A missing runtime (`python3`, `node`), a global npm package, or a system CLI tool (e.g.
poppler's `pdftotext`, usually `brew install poppler`) is a bigger commitment — it may
pull in Homebrew, need `sudo`, or change the system toolchain. Don't run these
silently. Show the user the exact `install_cmd` the script proposes and what it's for
(which skills need it), and run it only after they say yes. For example:

> `node` is missing — `ww-scrape-jobs` needs it. I'd run `brew install node`.
> Want me to go ahead?

If the user declines, leave it and note in your summary that those skills won't run until
it's installed.

## Step 4 — Verify the browser connector (`user`)

The checker reports the browser connector (`class: "user"`, `installed: null`) but can't
see whether it's actually live — a Chrome connector isn't visible from a shell. **You can
see it, though: check your own available tools.** If the Claude in Chrome browser-control
tools are present in this session — tool names beginning `mcp__Claude_in_Chrome__` (e.g.
`mcp__Claude_in_Chrome__navigate`) — then Claude in Chrome is connected.

- **Tools present** → connected. Report it as satisfied; don't tell the user to set it up.
- **Tools absent** → not connected. Tell the user which skills need it, pass along the
  `note` (setup hint) from the report, and offer to re-check. Don't claim the project is
  fully initialized while it's still unconnected — say it's "ready except for the browser
  connection," so the user isn't surprised later when a WaterlooWorks skill can't find the
  browser.

Your tool-availability check, not the checker's `installed: null`, is the source of truth
for this dependency.

## Step 5 — Create the working folders

The skills read and write three folders in the project root. `ww-scrape-jobs` and
`ww-write-cover-letter` create `jds/` and `coverletter/` lazily, but `resume/` is never
auto-created and the apply/cover-letter skills expect a résumé PDF to already be there.
Create all three up front so the user has somewhere to drop their résumé. This is
idempotent — `-p` leaves existing folders (and their contents) untouched:

```bash
mkdir -p resume coverletter jds
```

Then remind the user to put their résumé PDF in `resume/` (e.g. `resume/ai.pdf`) — the
skills tailor cover letters and pick the application document from there.

## Step 6 — Verify and report

Re-run the checker (Step 1) to confirm the `light`/`heavy` items now show as installed.
Then give the user a short, honest summary grouped by outcome — for example:

> Project initialized:
> - ✅ Installed: reportlab
> - ✅ Already present: python3 (3.13), node (v22)
> - ✅ Folders ready: resume/, coverletter/, jds/ (drop your résumé PDF in resume/)
> - ✅ Connected: Claude in Chrome (browser-control tools available)

(If the browser tools were absent instead, that last line becomes
`⏳ Needs you: Claude in Chrome — connect it, then I can re-check.`)

This skill is **idempotent** — safe to run any time. On an already-set-up machine it just
confirms everything's present and points out anything that drifted.

## Notes

- **Scope is `.claude/skills` by default**, matching how this repo is set up. If the user
  asks to also cover `.codex/skills` (it mirrors `.claude`), pass `--root .codex/skills`
  and merge the results — the dependency set is nearly identical.
- **The script only detects and reports; it never installs.** Keeping installation here in
  the skill is deliberate: the auto-light / confirm-heavy / hand-off-user policy lives in
  one place, and the user stays in control of anything with system-level consequences.
- **New dependencies are picked up automatically.** Detection is driven by what the skills
  actually import/require and the MCP signals in their docs, so when a skill gains a new
  tool, this check will flag it without anyone updating a hardcoded list. The checker
  assumes a package's pip name matches its import name; if they differ (e.g. `yaml` →
  `pyyaml`), install with the correct pip name.
