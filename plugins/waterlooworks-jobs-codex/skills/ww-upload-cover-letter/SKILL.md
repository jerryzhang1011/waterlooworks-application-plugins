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

Use the `@chrome` plugin (`plugin://chrome@openai-bundled`) so the task runs against the user's logged-in Chrome session, which WaterlooWorks depends on. Uploads go through the Playwright `filechooser` API the `@chrome` plugin exposes.

- Claim or continue the existing WaterlooWorks `Submit Application` tab; do not start a new unrelated application.
- Do not inspect cookies, local storage, saved passwords, or browser profile internals.
- Use the browser file-chooser flow as the upload method:

```js
const chooserPromise = tab.playwright.waitForEvent("filechooser", { timeoutMs: 10000 });
const fileControl = tab.playwright.locator('input[type="file"]'); // scope to the upload dialog when needed
await fileControl.click({});
const chooser = await chooserPromise;
await chooser.setFiles([coverletterPath]); // absolute path to coverletter/<Company>-coverletter.pdf
```

- Start `waitForEvent("filechooser")` before clicking the file input or its associated upload control.
- Prefer the actual `input[type="file"]` when available. Click a visible button or label only when it opens the chooser.
- Use absolute paths for `setFiles(...)`.
- Use `chooser.isMultiple()` before passing multiple files when needed.
- Do not look for or use `locator.setInputFiles(...)`; uploads are exposed through the chooser object.
- Try the file chooser flow before falling back to a native picker.
- On WaterlooWorks, first try the dialog-scoped Orbis file input (`#fileUpload_docUpload` or `input[type="file"]`) when it is genuinely clickable.
- If the file input is hidden, tiny, or does not emit a chooser, click the associated visible upload button or `label[for="fileUpload_docUpload"]` after arming `waitForEvent("filechooser")`. WaterlooWorks may require opening a nested `Upload Cover Letter` file panel first, then clicking the visible `Choose a file` label in that nested panel.
- If Chrome reports that file upload needs file URL access, tell the user exactly: `To enable file upload, go to chrome://extensions in Chrome, click Details under the Codex extension, and enable "Allow access to file URLs." See [here](https://developers.openai.com/codex/app/chrome-extension#upload-files) for details.`

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

3. Fill the document name:
   - Click the `Name` field.
   - Fill it with `document_name`, usually the organization name from the application header.
   - If the field already contains the desired name, leave it unchanged.

4. Choose the PDF:
   - Use the browser file-chooser flow as the source of truth: start `tab.playwright.waitForEvent("filechooser", { timeoutMs: 10000 })` before clicking a file input or associated upload control, then call `chooser.setFiles([coverletter_path])` with an absolute path.
   - First try the dialog-scoped `input[type="file"]` / `#fileUpload_docUpload` when it is present and clickable.
   - If the input is hidden, tiny, or does not emit a chooser, click the associated visible upload control after arming the chooser listener. On WaterlooWorks this can be `#btn_fileUploadDialog_docUpload`; if it opens a nested file-upload panel, arm a new chooser listener and click the visible `label[for="fileUpload_docUpload"]` / `Choose a file` label in that nested panel.
   - Do not use `locator.setInputFiles(...)`; the documented upload API is `waitForEvent("filechooser")` followed by `chooser.setFiles(...)`.
   - If the native macOS picker appears instead of the chooser API, press Cmd+Shift+G and paste the absolute `coverletter_path`, then choose the file and click `Open`. Use stable labels and the typed path, not raw screen coordinates.
   - If neither the chooser API nor the native picker can be driven, use the `## Fallback — inject bytes via DataTransfer` section below.
   - Wait until WaterlooWorks shows the chosen filename and the `Upload A Document` button is enabled.

5. Upload and verify:
   - NOTE: after the file is staged, a `Current File: …` row appears in the dialog and pushes the `Upload A Document` button DOWN. Re-screenshot / re-locate the button before clicking — clicking its pre-staging position will miss and hit empty space.
   - Click `Upload A Document`.
   - Wait for the upload dialog to close or for the application options page to regain focus.
   - Verify the cover-letter section now shows the uploaded file, such as `Current File: <Company>-coverletter.pdf`, a `Quick View` control for the cover letter, or a new cover-letter document row.
   - Verify the uploaded cover letter is selected. WaterlooWorks may auto-select the uploaded row in some flows, but it may also leave the new row unselected. Check the uploaded cover letter radio in the DOM; if it is unchecked, click the uploaded cover letter's radio/row and verify it is `checked` (and that no other cover-letter option is selected) before handing back. A finished-looking upload that still blocks submission is often this missing selection.
   - Return control to the parent workflow. Do not click `Submit` or `Next` from this skill unless the parent workflow explicitly instructs you to continue after verification.

## Fallback — inject bytes via DataTransfer

Use this only if the file-chooser path in Step 4 (dialog file input, associated visible controls, nested `Choose a file` label, and native picker) has genuinely failed, AND the page exposes `File`, `DataTransfer`, `Uint8Array`, and `atob`. If those constructors are unavailable, stop and ask for manual upload.

Run from the open `Upload Cover Letter` dialog (after clicking `Upload New Cover Letter`):

1. Base64-encode the PDF locally (shell):

   ```bash
   base64 < coverletter/<Company>-coverletter.pdf | tr -d '\n'
   ```

   A one-page letter (~4 KB) becomes ~5 KB of base64 — small enough to embed inline in the JS string below. For a larger file, write the base64 to a temp file and read it into the snippet.

2. Execute this in the WaterlooWorks application tab via the Codex extension's JavaScript-execution tool. It decodes the bytes into a real `File`, assigns it to the hidden Orbis file input through a `DataTransfer`, fires the events the widget listens for, and sets the document name:

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

3. The dialog now shows `Current File: …`. Click `Upload A Document` exactly as in Step 5 — WaterlooWorks issues its own multipart POST to `jobs.htm` (carrying the logged-in session and CSRF token), so you never hand-craft an HTTP request. Then verify the cover-letter section shows the uploaded document and verify whether its radio is selected (Step 5).

**Why it works:** page JS cannot construct a `File` from a disk *path*, but it *can* construct one from *bytes* (supplied via base64) and assign it through `DataTransfer.files`. Letting WaterlooWorks' own handler send the request avoids reverse-engineering the upload endpoint, field names, or CSRF token.

## Failure Handling

- If no cover-letter PDF is found in the `coverletter/` folder, create one first by following the `ww-write-cover-letter` skill (or ask the user for the exact file path), then continue.
- If the file is too large or not a PDF, stop and report the file validation issue.
- If `Upload New Cover Letter` is missing but `Select Existing Cover Letter` is available, do not guess an existing document unless the user explicitly asked to use it.
- If WaterlooWorks shows `Other - Per Job Posting` as required, stop; this skill only handles `Cover Letter`.
- If the chooser path (input, associated visible controls, nested `Choose a file` label, and native picker) all fail, use the `## Fallback — inject bytes via DataTransfer` section — only when the page exposes `File`, `DataTransfer`, `Uint8Array`, and `atob`. If those constructors are unavailable, stop and ask for manual upload.
