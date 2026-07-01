---
name: ww-upload-cover-letter
description: Upload a PDF cover letter from the `coverletter/` folder (typically coverletter/Company-coverletter.pdf produced by `ww-write-cover-letter`) into a required WaterlooWorks `Cover Letter` document slot during the Full-Cycle Service `Submit Application` workflow. Use when a WaterlooWorks application package requires `*Cover Letter`, especially when called from `ww-apply-to-job`; do not use for resumes, grade reports, work histories, or `Other - Per Job Posting` documents.
---

# Upload Cover Letter

## Overview

Upload a cover-letter PDF into the current WaterlooWorks application package without submitting the application. This skill is intended to be called from a WaterlooWorks application flow after `Create Custom Application Package` is selected and a required `*Cover Letter` slot is visible.

The recorded workflow showed WaterlooWorks opening an `Upload Cover Letter` dialog, then a file picker. The stable targets were `Upload New Cover Letter`, the `Name` field, the dialog's actual `input[type="file"]` / `#fileUpload_docUpload` control, the cover-letter PDF in the `coverletter/` folder, and `Upload A Document`.

## Inputs

Require or infer these before starting:

- `application_tab`: a Chrome-controlled WaterlooWorks tab showing `Submit Application` -> `Application Options`.
- `coverletter_path`: default to `coverletter/<Company>-coverletter.pdf` — this is where `ww-write-cover-letter` writes it. If several `coverletter/*-coverletter.pdf` files exist, prefer the one whose company matches the application; ask only if none match or the choice is ambiguous.
- `document_name`: optional display name for the uploaded WaterlooWorks document. Prefer the organization name shown in the application header; otherwise use the base file name without `.pdf`.

Do not upload a non-PDF file. The recorded WaterlooWorks dialog accepted `pdf` and showed a 5.00 MB max file size, so verify the local file exists, is a `.pdf`, and is no larger than 5 MB before uploading.

## Browser Setup

Use the Claude in Chrome connection (the in-page `javascript_tool`) so the task runs against the user's logged-in Chrome session, which WaterlooWorks depends on. Uploads go through the DataTransfer byte-injection method in `## Inject bytes via DataTransfer` below — page JS cannot build a `File` from a disk path, but it can from bytes.

- Claim or continue the existing WaterlooWorks `Submit Application` tab; do not start a new unrelated application.
- Do not inspect cookies, local storage, saved passwords, or browser profile internals.

## Inject bytes via DataTransfer

This is the upload method. It requires the page execution environment to expose `File`, `DataTransfer`, `Uint8Array`, and `atob` (standard in the page context); if those constructors are unavailable, ask for manual upload. Verified working 2026-06-25 (job 476469, Agriculture and Agri-Food Canada) and 2026-06-26 (TribalScale, jobs 476846 / 476849).

Run from the open `Upload Cover Letter` dialog (after clicking `Upload New Cover Letter`):

1. Base64-encode the PDF locally (shell):

   ```bash
   base64 < coverletter/<Company>-coverletter.pdf | tr -d '\n'
   ```

   A one-page letter (~4 KB) becomes ~5 KB of base64 — small enough to embed inline in the JS string below. For a larger file, write the base64 to a temp file and read it into the snippet.

2. Execute this in the WaterlooWorks application tab via the `javascript_tool`. It decodes the bytes into a real `File`, assigns it to the hidden Orbis file input through a `DataTransfer`, fires the events the widget listens for, and sets the document name:

   ```js
   const b64 = "<paste the base64 string here>";
   const bin = atob(b64);
   const bytes = new Uint8Array(bin.length);
   for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
   const file = new File([bytes], "<Company>-coverletter.pdf", { type: "application/pdf" });

   const input = document.getElementById("fileUpload_docUpload"); // Orbis hidden <input type=file class="orbisFileUpload file-upload">
   const dt = new DataTransfer();
   dt.items.add(file);
   input.files = dt.files;                                  // browsers allow assigning a File built from bytes
   input.dispatchEvent(new Event("change", { bubbles: true }));
   input.dispatchEvent(new Event("input", { bubbles: true }));

   const dn = document.getElementById("docName");           // document-name field
   if (dn) {
     dn.value = "<document_name>";
     dn.dispatchEvent(new Event("input", { bubbles: true }));
     dn.dispatchEvent(new Event("change", { bubbles: true }));
   }
   ({ files: input.files.length, name: input.files[0]?.name, size: input.files[0]?.size, docName: dn?.value });
   ```

   - If `#fileUpload_docUpload` is not present, find the dialog's `input[type=file]` (Orbis class `orbisFileUpload file-upload`) and use its id; the name field is `#docName`.
   - Confirm the returned `files` is `1` and `size` matches the local file's byte count before continuing.

