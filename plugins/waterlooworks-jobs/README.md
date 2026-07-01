# WaterlooWorks Jobs

A plugin that automates the WaterlooWorks application workflow for **any University of Waterloo student — any program, any work term.** It drives your own logged-in Chrome session to scrape postings, write tailored cover letters, upload documents, and submit Full-Cycle Service applications. This is the **Claude Code** build (`.claude-plugin/`); the matching **Codex** build lives in [`../waterlooworks-jobs-codex`](../waterlooworks-jobs-codex).

> This plugin automates *your* WaterlooWorks session on *your* machine. It never stores or transmits your credentials — when a real login, Duo/MFA, or CAPTCHA prompt appears, it stops and hands control back to you. All examples use a fictional student ("Jordan Goose").

## Skills

| Skill | What it does |
| --- | --- |
| `ww-setup` | Checks and installs everything the other skills need (runtimes, Python/npm packages, `poppler`, browser-control). Run this first on a new machine. |
| `ww-login` | Restores a dropped WaterlooWorks session automatically before viewing or applying. |
| `ww-scrape-jobs` | Saves job descriptions as individual Markdown files under `jds/`. Defaults to your "My Program" filter but accepts any WaterlooWorks search or filter. |
| `ww-write-cover-letter` | Generates a tailored one-page cover-letter PDF from a job description and one of your résumés. |
| `ww-upload-cover-letter` | Uploads a cover-letter PDF into a required `Cover Letter` document slot during submission. |
| `ww-apply-to-job` | Applies to a Full-Cycle Service job by ID end to end — handles logged-out states, required cover letters, and returns employer apply links when a posting requires applying directly. |

## Install

The easiest path is to let your AI assistant set everything up — see the [repo README](../../README.md) for a copy-paste prompt.

To install it yourself, send Claude Code this prompt:
```text
Add the marketplace jerryzhang1011/waterlooworks-application-plugins and install the waterlooworks-jobs plugin
```

**Codex** — add the plugin referenced by `.agents/plugins/marketplace.json` in the cloned repo.

Then reload so the skills register.

## First-time configuration

These live in *your* working directory (git-ignored), not in the plugin:

- `coverletter-config.json` — your name, address, and contact links for cover-letter headers. Copy [`coverletter-config.example.json`](../../coverletter-config.example.json) and edit. `ww-write-cover-letter` will also create it from your answers if it's missing.
- A résumé PDF in `resume/` (e.g. `resume/ai.pdf`) to tailor cover letters from — see [`resume/example-resume.pdf`](../../resume/example-resume.pdf). Generated cover letters land in `coverletter/` — see [`coverletter/example-coverletter.pdf`](../../coverletter/example-coverletter.pdf).

## Usage

```
Set up the WaterlooWorks tools on this machine.          # ww-setup
Scrape WaterlooWorks jobs for my program.                # ww-scrape-jobs
Write a cover letter for job 475135 using my résumé.     # ww-write-cover-letter
Apply to WaterlooWorks job 475135 with my résumé.        # ww-apply-to-job (chains login + cover letter)
```

## License

MIT — see [LICENSE](./LICENSE).
