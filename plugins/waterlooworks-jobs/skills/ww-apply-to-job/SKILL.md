---
name: ww-apply-to-job
description: Apply to WaterlooWorks Full-Cycle Service jobs from a valid WaterlooWorks job ID using the user's logged-in Chrome session. Use when the user asks Claude to apply on WaterlooWorks by job id and provides or can provide both the job ID and the resume/application document label to use. Handles recoverable WaterlooWorks logged-out states by invoking `ww-login`; handles required Cover Letter documents by invoking `ww-upload-cover-letter` against coverletter/Company-coverletter.pdf (generating it with `ww-write-cover-letter` if needed); still stops for required `Other - Per Job Posting`. If the posting says applicants must apply directly to the employer, still apply through WaterlooWorks and return the employer application link in chat.
---

# Apply WaterlooWorks By Job ID

Use Chrome to apply to a WaterlooWorks Full-Cycle Service posting by job ID. This workflow is based on a recorded application flow and should target stable WaterlooWorks labels and page state, not screen coordinates.

If the posting says applicants must apply through WaterlooWorks and directly to the employer, do not treat that as a blocker. Complete the WaterlooWorks application, extract the employer application link, and paste that link in the chat for the user. Do not complete the external employer application unless the user separately asks for that.

## Required Inputs

Require these before starting:

- `job_id`: a valid WaterlooWorks job ID visible in the user's account.
- `resume_name`: the exact or clearly unambiguous visible resume label to select, such as `ai-fall2026`.

Ask for any missing required input. Do not choose a resume by guessing from the job title.

Optional inputs:

- `prescreen_answers`: answers to any pre-screening questions. If a pre-screening question appears and the user has not already provided the answer, pause and ask. Do not infer citizenship, work authorization, eligibility, demographic, or other personal answers from the recording.
- `coverletter_path`: path to a PDF cover letter when the posting requires `Cover Letter`. Default to `coverletter/<Company>-coverletter.pdf`, where `ww-write-cover-letter` writes it.

Output when present:

- `direct_employer_apply_link`: a link from `Application Information` -> `Additional Application Information` when the posting says `Interested applicants must apply through WaterlooWorks and directly to the employer to be considered for this position`.

## User Input Logging

Whenever this skill asks the user for input, record the exact question and exact answer after the user replies. Do not edit the log file directly. Use the bundled helper — it lives in this skill's own `scripts/` directory. Resolve `<skill dir>` to the absolute path shown as "Base directory for this skill:" when this skill loads. (Under a plugin install that path is inside the plugin cache; a literal `.claude/skills/…` path is only correct for a local repo checkout, so do not hardcode it.)

```bash
python3 "<skill dir>/scripts/question_log.py" add \
  --question "exact question shown to the user" \
  --answer "exact user answer" \
  --job-id "<job_id>" \
  --context step=pre-screening
```

- Run the command from the chat's starting/current working directory so the default log file is saved there as `.codex_user_input_log.jsonl`. In this workspace, that directory is the project root — the folder that contains `jds/`, `resume/`, and `coverletter-config.json`.
- To inspect recorded inputs, run `python3 "<skill dir>/scripts/question_log.py" list` from the same directory.
- To correct an entry, use the script's `update --id ...` command. Do not manually edit `.codex_user_input_log.jsonl`.
- Record only user-provided answers. Do not invent or infer citizenship, work authorization, eligibility, demographic, or other personal answers.

## Chrome Setup

Use the `@chrome` / `chrome:control-chrome` workflow when available so the task runs in the user's existing Chrome profile and WaterlooWorks login state.

