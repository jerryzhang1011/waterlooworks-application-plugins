---
name: ww-scrape-jobs
description: Scrape WaterlooWorks co-op job descriptions into a folder under this repository's jds/ directory as individual Markdown files. Use when the user asks to collect, scrape, export, or save WaterlooWorks jobs/JDs and wants Markdown files matching the existing cycle1 format. Defaults to the WaterlooWorks "For my program" / "My Program" filter when the user does not specify a filter, but supports any user-requested WaterlooWorks filter or search. Defaults the output folder to today's date (e.g. jds/2026-6-26) unless the user names a specific folder or cycle.
---

# WaterlooWorks JD Scraper

Use this project-only skill to scrape WaterlooWorks Full-Cycle Service job postings into a folder under `jds/` (a date-named folder by default) as individual Markdown files named `<job id> - <job title>.md`.

## Workflow

1. Choose the output folder under `jds/`:
   - Default the folder name to today's date in `YYYY-M-D` format with no zero-padding (e.g. `jds/2026-6-26`), matching the existing sibling folders. Read today's date from the session/system context.
   - If the user names a specific folder or cycle (e.g. "cycle 3" -> `jds/cycle3`, or "save to jds/2026-7-01"), use exactly that and do not reinterpret it.
   - Create the folder if it does not exist; this `<folder>` is used in every path below.
2. Inspect existing output format before writing:
   - Read one or two files from `jds/cycle1/`.
   - Preserve the same summary table and `##` section style.
3. Use Chrome for WaterlooWorks because it depends on the user's logged-in session.
   - Load the Chrome control skill if available.
   - Open `https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm`.
   - Choose the WaterlooWorks filter before scraping:
     - If the user did not specify a filter, tell them the default is `For my program` / `My Program` and apply the `My Program` quick filter.
     - If the user requested a different filter, keyword search, or filter combination, apply that instead and do not also force `My Program` unless they asked for it.
     - When reporting progress, name the filter or search criteria being used so the user knows they can request another filter in a future scrape.
4. Read `references/chrome-scrape-workflow.md` before scraping.
   - It contains the current WaterlooWorks selectors, modal extraction flow, pagination checks, and the browser-side snippet that saves a scrape JSON file under `/private/tmp`.
   - That main snippet targets a Playwright / Node REPL (`tab.playwright`, `node:fs`). If you are running in **Claude in Chrome** (the in-page `javascript_tool`, with no Playwright and no filesystem), follow the reference's `## Claude-in-Chrome (in-page) variant` section instead — run the scrape loop in-page and exfiltrate the JSON via a blob download.
5. Convert the scrape JSON into Markdown:
   - Run `node .codex/skills/ww-scrape-jobs/scripts/write_jds_from_scrape_json.js --input /private/tmp/waterlooworks-<folder>-scrape.json --out jds/<folder>` (the `--out` directory can be any folder, including a date-named one).
6. Validate the output:
   - Run `node .codex/skills/ww-scrape-jobs/scripts/validate_cycle_folder.js jds/<folder> --expected <count>`.
   - Also sample the first and last generated files with `sed`.

## Output Rules

- Write only inside the chosen `jds/<folder>/`.
- Leave other `jds/` folders untouched.
- Do not remove existing files unless the user explicitly asks to replace that folder's contents.
- Keep filenames ASCII-safe and stable: replace `/`, `\`, control characters, and `:`; collapse whitespace; truncate long titles.
- Drop WaterlooWorks UI-only lines (toolbar labels and Material-icon ligature names) from detail text — the `dropLines` set in `scripts/write_jds_from_scrape_json.js` is the source of truth for which lines are stripped.

## Notes

- WaterlooWorks direct data endpoints may be blocked by the browser sandbox. Prefer the UI workflow in the reference file unless a same-origin read-only endpoint is clearly available and verified.
- If Chrome cannot access WaterlooWorks due to login, MFA, CAPTCHA, or session timeout, stop and ask the user to complete the browser-side step.
