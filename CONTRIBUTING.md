# Contributing

Thanks for helping out! 🎉 This is a community project **by and for University of Waterloo students**. You're welcome here whatever your program, faculty, or coding experience — many of the most useful contributions come from non-CS students who just noticed something was wrong.

## You don't need to be a programmer

If a step below sounds technical, you can paste it to your AI assistant (Claude Code or Codex) and ask it to do it for you. That's the whole spirit of this project.

## The most valuable contribution: tell us what broke

WaterlooWorks changes its interface often, which quietly breaks automation. If a skill stops working, **that report is gold.** Please [open an issue](https://github.com/jerryzhang1011/waterlooworks-application-plugins/issues/new) and include:

- What you asked your assistant to do (e.g. "apply to job 475135").
- What you expected vs. what actually happened.
- Any error message, and roughly where it got stuck (login page? document upload? submit button?).
- Which assistant you used (Claude Code or Codex) and your operating system.

⚠️ **Please don't paste personal information** — no real résumé contents, home address, phone number, or WaterlooWorks password in issues or PRs.

## Suggesting a change or fix (pull request)

1. **Fork** this repo (top-right "Fork" button on GitHub).
2. Make your change. Most live in `plugins/waterlooworks-jobs/skills/<skill-name>/SKILL.md`.
3. **Open a pull request** describing what you changed and why.

A maintainer will review it. Small, focused PRs are easiest to merge.

## House rules for keeping it safe to publish

This repo must never contain anyone's real personal data. When you contribute:

- Use the placeholder student **"Jordan Goose"** and the values in `examples/` for any example — never real names, addresses, phone numbers, emails, or résumé content.
- Personal files (`coverletter-config.json`, your résumé PDFs, scraped jobs) are already in `.gitignore`. Keep it that way; don't commit them.

## Code of conduct

Be kind and constructive. We're all students trying to land jobs — assume good faith and help each other out.