- Start a new Chrome browser session/tab group for this workflow so the agent does not conflict with the user's active Chrome control.
- Do not claim or operate on an existing user-controlled WaterlooWorks tab unless the user explicitly asks to continue from that tab.
- Open a new agent-controlled tab to WaterlooWorks. The new tab can use the same logged-in Chrome profile, but all navigation and clicks should happen in the new tab group.
- If WaterlooWorks lands on a recoverable logged-out state (`notLoggedIn.htm`, `WaterlooWorks - Not Logged In`, WaterlooWorks home, or `waterloo.htm?action=login`), load and follow `.claude/skills/ww-login/SKILL.md` before asking the user for help.
- Ask the user to operate Chrome only when `ww-login` reaches a username/password page, SSO/WatIAM/Microsoft prompt, Duo/MFA, CAPTCHA, or another credential-only step.
- After `ww-login` reports success, re-open or re-check the requested WaterlooWorks page before continuing; never assume the previous application state survived the redirect.
- Do not inspect cookies, local storage, saved passwords, or browser profile internals.
- Treat the user's request to apply to the specified job with the specified resume as approval to submit the WaterlooWorks application after the job, answers, and required documents are verified. Do not add a final confirmation pause before clicking `Submit`.
- At the end, close agent-created intermediate tabs unless the user needs a handoff page left open for login, missing required answers, or further manual action.
- Tab lifecycle for a batch: each `Apply` opens a NEW WaterlooWorks tab for the `Submit Application` flow; clicking `Done` on the `Confirmation` step CLOSES that tab (it may briefly read `Error loading tab`). Keep the persistent search-results tab alive and run each next job's search there — do not expect the application tab to survive between jobs.
- Cancelling an in-progress application opens an `Are you sure you would like to cancel?` confirm dialog — click `Yes` to discard it.

### Resuming After User Input

If the workflow pauses for a pre-screening answer or other required user input, the browser-control session may expire before the user replies. When resuming:

- Reconnect to Chrome using the `chrome:control-chrome` bootstrap before taking any page action.
- Re-open the user's current Chrome tab list and find WaterlooWorks tabs at `https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm`, preferring tabs in the agent-created tab group for this job when available.
- Claim the newest matching WaterlooWorks tab. If it shows a recoverable logged-out state, run `.claude/skills/ww-login/SKILL.md`, then re-open the job/application page and inspect the DOM again.
- Verify the tab still shows `Submit Application` and the requested `job_id` before continuing from the visible step instead of restarting the job search or clicking `Apply` again.
- If the application tab closed itself after a successful action such as `Done`, claim the remaining search-results tab and verify the row state there.
- **Detect a silent mid-batch logout:** the session can drop without warning during a submit. Symptoms: the application tab navigates to `notLoggedIn.htm`, and/or other WaterlooWorks tabs hang on `Loading…` forever or show pagination `/NaN`. If you see these, run `.claude/skills/ww-login/SKILL.md` once to restore the session. Stop and ask the user only if `ww-login` reaches credentials, SSO/MFA, CAPTCHA, or loops back to logged-out state.
- **The `Confirmation` screen is proof — verify only when you did NOT see it:** the `Confirmation` screen showing "Your application package for Job ID <job_id> has been submitted on <date>" means the submit landed — trust it and finish, no re-search needed. Only re-search the in-flight `job_id` for an `Application Submitted` badge when the session dropped BEFORE that screen rendered (e.g. the tab went to `notLoggedIn.htm` or hung at submit) and you never saw the submitted message. Re-run the application only if the badge is absent; never re-submit a job whose confirmation screen you already saw.

## Workflow

1. Open the jobs page:
   - Use the new agent-controlled Chrome tab group/session created for this task.
   - Navigate through `CO-OP JOBS` -> `Full-Cycle Service` -> `Jobs / Applications`, or open `https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm`.
   - If navigation lands on `notLoggedIn.htm`, `WaterlooWorks - Not Logged In`, WaterlooWorks home, or `waterloo.htm?action=login`, run `.claude/skills/ww-login/SKILL.md` with `return_url` set to the jobs page, then verify the jobs page loaded.
   - If already on the jobs page with usable state, do not reload unnecessarily.

