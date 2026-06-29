# Chrome Scrape Workflow

Use this reference after loading the Chrome control skill and opening:

`https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm`

## Current UI selectors (verified 2026-06-28) — READ FIRST

The WaterlooWorks UI changed. The older Playwright snippet below uses several **stale** selectors. Use these current ones everywhere (both the Playwright snippet and the in-page variant):

| Purpose | STALE (do not trust) | CURRENT (verified 2026-06-28) |
| --- | --- | --- |
| Result rows | `table tbody tr` | Default "card" view: `<li>` under `.doc-viewer__results`, each containing `input[name="dataViewerSelection"]` (the id) + an `<a>` title link. A `table`/`tr` layout only appears in the alternate "table" view. Handle BOTH: iterate `input[name="dataViewerSelection"]` and take `inp.closest('li') || inp.closest('tr')`. |
| Title link | `a.overflow--ellipsis` | Any `<a>` inside the row with non-trivial text (the class is gone/obfuscated). |
| Job detail container | `.modal.is--visible` | `.is--long-form-reading` (a full-page reading panel; there is **no** `.modal.is--visible`). |
| Detail "ready" check | modal text contains the job id | The detail panel does **NOT** contain the numeric job id. Treat ready when `.is--long-form-reading` exists, its `innerText` length > 500, includes `Job Title:`, AND includes the first ~15 chars of the expected row title. |
| Close the detail | Escape / `.modal__close` | Click the `arrow_back` button (a `<button>` whose visible text is `arrow_back`); Escape does nothing. Wait until `.is--long-form-reading` is gone. |
| Next page | `a.pagination__link` | Card view: `.doc-viewer__pagination__btn--next` (note: that class is shared by unrelated `edit`/`more_vert` buttons — pick the one with text `navigate_next`). Numbered `a.pagination__link` links exist ONLY in the table view. |
| Browse detail→detail | (n/a) | While a detail is open, a `navigate_next` / `navigate_before` button pages through postings WITHOUT returning to the list — far faster than close+reopen per row. Unreliable on a short last page; fall back to opening each remaining row. |

⚠️ **Filter reset:** when using the `My Program` quick filter, opening AND closing a posting can silently turn it OFF (result count jumps e.g. 55 → 149). See `## Page Setup` step 5.

⚠️ **45s call limit (in-page):** `javascript_tool` calls are killed at ~45s ("renderer may be frozen"). Never run a single-shot loop over all rows. Batch ≈8 detail reads per call; progress persists in `window.wwJobs` between calls. See the in-page variant.

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
5. **The `My Program` filter can reset when you open/close a posting.** If using that default filter, after navigating through detail panels (or paginating), re-read the chip/count and re-toggle `My Program` before reading any later page. Defensively, capture the filtered id→title list FIRST (one pass over the rows, no detail opens), then verify every scraped detail's title against that list so an accidentally-unfiltered page can never inject wrong jobs.

## Scraper Snippet (Playwright / Node REPL)

Run this in the Chrome plugin Node REPL after `globalThis.tab` points at the filtered WaterlooWorks tab. Change `cycleNumber` before running. **This snippet requires `globalThis.tab.playwright`, `nodeRepl`, and `node:fs`** — i.e. a Codex/Playwright-style REPL. If you are using Claude in Chrome (the in-page `javascript_tool`), skip this and use the `## Claude-in-Chrome (in-page) variant` section below.

> ⚠️ **This snippet's selectors are STALE** (see `## Current UI selectors` above). Before running it, swap in the current selectors: rows = `<li>` under `.doc-viewer__results` via `input[name="dataViewerSelection"]` (not `table tbody tr`); detail = `.is--long-form-reading` (not `.modal.is--visible`); readiness = title-match, not job-id-in-modal; close = click the `arrow_back` button (not Escape); pagination = `.doc-viewer__pagination__btn--next` in card view (not `a.pagination__link`). Also re-apply the `My Program` filter after each page when using that default filter (opening/closing a posting clears it). The structure below is still useful, but it will scrape 0 rows as written.

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
node .claude/skills/ww-scrape-jobs/scripts/write_jds_from_scrape_json.js --input /private/tmp/waterlooworks-cycle3-scrape.json --out jds/cycle3
node .claude/skills/ww-scrape-jobs/scripts/validate_cycle_folder.js jds/cycle3 --expected 237
```

## Claude-in-Chrome (in-page) variant

The `## Scraper Snippet` above targets a Playwright / Node REPL (`globalThis.tab.playwright`, `nodeRepl.write`, `node:fs`). **Claude in Chrome is different:** its `javascript_tool` runs JavaScript *in the page only* — there is no `tab.playwright`, no `nodeRepl`, and no filesystem. Use this variant instead.

