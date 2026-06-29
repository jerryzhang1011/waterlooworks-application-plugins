# WaterlooWorks Application Plugins

**AI plugins that apply to WaterlooWorks jobs for you — built for every University of Waterloo student, in any program, in any work term.**

You don't need to know how to code. You point your AI coding assistant (Claude Code or Codex) at this repo, and it does the technical setup for you. Then you just say things like *"scrape jobs for my program"* or *"apply to job 475135 with my résumé,"* and the assistant drives your own WaterlooWorks session to do it.

> 🔒 **Your data stays with you.** These plugins run on *your* computer and drive *your* logged-in browser. Your résumé, cover-letter details, and WaterlooWorks login never get uploaded anywhere by this project. Every example in this repo uses a made-up student ("Jordan Goose") — none of it is real.

---

## 🚀 Get started (no coding required)

You need one of these AI assistants installed first:
- **[Claude Code](https://claude.com/claude-code)**, or
- **[Codex](https://developers.openai.com/codex)**

Open it in **any empty folder** on your computer, then **copy the prompt below and paste it in.** Your assistant will handle the rest.

```text
I'm a University of Waterloo student and I want to use you to help me apply to
jobs on WaterlooWorks. I'm not a programmer, so please do all the technical
steps for me and explain each step in plain language.

1. Clone https://github.com/jerryzhang1011/waterlooworks-application-plugins
   into this folder.

2. Install the "waterlooworks-jobs" plugin from the cloned repo for whichever
   assistant you are:
   - If you are Claude Code: add the plugin marketplace from the cloned repo
     folder, then install the waterlooworks-jobs plugin, and reload so the
     skills become available.
   - If you are Codex: add the plugin from .agents/plugins/marketplace.json in
     the cloned repo.

3. Run the ww-setup skill to check my computer and install any tools the
   skills need (it will ask before anything big).

4. Help me create my own coverletter-config.json and add my résumé PDF, using
   the example files in the repo's resume/ and coverletter/ folders as a
   template. Use MY real details
   — and remind me they stay on my computer and are never uploaded.

5. When everything is ready, tell me how to scrape jobs, write a cover letter,
   and apply to a job.
```

That's it. After setup, you can ask in plain English:

- *"Scrape WaterlooWorks jobs for my program."*
- *"Write a cover letter for job 475135 using my résumé."*
- *"Apply to WaterlooWorks job 475135 with my résumé."*

---

## 📦 What's in this repo

Two plugins — really the **same six skills packaged for two different AI assistants** — so it doesn't matter which one you use:

| Plugin | For | Manifest |
| --- | --- | --- |
| **Claude Code plugin** | Claude Code | [`plugins/waterlooworks-jobs/.claude-plugin/plugin.json`](plugins/waterlooworks-jobs/.claude-plugin/plugin.json) |
| **Codex plugin** | Codex | [`plugins/waterlooworks-jobs/.codex-plugin/plugin.json`](plugins/waterlooworks-jobs/.codex-plugin/plugin.json) |

### The six skills

| Skill | What it does |
| --- | --- |
| `ww-setup` | Checks your computer and installs the tools the other skills need. Run this first. |
| `ww-login` | Restores your WaterlooWorks session automatically when it drops, so you don't get stuck logged out. |
| `ww-scrape-jobs` | Saves job postings as tidy files you can read and compare. Defaults to your program's listings, but works with any WaterlooWorks search or filter. |
| `ww-write-cover-letter` | Writes a tailored one-page cover-letter PDF from a posting and your résumé. |
| `ww-upload-cover-letter` | Uploads a cover-letter PDF into the right slot during application. |
| `ww-apply-to-job` | Applies to a Full-Cycle Service job by its ID, end to end. |

---

## ✅ What you'll need

The `ww-setup` skill checks all of this for you and installs what it safely can:

- **Google Chrome**, signed in to WaterlooWorks, with a browser-control connection for your assistant.
- **Python 3** and **Node.js** (for the helper scripts), plus `poppler` (for PDFs).

---

## 🔧 Set up your own details

These live in *your* folder and are git-ignored, so they never get committed:

- **`coverletter-config.json`** — your name, address, and contact links for cover-letter headers. Copy [`coverletter-config.example.json`](coverletter-config.example.json) and replace the placeholders with your details. (Your assistant can do this for you in step 4 above.)
- **A résumé PDF** in `resume/` — see [`resume/example-resume.pdf`](resume/example-resume.pdf) for the kind of file to point the skills at.
- **Cover letters** are written to `coverletter/` — see [`coverletter/example-coverletter.pdf`](coverletter/example-coverletter.pdf) for an example of what the plugin produces.

---

## 🤝 Contributing — UW students welcome!

This is a community project **by and for University of Waterloo students**, and we'd love your help — whatever your program or experience level.

- 🐛 **Found a bug or something that broke?** [Open an issue.](https://github.com/jerryzhang1011/waterlooworks-application-plugins/issues/new)
- 💡 **Have an idea, or fixed something?** [Open a pull request.](https://github.com/jerryzhang1011/waterlooworks-application-plugins/pulls)
- 📣 WaterlooWorks changes its interface often — reporting what broke for you genuinely helps every other student.

You don't have to be a CS student to contribute. See [CONTRIBUTING.md](CONTRIBUTING.md) for friendly, step-by-step guidance (your AI assistant can help you do it).

---

## License

MIT — see [LICENSE](LICENSE). Use it, share it, improve it.
