---
name: ww-apply-to-job
description: Apply to WaterlooWorks Full-Cycle Service jobs from a valid WaterlooWorks job ID using the user's logged-in Chrome session. Use when the user asks Codex to apply on WaterlooWorks by job id and provides or can provide both the job ID and the resume/application document label to use. Handles recoverable WaterlooWorks logged-out states by invoking `ww-login`; handles required Cover Letter documents by invoking `ww-upload-cover-letter` against coverletter/Company-coverletter.pdf (generating it with `ww-write-cover-letter` if needed); still stops for required `Other - Per Job Posting`. If the posting says applicants must apply directly to the employer, still apply through WaterlooWorks and return the employer application link in chat.
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

Whenever this skill asks the user for input, record the exact question and exact answer after the user replies. Do not edit the log file directly. Use the bundled helper:

```bash
python3 .codex/skills/ww-apply-to-job/scripts/question_log.py add \
  --question "exact question shown to the user" \
  --answer "exact user answer" \
  --job-id "<job_id>" \
  --context step=pre-screening
```

- Run the command from the chat's starting/current working directory so the default log file is saved there as `.codex_user_input_log.jsonl`. In this workspace, that directory is the project root — the folder that contains `jds/`, `resume/`, and `coverletter-config.json`.
- To inspect recorded inputs, run `python3 .codex/skills/ww-apply-to-job/scripts/question_log.py list` from the same directory.
- To correct an entry, use the script's `update --id ...` command. Do not manually edit `.codex_user_input_log.jsonl`.
- Record only user-provided answers. Do not invent or infer citizenship, work authorization, eligibility, demographic, or other personal answers.

## Chrome Setup

Use the `@chrome` / `chrome:control-chrome` workflow when available so the task runs in the user's existing Chrome profile and WaterlooWorks login state.

- Start a new Chrome browser session/tab group for this workflow so Codex does not conflict with the user's active Chrome control.
- Do not claim or operate on an existing user-controlled WaterlooWorks tab unless the user explicitly asks to continue from that tab.
- Open a new agent-controlled tab to WaterlooWorks. The new tab can use the same logged-in Chrome profile, but all navigation and clicks should happen in the new tab group.
- If WaterlooWorks lands on a recoverable logged-out state (`notLoggedIn.htm`, `WaterlooWorks - Not Logged In`, WaterlooWorks home, or `waterloo.htm?action=login`), load and follow `.codex/skills/ww-login/SKILL.md` before asking the user for help.
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
- Claim the newest matching WaterlooWorks tab. If it shows a recoverable logged-out state, run `.codex/skills/ww-login/SKILL.md`, then re-open the job/application page and inspect the DOM again.
- Verify the tab still shows `Submit Application` and the requested `job_id` before continuing from the visible step instead of restarting the job search or clicking `Apply` again.
- If the application tab closed itself after a successful action such as `Done`, claim the remaining search-results tab and verify the row state there.
- **Detect a silent mid-batch logout:** the session can drop without warning during a submit. Symptoms: the application tab navigates to `notLoggedIn.htm`, and/or other WaterlooWorks tabs hang on `Loading…` forever or show pagination `/NaN`. If you see these, run `.codex/skills/ww-login/SKILL.md` once to restore the session. Stop and ask the user only if `ww-login` reaches credentials, SSO/MFA, CAPTCHA, or loops back to logged-out state.
- **The `Confirmation` screen is proof — verify only when you did NOT see it:** the `Confirmation` screen showing "Your application package for Job ID <job_id> has been submitted on <date>" means the submit landed — trust it and finish, no re-search needed. Only re-search the in-flight `job_id` for an `Application Submitted` badge when the session dropped BEFORE that screen rendered (e.g. the tab went to `notLoggedIn.htm` or hung at submit) and you never saw the submitted message. Re-run the application only if the badge is absent; never re-submit a job whose confirmation screen you already saw.

## Workflow

1. Open the jobs page:
   - Use the new agent-controlled Chrome tab group/session created for this task.
   - Navigate through `CO-OP JOBS` -> `Full-Cycle Service` -> `Jobs / Applications`, or open `https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm`.
   - If navigation lands on `notLoggedIn.htm`, `WaterlooWorks - Not Logged In`, WaterlooWorks home, or `waterloo.htm?action=login`, run `.codex/skills/ww-login/SKILL.md` with `return_url` set to the jobs page, then verify the jobs page loaded.
   - If already on the jobs page with usable state, do not reload unnecessarily.

