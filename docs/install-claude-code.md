# Install on Claude Code

A step-by-step guide for **Claude Code** users. Written for students who are **not** programmers — just follow along in order.

> 🟣 Using **Codex** instead? See [Install on Codex](install-codex.md).

---

## Before you start

You need two things:

1. **Claude Code** installed and open. If you don't have it yet, get it at [claude.com/claude-code](https://claude.com/claude-code).
2. **Google Chrome**, signed in to your WaterlooWorks account, with Claude Code able to control your browser. (Don't worry if browser control isn't set up yet — the `ww-setup` skill in Step 4 checks this and walks you through it.)

You do **not** need to download or clone anything by hand. The command below pulls everything from GitHub for you.

---

## Step 1 — Add the plugin marketplace

In Claude Code, type:

```text
/plugin marketplace add jerryzhang1011/waterlooworks-application-plugins
```

This tells Claude Code where to find the plugin. (A "marketplace" is just a list of plugins.)

## Step 2 — Install the plugin

```text
/plugin install waterlooworks-jobs@uwaterloo-jobs
```

Here `waterlooworks-jobs` is the plugin and `uwaterloo-jobs` is the marketplace it comes from.

> 💡 Prefer clicking to typing? Run `/plugin`, open the **Discover** tab, find **WaterlooWorks Jobs**, and install it there.

## Step 3 — Turn the skills on

```text
/reload-plugins
```

(Or just quit and reopen Claude Code.) The plugin's six skills are now available: `ww-setup`, `ww-login`, `ww-scrape-jobs`, `ww-write-cover-letter`, `ww-upload-cover-letter`, and `ww-apply-to-job`.

## Step 4 — Finish setup

Open Claude Code in the folder where you want to keep your job-search files (your résumé, cover letters, and saved postings will live here). Then paste this:

```text
I'm a University of Waterloo student and I'm not a programmer. I just installed
the waterlooworks-jobs plugin. Please finish setting me up and explain each
step simply:

1. Run the ww-setup skill to check my computer and install any tools the skills
   need (ask me before anything big).

2. Help me put my résumé PDF in a resume/ folder and create my
   coverletter-config.json, using the example files in this repo as a template
   (resume/example-resume.pdf and coverletter-config.example.json). Use MY real
   details — and remind me they stay on my computer and are never uploaded.

3. Tell me how to scrape jobs, write a cover letter, and apply to a job.
```

## Step 5 — Use it

Just ask in plain English:

- *"Scrape WaterlooWorks jobs for my program."*
- *"Write a cover letter for job 475135 using my résumé."*
- *"Apply to WaterlooWorks job 475135 with my résumé."*

The skills also kick in automatically when they're relevant — e.g. if your WaterlooWorks session has logged out, `ww-login` restores it for you.

---

## Keeping it updated

WaterlooWorks changes often, so update the plugin now and then:

```text
/plugin marketplace update uwaterloo-jobs
/plugin install waterlooworks-jobs@uwaterloo-jobs
```

## Removing it

```text
/plugin uninstall waterlooworks-jobs@uwaterloo-jobs
```

---

## Troubleshooting

- **"The skills don't show up."** Run `/reload-plugins`, or quit and reopen Claude Code. Confirm the install with `/plugin` → **Manage**.
- **"Marketplace not found" when adding it.** Double-check the spelling: `jerryzhang1011/waterlooworks-application-plugins`. You need internet access the first time.
- **"It says I'm logged out of WaterlooWorks."** Ask Claude to *"restore my WaterlooWorks login"* — the `ww-login` skill handles recoverable cases; it will pause and ask you only if a password, Duo/MFA, or CAPTCHA prompt appears.
- **A posting needs a document the plugin can't guess** (e.g. `Other - Per Job Posting`). The plugin stops and asks you — that's intentional.
- **Still stuck?** [Open an issue](https://github.com/jerryzhang1011/waterlooworks-application-plugins/issues/new) and describe what happened (no personal info, please).

---

🔒 **Your data stays with you.** Everything runs on your computer and drives your own browser. Your résumé, cover-letter details, and WaterlooWorks login are never uploaded by this project. Your real files (`resume/`, `coverletter/`, `coverletter-config.json`) are git-ignored so they're never committed if you push this folder anywhere.