### Filter setup (in-page)

The "My Program" quick filter is a `<button>` whose text includes `My Program toggle_off`. Click it, then confirm `My Program toggle_on`, `filter_list 1`, and a result count like `32 results 1 - 32`. (A synthetic click is fine for this button; only the search keyword field needs real keystrokes — see the apply skill.)

⚠️ **The filter does not stick across detail opens.** Opening then closing a posting reverts `My Program` to OFF and the count jumps back to the full list (e.g. 55 → 149). Re-toggle it whenever you return to the list to read a new page, and always confirm the count is the filtered number before extracting rows.

### In-page scrape loop

Use the CURRENT selectors (see `## Current UI selectors`), not the Playwright snippet's. Verified-working approach (2026-06-28, 55 "My Program" jobs):

1. **Build the id→title map first** (one pass, no detail opens). Iterate `input[name="dataViewerSelection"]`; for each take `inp.closest('li')` and the first `<a>` with text > 3 chars. Store `{id, title}` in order. This map (a) drives title-match readiness and (b) lets you verify every detail belongs to a filtered row even if the filter silently dropped.
2. **Open detail by clicking the row's title `<a>`.** Detail loads into `.is--long-form-reading` (~0.5s). Ready when its `innerText` length > 500, includes `Job Title:`, and includes the first ~15 chars of the expected title.
3. **Browse forward with `navigate_next`** instead of close+reopen: click the visible `<button>` with text `navigate_next`, wait ~0.4s, then read the next detail. This avoids the slow list re-render and the filter reset. (On a short last page `navigate_next` may not advance / may vanish — fall back to closing via `arrow_back` and opening each remaining row individually, re-applying the filter each time.)
4. **Close** when needed by clicking the `arrow_back` button; wait until `.is--long-form-reading` is gone. Escape does NOT close it.
5. **Paginate** by re-applying the `My Program` filter (it reset), then clicking `.doc-viewer__pagination__btn--next` (card view) — or the numbered `a.pagination__link` if the view flipped to a table.

**Batch the work:** a single `javascript_tool` call dies at ~45s. Do ≈8 detail reads per call; accumulate into `window.wwJobs` keyed by id (persists between calls). Define the helpers once in `window`, then call them in chunks. Skeleton:

```js
// define once (one call):
(() => {
  const clean = s => (s||'').replace(/\s+/g,' ').trim();
  window.wwJobs = window.wwJobs || {};
  window.wwListMap = window.wwExtractRows = () => Array.from(document.querySelectorAll('input[name="dataViewerSelection"]')).map(inp => {
    const row = inp.closest('li') || inp.closest('tr'); if (!row || !/^\d+$/.test(inp.value)) return null;
    const a = Array.from(row.querySelectorAll('a')).find(x => clean(x.innerText).length > 3);
    return { id: inp.value, title: a ? clean(a.innerText) : '' };
  }).filter(Boolean);
  window.wwGetDetail = () => document.querySelector('.is--long-form-reading')?.innerText || '';
  window.wwReady = (title) => { const t = window.wwGetDetail(); return t.length>500 && t.includes('Job Title:') && clean(t).includes(clean(title).slice(0,15)); };
  window.wwNext = () => { const b = Array.from(document.querySelectorAll('button')).find(x=>{const r=x.getBoundingClientRect();return r.width>0&&r.height>0&&/navigate_next/i.test((x.innerText||'').trim());}); if (b) b.click(); return !!b; };
  window.wwClose = async () => { for (let k=0;k<8;k++){ if(!document.querySelector('.is--long-form-reading')) return true; const b=Array.from(document.querySelectorAll('button')).find(x=>{const r=x.getBoundingClientRect();return r.width>0&&r.height>0&&/arrow_back/i.test((x.innerText||'').trim());}); if(b)b.click(); await new Promise(r=>setTimeout(r,300)); } return !document.querySelector('.is--long-form-reading'); };
  return { rows: window.wwExtractRows().length };
})();
// then per chunk: open the start row's <a>, wait for wwReady(map[i].title), store window.wwGetDetail(),
// then for ~8 items click window.wwNext() / wait wwReady / store, mapping each to wwListMap[i].id.
```

Then exfiltrate `window.wwJobs` via the blob download below.

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
