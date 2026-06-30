# Chrome Scrape Workflow

Use this reference after loading the Chrome control skill and opening:

`https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm`

## Page Setup

1. Choose the filter in the visible WaterlooWorks UI:
   - If the user did not request a filter, default to `For my program` / `My Program`.
   - If the user requested another WaterlooWorks filter, keyword search, or filter combination, apply that instead.
2. When using `For my program`, click `My Program toggle_off` and verify:
   - `My Program toggle_on`
   - filter count is `filter_list 1`
   - chip says `My Program: Yes`
3. When using another filter/search, verify the visible chips, keywords, toggles, and result count match the user's request.
4. Confirm result count from page text, for example `237 results 1 - 50`.

## Scraper Snippet (Playwright / Node REPL)

Run this in the Chrome plugin Node REPL after `globalThis.tab` points at the filtered WaterlooWorks tab. Change `cycleNumber` before running. **This snippet requires `globalThis.tab.playwright`, `nodeRepl`, and `node:fs`** — i.e. a Codex/Playwright-style REPL. If you are using Claude in Chrome (the in-page `javascript_tool`), skip this and use the `## Claude-in-Chrome (in-page) variant` section below.

```js
var cycleNumber = 3;
var tmpPath = `/private/tmp/waterlooworks-cycle${cycleNumber}-scrape.json`;
globalThis.wwJobs = {};
globalThis.wwErrors = [];

globalThis.wwCloseModal = async function () {
  await globalThis.tab.cua.keypress({ keys: ["Escape"] }).catch(async () => {
    await globalThis.tab.playwright.locator("body").press("Escape", {}).catch(() => {});
  });
  for (let i = 0; i < 20; i++) {
    const n = await globalThis.tab.playwright.evaluate(
      () => document.querySelectorAll(".modal.is--visible").length,
      undefined,
      { timeoutMs: 5000 }
    );
    if (n === 0) return;
    await globalThis.tab.playwright.waitForTimeout(150);
  }
};

globalThis.wwExtractRows = async function () {
  return await globalThis.tab.playwright.evaluate(
    () => {
      const clean = (s) => (s || "").replace(/\s+/g, " ").trim();
      return Array.from(document.querySelectorAll("table tbody tr"))
        .map((tr) => {
          const cells = Array.from(tr.children).map((td) => clean(td.innerText || td.textContent));
          const idInput = tr.querySelector('input[name="dataViewerSelection"]');
          const link = tr.querySelector("a.overflow--ellipsis");
          if (!idInput || !/^\d+$/.test(idInput.value) || !link) return null;
          return {
            id: idInput.value,
            title: clean(link.textContent),
            organization: cells[2] || "",
            division: cells[3] || "",
            openings: cells[4] || "",
            city: cells[5] || "",
            level: cells[6] || "",
            apps: cells[7] || "",
            appDeadline: cells[8] || "",
          };
        })
        .filter(Boolean);
    },
    undefined,
    { timeoutMs: 15000 }
  );
};

globalThis.wwExtractDetail = async function (expectedId) {
  for (let i = 0; i < 40; i++) {
    const detail = await globalThis.tab.playwright.evaluate(
      (id) => {
        const modal = document.querySelector(".modal.is--visible");
        const reader = modal?.querySelector(".is--long-form-reading");
        const text = reader ? reader.innerText : "";
        const modalText = modal ? modal.innerText : "";
        return { text, ready: !!text && modalText.indexOf(String(id)) !== -1 };
      },
      expectedId,
      { timeoutMs: 10000 }
    );
    if (detail.ready) return detail.text;
    await globalThis.tab.playwright.waitForTimeout(250);
  }
  throw new Error("Timed out waiting for detail modal for " + expectedId);
};

globalThis.wwScrapeCurrentPage = async function () {
  await globalThis.wwCloseModal();
  const rows = await globalThis.wwExtractRows();
  const results = [];
  for (const row of rows) {
    if (globalThis.wwJobs[row.id]) {
      results.push({ id: row.id, skipped: true });
      continue;
    }
    const link = globalThis.tab.playwright.locator(
      "tr:has(input#resultRow_" + row.id + ") a.overflow--ellipsis"
    );
    const count = await link.count();
    if (count !== 1) throw new Error("Expected one link for " + row.id + ", got " + count);
    await link.click({});
    const detailText = await globalThis.wwExtractDetail(row.id);
    globalThis.wwJobs[row.id] = { ...row, detailText };
    results.push({ id: row.id, title: row.title, detailChars: detailText.length });
    await globalThis.wwCloseModal();
  }
  return {
    pageRows: rows.length,
    scraped: results.length,
    first: results[0],
    last: results[results.length - 1],
    totalStored: Object.keys(globalThis.wwJobs).length,
  };
};

globalThis.wwGoToPage = async function (pageNumber) {
  await globalThis.wwCloseModal();
  const before = await globalThis.wwExtractRows();
  const beforeFirst = before[0]?.id;
  const loc = globalThis.tab.playwright
    .locator("a.pagination__link")
    .filter({ hasText: String(pageNumber) });
  const count = await loc.count();
  if (count !== 1) throw new Error("Expected one pagination link for page " + pageNumber);
  await loc.click({});
  for (let i = 0; i < 60; i++) {
    const state = await globalThis.tab.playwright.evaluate(
      () => {
        const clean = (s) => (s || "").replace(/\s+/g, " ").trim();
        const active =
          Array.from(document.querySelectorAll("a.pagination__link.active")).map((a) =>
            clean(a.innerText || a.textContent)
          )[0] || "";
        const first = document.querySelector('input[name="dataViewerSelection"]')?.value || "";
        const results = clean(document.body.innerText || "").match(/\d+ results \d+ - \d+/)?.[0] || "";
        return { active, first, results };
      },
      undefined,
      { timeoutMs: 10000 }
    );
    if (state.active === String(pageNumber) && state.first && state.first !== beforeFirst) return state;
    await globalThis.tab.playwright.waitForTimeout(250);
  }
  throw new Error("Timed out waiting for page " + pageNumber);
};

var firstPage = await globalThis.wwScrapeCurrentPage();
var totalText = await globalThis.tab.playwright.evaluate(
  () => (document.body.innerText || "").match(/(\d+) results/)?.[1] || "",
  undefined,
  { timeoutMs: 10000 }
);
var expectedTotal = Number(totalText || Object.keys(globalThis.wwJobs).length);
var pageCount = Math.ceil(expectedTotal / 50);
var pageResults = [{ page: 1, result: firstPage }];
for (let page = 2; page <= pageCount; page++) {
  const state = await globalThis.wwGoToPage(page);
  const result = await globalThis.wwScrapeCurrentPage();
  pageResults.push({ page, state, result });
}

var fsPromises = await import("node:fs/promises");
await fsPromises.writeFile(tmpPath, JSON.stringify(Object.values(globalThis.wwJobs)), "utf8");
nodeRepl.write(
  JSON.stringify(
    { tmpPath, expectedTotal, scraped: Object.keys(globalThis.wwJobs).length, pageResults },
    null,
    2
  )
);
```