3. The dialog now shows `Current File: …`. Click `Upload A Document` by its VISUAL center from a fresh screenshot (NOT the `getBoundingClientRect()` center — it lands ~18px low and misses; see step 5), then confirm the dialog actually closed and retry if it didn't. WaterlooWorks issues its own multipart POST to `jobs.htm` (carrying the logged-in session and CSRF token), so you never hand-craft an HTTP request. Then verify the cover-letter section shows the uploaded document and **select its radio — the upload does NOT auto-select it** (see step 5).

**Why it works:** the extension's `file_upload` is sandboxed to session-shared files, and page JS cannot construct a `File` from a disk *path*. But page JS *can* construct a `File` from *bytes* (which the agent supplies via base64) and assign it through `DataTransfer.files`. Letting WaterlooWorks' own handler send the request avoids reverse-engineering the upload endpoint, field names, or CSRF token.

## Workflow

1. Verify the page context:
   - Confirm the tab is on WaterlooWorks and the visible page says `Submit Application`.
   - Confirm the current step is `Application Options`.
   - Confirm the application still refers to the expected job ID, title, and organization if this skill was called by a parent workflow.
   - Confirm `*Cover Letter` is present or the required package contents include `Cover Letter`.

2. Open the upload dialog:
   - Scope actions to the cover-letter document section, not `Résumé`, `Grade Report`, or `Other - Per Job Posting`.
   - Click `Upload New Cover Letter`.
   - Verify a dialog or panel titled `Upload Cover Letter` appears.

3. Decide the document name:
   - Usually the organization name shown in the application header; otherwise the base file name without `.pdf`.
   - This value goes into the injection in the next step (as `docName`) — you do not click the `Name` field.

4. Stage the PDF via `## Inject bytes via DataTransfer` above:
   - Base64-encode the file and run the injection snippet with your `document_name` as `docName`.
   - Confirm the returned `files` is `1` and `size` matches the local file's byte count.
   - WaterlooWorks then shows `Current File: …` and enables `Upload A Document`.

5. Upload and verify:
   - NOTE: after the file is staged, a `Current File: …` row appears in the dialog and pushes the `Upload A Document` button DOWN. Re-screenshot / re-locate the button before clicking — clicking its pre-staging position will miss and hit empty space.
   - **Click `Upload A Document` by its VISUAL center from a fresh screenshot — do NOT click the raw `getBoundingClientRect()` center.** On this modal the JS rect and the click/screenshot coordinate space don't align (WaterlooWorks screenshots come back at alternating sizes, e.g. 1512×801 vs 1456×825), so a click at the element's `getBoundingClientRect()` center lands low (observed ~18px below the button) and hits empty space. Take a screenshot once the file is staged and click the middle of the visible `Upload A Document` button. (This offset is specific to the modal button; radios elsewhere are usually fine at JS-rect coords.)
   - **Confirm the click registered, and retry if not.** A successful upload closes the dialog and the document appears as a row in the section (and may auto-select). If the dialog is still open after the click (e.g. the `Current File:` row + `Upload A Document` button are still visible), the click missed — re-screenshot and click the button's visual center again. Do not assume one click worked. (Note: `#fileUpload_docUpload` lingers in the DOM even after the dialog closes, so judge "still open" from the screenshot, not from that element's presence.)
   - Wait for the upload dialog to close or for the application options page to regain focus.
   - Verify the cover-letter section now shows the uploaded file, such as `Current File: <Company>-coverletter.pdf`, a `Quick View` control for the cover letter, or a new cover-letter document row.
   - **Select the uploaded cover letter — it is NOT auto-selected.** After the dialog closes the new row appears with an *unselected* radio, and the parent application's `Submit` stays disabled until a cover letter is chosen. Click the uploaded cover letter's radio/row and verify it is `checked` (and that no other cover-letter option is selected) before handing back. A finished-looking upload that still blocks submission is almost always this missing selection.
   - Return control to the parent workflow. Do not click `Submit` or `Next` from this skill unless the parent workflow explicitly instructs you to continue after verification.

## Failure Handling

- If no cover-letter PDF is found in the `coverletter/` folder, create one first by following the `ww-write-cover-letter` skill (or ask the user for the exact file path), then continue.
- If the file is too large or not a PDF, stop and report the file validation issue.
- If `Upload New Cover Letter` is missing but `Select Existing Cover Letter` is available, do not guess an existing document unless the user explicitly asked to use it.
- If WaterlooWorks shows `Other - Per Job Posting` as required, stop; this skill only handles `Cover Letter`.
- If the page does not expose `File`, `DataTransfer`, `Uint8Array`, and `atob` (so the byte-injection can't run), stop and ask for manual upload.
