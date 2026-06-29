# Install on Codex

A step-by-step guide for **Codex** users. Written for students who are **not** programmers — just follow along in order.

> 🟢 Using **Claude Code** instead? See [Install on Claude Code](install-claude-code.md).

---

## Before you start

You need two things:

1. **Codex** installed — the CLI or the app. If you don't have it yet, see [developers.openai.com/codex](https://developers.openai.com/codex).
2. **Google Chrome**, signed in to your WaterlooWorks account. Codex drives the browser through its bundled **`@chrome`** plugin; the `ww-setup` skill in Step 3 checks this and helps you finish if needed.

You do **not** need to download or clone anything by hand — the command below pulls everything from GitHub for you.

---

## Step 1 — Add the plugin marketplace

In your terminal, run:

```bash
codex plugin marketplace add jerryzhang1011/waterlooworks-application-plugins
```

This registers the marketplace (a list of plugins) with Codex. GitHub shorthand (`owner/repo`) is supported, so that's all you need.

## Step 2 — Install the plugin

Open the plugin browser:

```text
/plugins
```

Plugins are grouped by marketplace. Find **WaterlooWorks Jobs** under the `uwaterloo-jobs` marketplace, open it, and choose **Install**. Make sure it's **enabled** (toggled on) after installing.

> 💡 Using the Codex **app** instead of the CLI? Open the **Plugins** section, find **WaterlooWorks Jobs**, and click **Add to Codex**.

Once installed and enabled, the plugin's six skills are available: `ww-setup`, `ww-login`, `ww-scrape-jobs`, `ww-write-cover-letter`, `ww-upload-cover-letter`, and `ww-apply-to-job`. (Codex stores each plugin's on/off state in `~/.codex/config.toml`.)

## Step 3 — Finish setup

Start Codex in the folder where you want to keep your job-search files (your résumé, cover letters, and saved postings will live here). Then paste this:

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

## Step 4 — Use it

Two ways to run a skill:

- **Just ask in plain English** — *"Scrape WaterlooWorks jobs for my program."*
- **Call it explicitly** — type `@` and pick the skill, e.g. `@ww-scrape-jobs`, `@ww-write-cover-letter`, `@ww-apply-to-job`.

Examples:

- *"Scrape WaterlooWorks jobs for my program."*
- *"Write a cover letter for job 475135 using my résumé."*
- *"Apply to WaterlooWorks job 475135 with my résumé."*

The skills also kick in automatically when relevant — e.g. `ww-login` restores a dropped WaterlooWorks session for you.

---

## Keeping it updated

WaterlooWorks changes often, so refresh the marketplace now and then and reinstall:

```bash
codex plugin marketplace update jerryzhang1011/waterlooworks-application-plugins
```
then reinstall from `/plugins` if prompted.

## Removing it

Open `/plugins`, select **WaterlooWorks Jobs**, and choose **Uninstall** (or disable it to keep it but turn it off).

---

## Troubleshooting

- **"The skills don't show up."** Make sure the plugin is **enabled** in `/plugins`. Restart Codex if needed.
- **"Marketplace add failed."** Check the spelling: `jerryzhang1011/waterlooworks-application-plugins`. You need internet access the first time. You can also pin a version with `--ref` if asked to.
- **"Browser control isn't working."** Confirm Codex's bundled **`@chrome`** plugin is enabled and Chrome is open and signed in to WaterlooWorks. `ww-setup` checks this.
- **"It says I'm logged out of WaterlooWorks."** Ask Codex to *"restore my WaterlooWorks login"* (`@ww-login`). It handles recoverable cases and pauses for you only if a password, Duo/MFA, or CAPTCHA prompt appears.
- **A posting needs a document the plugin can't guess** (e.g. `Other - Per Job Posting`). The plugin stops and asks you — that's intentional.
- **Still stuck?** [Open an issue](https://github.com/jerryzhang1011/waterlooworks-application-plugins/issues/new) and describe what happened (no personal info, please).

---

🔒 **Your data stays with you.** Everything runs on your computer and drives your own browser. Your résumé, cover-letter details, and WaterlooWorks login are never uploaded by this project. Your real files (`resume/`, `coverletter/`, `coverletter-config.json`) are git-ignored so they're never committed if you push this folder anywhere.