2. Search by job ID:
   - Use the keyword field labeled like `Enter a keyword, job title, job ID, etc.` or `Keyword Search (All of these words)`.
   - **Clear any existing keyword first.** This UI ADDS each new keyword as a separate token (the chip shows e.g. `Keyword 2`) and AND-combines them, so reusing one tab across multiple job_ids without clearing returns 0 results. Click `Clear Filters` (or remove the existing keyword chip) before typing the new `job_id`.
   - Type `job_id`, then submit using the visible search control for the current page state:
     - If the loaded search/table view shows a `Submit Keyword` search/magnifier button beside `Keyword Search (All of these words)`, click that button.
     - If the empty Job Search overview only shows the large `Enter a keyword, job title, job ID, etc.` field and no search/magnifier button is visible, press a real `Enter` key on the focused field. This can transition to the result table with the keyword filter applied.
     - Do not rely on a programmatically dispatched synthetic `KeyboardEvent`; use real browser input (`press("Enter")` / CUA keypress) or the visible button.
   - Confirm the search actually filtered before trusting the results: the active filter chip should read `Keyword: All of these words: <job_id>` and the result count should be small. If you still see the full job list, the keyword did not apply — use the keyword field in the loaded search/table view and click `Submit Keyword`, or clear filters and retype.
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
   - Results may render as a table row or as cards. Prefer opening the posting (click the job title) and clicking the `Apply` button in the **job detail panel** after checking status badges and additional application information. Locate it by its accessible name `Apply` within the detail dialog/panel, not by a brittle table selector.
   - If using an inline table-row `Apply` button instead, scope it to the row whose ID is exactly `job_id`, verify it is the only matching row, and do not click it again after a new application tab has opened.
   - WaterlooWorks may open the `Submit Application` workflow in a new tab with the same base jobs URL instead of navigating the search-results tab. Before clicking `Apply`, record the current open Chrome tabs from both the agent tab list and Chrome's full user tab list when available. After clicking, inspect newly opened WaterlooWorks tabs from the full user tab list as well as the agent tab list, then claim the newest tab in the agent-created tab group if one appears.
   - If a new WaterlooWorks tab appears, switch to that tab and inspect its DOM even if its title and URL still look like `Jobs / Applications`; the visible body may contain the `Submit Application` form.
   - If no new tab appears, check the current tab for the `Submit Application` form before retrying. Do not repeatedly click `Apply` after a new application tab has already opened.
   - Verify the `Submit Application` page header contains the requested `job_id`.
   - Capture the job title, organization, and deadline shown on the application page for verification and final reporting.

5. Handle pre-screening questions:
   - If a `Pre-Screening Questions` step appears, answer only from explicit user-provided `prescreen_answers`.
   - Scope pre-screening controls to the visible question on the current step. WaterlooWorks may keep hidden application-option selects in the DOM before the `Application Options` step, so do not target a broad `select` locator without checking visibility and question context.
   - If there are multiple `select` elements, identify the visible pre-screening select by checking bounding boxes and option labels. Hidden application document selects may already be in the DOM and must not be targeted.
   - Before asking the user, check the prior log for an already-answered version of this question: run `python3 .codex/skills/ww-apply-to-job/scripts/question_log.py list` and look for an entry whose `question` text matches (ignore the `job_id` — it will differ across postings). If the question is about the applicant's own circumstances (co-op sequence/8-month commitment, work authorization confirmed earlier, remote/in-office availability, relocation radius, etc.) and the text matches an earlier entry, reuse that recorded answer silently instead of re-asking. Only treat a logged answer as job-specific (and re-ask) when the question embeds details that genuinely vary by posting, such as a specific office city or a posting-unique skill claim.
   - If any answer is missing, ask the user for the exact answer and wait. After the user answers, record the question and answer with `scripts/question_log.py add` before using the answer in WaterlooWorks. When you reuse a prior logged answer without asking, do not add a duplicate log entry.
   - Continue with `Next` only after required questions have been answered.

6. Configure application options:
   - Select `Create Custom Application Package` so the requested resume can be chosen directly.
   - WaterlooWorks radio controls may be implemented as 1px inputs inside larger visible rows. If Playwright `check()` or a direct input click does not change the checked state, inspect the input and parent row geometry, click the visible row/control area, then verify `checked === true` in the DOM before proceeding.
   - Leave the auto-generated `Application Package Name` unchanged unless the user explicitly asked for a different name.
   - Review the document requirements list before choosing documents.

7. Enforce this skill's document scope:
   - Treat `Cover Letter` and `Other - Per Job Posting` as required if they appear with a leading `*`, are listed in the required package contents, or WaterlooWorks blocks submission until they are selected.
   - If `Cover Letter` is required, get the PDF in place before touching the document controls:
     1. **Generate it in a sub-agent.** Spawn a sub-agent that follows `.codex/skills/ww-write-cover-letter/SKILL.md` for this posting, passing the job ID and the résumé this application uses (`resume_name`, i.e. `resume/<resume_name>.pdf`). It writes `coverletter/<Company>-coverletter.pdf`. Delegating to a sub-agent keeps your browser-application context focused while it does the JD/résumé reading and drafting. (Skip regeneration if the user supplied `coverletter_path`, or a current `coverletter/<Company>-coverletter.pdf` for this company already exists.)
     2. **Upload it.** Load and follow `.codex/skills/ww-upload-cover-letter/SKILL.md` with `coverletter_path` set to the path the sub-agent reports.
   - After invoking `ww-upload-cover-letter`, verify the cover-letter section shows the uploaded/current file before selecting the remaining documents.
   - If `Other - Per Job Posting` is required, stop and tell the user this workflow does not handle that document type yet.
   - If optional `Cover Letter` or `Other - Per Job Posting` upload/select controls appear with no required marker, leave them blank unless the user explicitly asked to include one.

8. Select required documents:
   - If a required cover letter was uploaded by `ww-upload-cover-letter`, make sure its radio is actually **selected**. WaterlooWorks may auto-select the newly uploaded cover letter, but do not assume that. Verify it reads `checked` in the DOM; if it is not checked, click the uploaded cover letter's row/radio and verify it again. Do not open `Select Existing Cover Letter` for the just-uploaded file.
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