## After Scraping

Run from the project root:

```bash
node .codex/skills/ww-scrape-jobs/scripts/write_jds_from_scrape_json.js --input /private/tmp/waterlooworks-cycle3-scrape.json --out jds/cycle3
node .codex/skills/ww-scrape-jobs/scripts/validate_cycle_folder.js jds/cycle3 --expected 237
```

## Claude-in-Chrome (in-page) variant

The `## Scraper Snippet` above targets a Playwright / Node REPL (`globalThis.tab.playwright`, `nodeRepl.write`, `node:fs`). **Claude in Chrome is different:** its `javascript_tool` runs JavaScript *in the page only* — there is no `tab.playwright`, no `nodeRepl`, and no filesystem. Use this variant instead.

### Filter setup (in-page)

The "My Program" quick filter is a `<button>` whose text includes `My Program toggle_off`. Click it, then confirm `My Program toggle_on`, `filter_list 1`, and a result count like `32 results 1 - 32`. (A synthetic click is fine for this button; only the search keyword field needs real keystrokes — see the apply skill.)

### In-page scrape loop

Drive the same DOM targets as the Playwright snippet, but from `javascript_tool`:

- Rows: `table tbody tr` containing `input[name="dataViewerSelection"]` (the id) and `a.overflow--ellipsis` (the title link). Results may also render as cards (`.doc-viewer__card`) instead of a table — handle both.
- Open a detail: click the row/card title link.
- Detail text: `.modal.is--visible .is--long-form-reading` (`innerText`); treat it as ready only once the modal text also contains the job id.
- Close: dispatch an `Escape` `keydown` on `document.body` and/or click the modal close control; wait until `document.querySelectorAll('.modal.is--visible').length === 0`.
- Paginate: click the `a.pagination__link` for the next page; wait until the active page label changes and the first row id differs from the previous page.

Accumulate into a `window.wwJobs` object keyed by id, and run the modal loop in **batches** (≈8 ids per `javascript_tool` call) so no single call runs too long; progress persists in `window.wwJobs` between calls.

### Exfiltrating the scrape JSON (no filesystem)

In-page JS cannot write `/private/tmp`. Getting the (~100–200 KB) JSON out of Claude in Chrome has sharp edges:

- **Returning base64 is BLOCKED** — the Chrome MCP sanitizer replaces it with `[BLOCKED: Base64 encoded data]`.
- **Returning the raw JSON string is TRUNCATED** at the tool's display limit (a few KB).
- **`navigator.clipboard.writeText` is BLOCKED** without a user gesture.

Working method — **blob download**: build a Blob from the JSON in-page and click a programmatic `<a download>`, which lands the file in the user's Downloads folder; then copy it to the temp path the converter expects.

```js
// in-page (javascript_tool), after the scrape loop:
const json = JSON.stringify(Object.values(window.wwJobs));
const a = document.createElement('a');
a.href = URL.createObjectURL(new Blob([json], { type: 'application/json' }));
a.download = 'waterlooworks-<folder>-scrape.json';
document.body.appendChild(a); a.click();
setTimeout(() => { a.remove(); URL.revokeObjectURL(a.href); }, 3000);
({ triggered: true, len: json.length });
```

```bash
# then, from the shell:
cp ~/Downloads/waterlooworks-<folder>-scrape.json /private/tmp/waterlooworks-<folder>-scrape.json
node -e "const d=require('/private/tmp/waterlooworks-<folder>-scrape.json'); console.log('jobs:', d.length, 'all detailText:', d.every(j=>j.detailText&&j.detailText.length>500));"
```

Then run the converter and validator exactly as in `## After Scraping`, substituting your `<folder>`. Verified working 2026-06-26 (32 "My Program" jobs).