2. Search by job ID:
   - **Use the big landing "Keyword" box** — the visible text input with placeholder `Enter a keyword, job title, job ID, etc.` Do NOT use the `Keyword Search (All of these words)` field: a `find` for the search box surfaces that one FIRST, but it is a hidden/secondary control whose typing + magnifier silently no-op (value never lands, search never filters). Target the big landing box only.
   - **Reset before each job by navigating fresh** to `https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm`. This returns an empty landing keyword box — simpler and more reliable than clearing chips. (Background: the UI otherwise ADDs each keyword as a separate AND-combined token, so reusing a stale keyword returns 0 results.)
   - **Type the `job_id`, then READ BACK the input's `value` before submitting.** Typing into this box silently fails immediately after a navigation (the value stays empty). If `value !== job_id`, click the box again and retype; only proceed once the value equals the job id.
   - **Submit with `Enter`** once the value is confirmed present. The big box has no magnifier, so Enter is the submit. (The earlier "use the magnifier, avoid Enter" guidance was for a different field.) Note: the first Enter right after a fresh navigation can still return the full all-jobs list **even when you have confirmed the value is present** — it's a timing quirk, not proof the value was missing. Don't keep re-pressing Enter on the same page; the reliable cure is the navigate-fresh + retype + Enter retry in the next bullet.
   - Confirm the search actually filtered before trusting the results: the active filter chip should read `Keyword: All of these words: <job_id>` and the result count should be 1. If you still see the full job list, the keyword did not apply — retype (verifying the value) and press Enter again.
   - Verify exactly one result row/card has ID equal to `job_id`.
   - If there is no exact match, stop and report that the job ID was not found in WaterlooWorks.
   - **Detect already-applied:** open the posting (click its title) and read the detail panel's status badges. An `Application Submitted` badge — shown alongside `NEW` / `Deadline in N day(s)` / `Viewed` — means it is already applied; skip/stop and report. (A `Cancel Application` row action is the equivalent signal in the older table UI.)

3. Inspect additional application information:
   - Before clicking `Apply`, open the matching job's details or quick view using the job title link or `Quick View`.
   - Find `Application Information` -> `Additional Application Information`.
   - If it contains `Interested applicants must apply through WaterlooWorks and directly to the employer to be considered for this position`, extract the employer application URL from the same section. Prefer the actual `href` of the link over visible shortened text.
   - Store the URL as `direct_employer_apply_link` and continue with the WaterlooWorks application.
   - If that direct-employer sentence is present but no link is visible, continue applying through WaterlooWorks and report that the note was present but no employer link was found.
   - Return to the search result or close the detail view before starting the application.

4. Start the application:
   - Results render as **cards** (`.doc-viewer__card`), not a table, and there is usually no inline `Apply` button in the card. Open the posting (click the job title) and click the `Apply` button in the **job detail panel** — its navigation row at the bottom of the posting. Locate it by its accessible name `Apply` (e.g. a `find` for "Apply button in job details panel") rather than a `tr:has(input#resultRow_...)` selector.
   - WaterlooWorks may open the `Submit Application` workflow in a new tab with the same base jobs URL instead of navigating the search-results tab. Before clicking `Apply`, record the current open Chrome tabs from both the agent tab list and Chrome's full user tab list when available. After clicking, inspect newly opened WaterlooWorks tabs from the full user tab list as well as the agent tab list, then claim the newest tab in the agent-created tab group if one appears.
   - If a new WaterlooWorks tab appears, switch to that tab and inspect its DOM even if its title and URL still look like `Jobs / Applications`; the visible body may contain the `Submit Application` form.
   - If no new tab appears, check the current tab for the `Submit Application` form before retrying. Do not repeatedly click `Apply` after a new application tab has already opened.
   - Verify the `Submit Application` page header contains the requested `job_id`.
   - Capture the job title, organization, and deadline shown on the application page for verification and final reporting.

