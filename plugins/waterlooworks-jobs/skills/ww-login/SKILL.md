---
name: ww-login
description: Restore a WaterlooWorks Chrome session when Claude is viewing or applying to WaterlooWorks jobs and lands on recoverable logged-out states such as `notLoggedIn.htm`, `WaterlooWorks - Not Logged In`, the WaterlooWorks home page, or `waterloo.htm?action=login`. Use before asking the user to log in; stop and ask only when username/password, Duo/MFA, CAPTCHA, or another credential prompt is required.
---

# WaterlooWorks Login Refresh

## Overview

Restore the user's existing WaterlooWorks session in Chrome without handling credentials. This skill follows the recorded refresh path: `notLoggedIn.htm` -> `Log Into WaterlooWorks` -> WaterlooWorks home -> `Students/Alumni/Staff` -> authenticated MyAccount dashboard.

Use this only with the user's existing Chrome profile/session. Do not inspect cookies, local storage, saved passwords, or browser profile internals.

## Inputs

- `application_tab` or `jobs_tab`: a Chrome-controlled WaterlooWorks tab that may be logged out.
- `return_url`: optional WaterlooWorks URL to reopen after refresh. Default to `https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm`.

## Recoverable States

Treat these as recoverable without user help:

- URL contains `waterlooworks.uwaterloo.ca/notLoggedIn.htm`.
- Page title or heading contains `WaterlooWorks - Not Logged In`.
- Page shows a `Log Into WaterlooWorks` link.
- Page is `https://waterlooworks.uwaterloo.ca/home.htm` and shows `Students/Alumni/Staff`.
- URL is `https://waterlooworks.uwaterloo.ca/waterloo.htm?action=login` and the tab is redirecting or already titled `University of Waterloo - MyAccount - Dashboard`.

Stop and ask the user to complete login manually when the page shows any username/password field, Microsoft/WatIAM/SSO sign-in form, Duo/MFA approval, CAPTCHA, browser permission prompt, or explicit authentication error. After the user says they are done, run this skill again and verify the session.

## Workflow

1. Claim or continue the relevant WaterlooWorks Chrome tab. If no tab is supplied, open `return_url` in the user's existing Chrome profile.
2. Inspect the visible page title, URL, and accessible link/button labels.
3. If already authenticated under `/myAccount/`, return success. If the tab shows the MyAccount dashboard after a redirect, navigate to `return_url` and verify it loads.
4. If on `notLoggedIn.htm` or a `WaterlooWorks - Not Logged In` page, click the link named `Log Into WaterlooWorks`. Wait for navigation to the WaterlooWorks home page.
5. If on the WaterlooWorks home page, click the `Students/Alumni/Staff` link. Wait for the redirect to finish.
6. If the tab reaches `University of Waterloo - MyAccount - Dashboard` or any authenticated `/myAccount/` page, navigate to `return_url` if needed.
7. Verify success by checking that the final page URL is under `waterlooworks.uwaterloo.ca/myAccount/` and does not show `notLoggedIn.htm`, credential fields, or a logged-out heading.

## Failure Handling

- If the recovery clicks loop back to `notLoggedIn.htm` twice, stop and ask the user to complete login manually.
- If a credential, MFA, or CAPTCHA page appears, stop and ask the user to operate the browser. Do not type credentials or answer MFA prompts.
- If the original workflow was applying to a job, return control to the parent skill after login restoration; the parent must re-check the job ID, selected documents, and submission state before continuing.