5. Handle pre-screening questions:
   - If a `Pre-Screening Questions` step appears, answer only from explicit user-provided `prescreen_answers`.
   - Scope pre-screening controls to the visible question on the current step. WaterlooWorks may keep hidden application-option selects in the DOM before the `Application Options` step, so do not target a broad `select` locator without checking visibility and question context.
   - If there are multiple `select` elements, identify the visible pre-screening select by checking bounding boxes and option labels. Hidden application document selects may already be in the DOM and must not be targeted.
   - Before asking the user, check the prior log for an already-answered version of this question: run `python3 "<skill dir>/scripts/question_log.py" list` and look for an entry whose `question` text matches (ignore the `job_id` — it will differ across postings). If the question is about the applicant's own circumstances (co-op sequence/8-month commitment, work authorization confirmed earlier, remote/in-office availability, relocation radius, etc.) and the text matches an earlier entry, reuse that recorded answer silently instead of re-asking. Only treat a logged answer as job-specific (and re-ask) when the question embeds details that genuinely vary by posting, such as a specific office city or a posting-unique skill claim.
   - If any answer is missing, ask the user for the exact answer and wait. After the user answers, record the question and answer with `<skill dir>/scripts/question_log.py add` before using the answer in WaterlooWorks. When you reuse a prior logged answer without asking, do not add a duplicate log entry.
   - Continue with `Next` only after required questions have been answered, then **verify the step actually advanced by DOM state, not by text matching.** Do NOT decide which step you are on with an `innerText` regex for `Pre-Screening Questions` / `Application Options` / `Confirmation` — all three appear in the persistent stepper sidebar, so such a regex false-positives and reports the wrong step. Instead key off concrete controls: you are on Application Options once the `Create Custom Application Package` radio (`input[value="customPkg"]`) is present and visible; you are still on Pre-Screening while the question's select/toggle controls are visible. Also note the `find` tool mislabels step buttons (it has called a stale "Next Page" ref that does nothing, and called a `Done` button "the final submit button"); if a `find`-located Next/Submit click does not change the DOM state, click the VISIBLE button by its screenshot coordinates and re-check.

6. Configure application options:
   - Select `Create Custom Application Package` so the requested resume can be chosen directly.
   - **Radios here are 1px/custom controls and resist programmatic selection.** Clicking via an element ref/handle, Playwright `check()`, a direct input `.click()`, or dispatched events frequently leaves `checked` FALSE. Reliable pattern for EVERY radio (custom package, résumé, cover letter, work history, grade report): (a) read the target input's `getBoundingClientRect()`, (b) issue a real pointer click at that rect's center coordinates (the `computer`/CUA click, not a ref click), (c) verify `checked === true` on that input (and that sibling radios in the group are unchecked) before moving on. If it did not stick, do NOT just re-click the same rect center — the JS rect and the screenshot/click coordinate space can be offset by ~10–18px (the same mismatch documented for the modal `Upload A Document` button, and observed on the résumé radios). Take a fresh screenshot and click the VISIBLE radio circle at its on-screen center, then re-verify `checked`.
   - **Re-read the rect immediately before each click** — positions shift after scrolling, and selecting one document (e.g. a cover letter) can re-render the list and move the résumé rows. Do not reuse a coordinate captured before a scroll or a prior selection.
   - Leave the auto-generated `Application Package Name` unchanged unless the user explicitly asked for a different name.
   - Review the document requirements list before choosing documents.

7. Enforce this skill's document scope:
   - Treat `Cover Letter` and `Other - Per Job Posting` as required if they appear with a leading `*`, are listed in the required package contents, or WaterlooWorks blocks submission until they are selected.
   - If `Cover Letter` is required, get the PDF in place before touching the document controls:
     1. **Generate it in a sub-agent.** Spawn a sub-agent that follows the `ww-write-cover-letter` skill for this posting, passing the résumé this application uses (`resume_name`, i.e. `resume/<resume_name>.pdf`). It writes `coverletter/<Company>-coverletter.pdf`. Delegating to a sub-agent keeps your browser-application context focused while it does the JD/résumé reading and drafting.
        - **Give it the JD the right way:** if a JD file for this job ID already exists under `jds/`, just pass the job ID — the sub-agent reads it locally. If it does NOT (e.g. you applied by ID directly and never scraped this posting), the sub-agent can neither see your browser nor find a local file, so extract the JD text from the open posting and pass that text/facts in the prompt. Do not pass raw JD text when the `jds/` file already exists — let the sub-agent read the file.
        - Skip regeneration entirely if the user supplied `coverletter_path`, or a current `coverletter/<Company>-coverletter.pdf` for this company already exists.
     2. **Upload it.** Load and follow the `ww-upload-cover-letter` skill with `coverletter_path` set to the path the sub-agent reports.
   - After invoking `ww-upload-cover-letter`, verify the cover-letter section shows the uploaded/current file before selecting the remaining documents.
   - If `Other - Per Job Posting` is required, stop and tell the user this workflow does not handle that document type yet.
   - If optional `Cover Letter` or `Other - Per Job Posting` upload/select controls appear with no required marker, leave them blank unless the user explicitly asked to include one.

8. Select required documents:
   - If a required cover letter was uploaded by `ww-upload-cover-letter`, make sure its radio is actually **selected**. Uploading may or may not auto-select the new row (it has been observed to auto-select). Check the cover-letter radio's `checked` state in the DOM; if it is unchecked, click the uploaded cover letter's row/radio and re-verify `checked`. `Submit` stays disabled until a cover letter is selected.
   - **Resuming after an interruption/logout:** an already-uploaded cover letter persists server-side in the document library, but the required slot will NOT pre-populate it on a fresh application attempt. Rather than re-uploading a duplicate, click `Select Existing Cover Letter`, pick the `<Company>` document from the dropdown, click the dialog's `Select`, then verify the cover-letter radio is `checked`. (Only use `Select Existing` for a document you uploaded for THIS company — do not guess an unrelated existing one.)
   - Keep or select the existing `University of Waterloo Co-op Work History` when it is required. If multiple choices appear, choose the already-selected/default option; ask if none is selected and there is more than one.
   - Select the resume radio option whose visible label exactly matches `resume_name`. If the user provided a filename ending such as `.pdf` but WaterlooWorks shows the same base label without the extension, treat that as an unambiguous match. If there is no exact or unambiguous base-label match, list the visible resume labels and ask the user which to use.
   - For resume radios, use the same custom-control handling as `Create Custom Application Package`: if the radio input is tiny/hidden or `check()` does not stick, click the visible row for the matching resume label and verify that the matching radio is checked while the other resume radios are unchecked.
   - Keep or select the existing `Grade Report` when it is required. If multiple choices appear, choose the already-selected/default option; ask if none is selected and there is more than one.

9. Submit and verify:
   - When WaterlooWorks enables `Submit`, verify locally that the page still refers to the requested job ID, job title, organization, deadline, and selected resume, then click `Submit` without asking the user for an extra confirmation.
   - If a confirmation step or modal appears, verify it still refers to the same job ID and selected package, then complete the final confirm/submit action without asking the user again.
   - Stop before submitting only when the page shows a different job, a different resume/package, an unexpected required document or answer, a login/CAPTCHA, or an external employer application form that the user did not separately ask to complete.
   - The `Confirmation` screen is definitive success: once the page shows "Your application package for Job ID <job_id> has been submitted on <date>", the application is complete. Click `Done` to finish (this closes the application tab) — do NOT re-search the posting or hunt for an `Application Submitted` badge as extra verification.
   - Report the final state succinctly. If `direct_employer_apply_link` was found, paste it in the chat with a clear note that the posting also requires applying directly to the employer.

## Stable Labels From Recording

The recorded demo used these WaterlooWorks controls and labels:

- Recoverable login refresh: `WaterlooWorks - Not Logged In` -> `Log Into WaterlooWorks` -> `Students/Alumni/Staff` -> `University of Waterloo - MyAccount - Dashboard`
- `CO-OP JOBS` -> `Full-Cycle Service` -> `Jobs / Applications`
- Keyword field accepting a job ID
- Matching result row with an `Apply` button
- Job detail section `Application Information` -> `Additional Application Information`
- `Submit Application`
- `Pre-Screening Questions`, `Application Options`, `Confirmation`
- `Create Custom Application Package`
- Required document sections for `University of Waterloo Co-op Work History`, `Résumé`, and `Grade Report`
- Optional sections may include `Cover Letter` and `Other - Per Job Posting`
- Required cover-letter uploads use the sibling `ww-upload-cover-letter` skill and the stable targets `Upload New Cover Letter`, `Upload Cover Letter`, the dialog's actual `input[type="file"]` / `#fileUpload_docUpload`, and `Upload A Document`
