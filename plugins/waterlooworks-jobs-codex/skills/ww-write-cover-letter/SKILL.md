---
name: ww-write-cover-letter
description: Create a tailored, one-page cover letter PDF named `<Company>-coverletter.pdf` in the `coverletter/` folder, generated from a job description and one of the user's résumés and styled like their sample letter (Times font, centered bold name, address-left/links-right header). Use this whenever the user wants to write, draft, generate, or make a cover letter for a specific job, company, or posting — e.g. "write a cover letter for job 475135", "make a coverletter for the Jaza Energy role using ai.pdf", "draft a cover letter for this JD". This is distinct from `ww-upload-cover-letter`, which only uploads an already-made PDF into WaterlooWorks; this skill GENERATES the PDF (hand the result to `ww-upload-cover-letter` afterward if applying). Header details (name, address, phone, email, LinkedIn, GitHub) live in `coverletter-config.json` in the current folder — if it is missing, ask the user for them and create it before generating.
---

# Generate Cover Letter

## Overview

Produce a one-page, job-specific cover letter PDF that matches the user's reference style: the
name centered and bold at the top, a contact row with the mailing address on the left and links
(LinkedIn, email, etc.) on the right, then "Dear Hiring Manager," three-to-four tailored body
paragraphs, "Sincerely," and the signature name.

The division of labor matters: **you write the tailored prose**, and a bundled script
(`scripts/generate_cover_letter.py`, reportlab) owns the layout and the one-page guarantee. The
script auto-fits the text by stepping down through compact typographic presets, and if the body
is too long to fit on one page even at the smallest readable size it fails loudly instead of
spilling onto a second page — so keep the writing tight and let the script handle the rest.

The output is written to the **`coverletter/`** folder (created automatically) as `<Company>-coverletter.pdf`.

## Inputs

Gather or infer these before generating:

- **Job description** — accept any of: a WaterlooWorks job ID (e.g. `475135`), a path to a JD
  file, JD text pasted into chat, or **JD details already in your context** (a calling skill or
  agent passed the posting facts, or you read the posting earlier this session — no local file
  needed). From it you need the **company/organization name**, the **role title**, the **work
  term** (e.g. "Fall 2026"), and the key **responsibilities/skills** to tailor toward.
- **Résumé** — which of the user's résumés to draw evidence from (`resume/ai.pdf`, `swe.pdf`,
  `frontend.pdf`, `backend.pdf`). If the user names one, use it. If not, check `ranks/shortlist.md`
  in the repo — it maps job IDs to the recommended résumé. If still ambiguous, ask.
- **Header config** — `coverletter-config.json` in the current folder (see Step 0).

## Step 0 — Ensure the header config exists

Look for `coverletter-config.json` in the current working directory.

- **If it exists**, use it as-is.
- **If it is missing**, ask the user for their header details and write the file before
  continuing. Collect: full name; mailing address lines (or confirm none); and which contact
  items to show on the right (LinkedIn, GitHub, email, phone, website) with their URLs. Then write
  the config in this schema:

```json
{
  "name": "Jordan Goose",
  "address_lines": ["200 University Ave W", "Waterloo, ON, Canada, N2L 3G1"],
  "contact_lines": [
    { "text": "LinkedIn", "url": "https://www.linkedin.com/in/your-handle" },
    { "text": "jordan.goose@uwaterloo.ca" }
  ]
}
```

- `name` (required) is centered + bold at the top and reused as the signature.
- `address_lines` fill the **left** of the contact row; use `[]` to omit the address.
- `contact_lines` fill the **right**, top-to-bottom in order; each shows `text`, hyperlinked when
  a `url` is given. This is the "customize your header line" knob — put phone / email / LinkedIn /
  GitHub / website here in any combination. A full example is in
  `assets/coverletter-config.example.json`.

Do not invent header values. If the user says "use my usual details" and the config already
exists, trust it.

## Step 1 — Gather the job facts

- **JD already in your context** (a caller passed the posting facts, or you read it earlier this
  session): use it directly — do **not** go hunting for a local file. Only fall back to a `jds/`
  lookup if the in-context info is missing a fact you need below.
- **Given a job ID** (and it isn't already in context): find the posting with `ls jds/**/"<id>"*`
  or a search for `<id> - *.md` under `jds/`. These files have a table with `Organization`, plus
  `Job Title`, `Work Term`, and responsibilities/requirements sections. Read enough to tailor
  honestly.
- **Given a file path or pasted JD**: read it directly.
- Pull out: company name (for the filename and the letter), role title, work term, and 2-4
  concrete things the role wants (technologies, domain, responsibilities, what the team values).

## Step 2 — Read the résumé

Extract the text so you tailor from real facts, not guesses:

```
pdftotext -layout resume/<chosen>.pdf -
```

Note the user's actual employers, projects, technologies, and outcomes. You will map these to the
job's needs. Never fabricate experience, employers, dates, or metrics that are not on the résumé.

## Step 3 — Draft the body

Write the body as 3-4 short paragraphs (~250-330 words total — this is what keeps it to one
page). Keep them as **paragraphs separated by blank lines** (no greeting, no
"Sincerely", no name — the script adds those). A reliable structure, mirroring the sample:

1. **Hook + who you are.** State excitement for the *exact role title* at the *company* for the
   *work term*, then one line on identity (e.g. "Computer Science student at the University of
   Waterloo") and 2-3 skill areas that match this posting.
2. **Evidence.** One or two concrete experiences/projects from the résumé that directly map to the
   job's needs, with specifics (what was built, the tech, the impact). Use the résumé's real
   wording and facts.
3. **Why this company/role.** Tie your interest to something specific in *this* JD — the product,
   mission, tech stack, team, or domain. This is the paragraph that proves it is not a generic
   letter; make it specific to the posting, not boilerplate.
4. **Close.** Thank them and add a light call to action.

Write naturally and specifically. Avoid clichés ("I am a hard worker", "team player"), filler, and
repeating the résumé verbatim. The tone in the sample is warm, direct, and confident — match it.

Keep the paragraphs blank-line separated — you'll pipe them straight into the generator on stdin in the next step, so there's no temp file to manage.

## Step 4 — Generate the PDF

Run the bundled script from the project root (where `coverletter-config.json` lives; the PDF lands in `coverletter/`, created if missing). The script lives in this skill's own `scripts/` directory — resolve `<skill dir>` to the absolute path shown as "Base directory for this skill:" when this skill loads. (Under a plugin install that is inside the plugin cache; a literal `.codex/skills/…` path is only correct for a local repo checkout, so do not hardcode it.) The body paragraphs go in on stdin via `--body -`:

```bash
python3 "<skill dir>/scripts/generate_cover_letter.py" \
  --config coverletter-config.json \
  --company "Jaza Energy" \
  --body - <<'EOF'
<paragraph 1>

<paragraph 2>

<paragraph 3>

<paragraph 4>
EOF
```

- `--company` drives the default output path: `Jaza Energy Inc` → `coverletter/Jaza-Energy-coverletter.pdf`
  (common legal suffixes like Inc/Ltd/LLC are dropped; the `coverletter/` folder is created if missing). Pass `--out <path>` to override.
- Optional: `--greeting "Dear <name>,"` when you know the hiring manager, `--date "June 23, 2026"`
  to add a date line, `--closing "Best regards,"`.

## Step 5 — Verify

- If the script **exits non-zero** saying the body does not fit, the letter would have run onto a
  second page. Tighten the prose (cut a sentence or two, merge a weak paragraph) and rerun. Do not
  work around the one-page rule.
- On success, confirm the output: it is exactly **one page**, the **filename uses the company
  name**, and the header shows the configured name/address/links. A quick check:
  `pdfinfo <file> | grep -i pages` and `pdftotext -layout <file> -`.
- Report the path of the generated PDF to the user.

## Failure handling

- **No JD found for the given ID** (and none in context): list nearby matches under `jds/` and ask
  the user to confirm the ID or paste the JD.
- **Résumé ambiguous**: if neither the user nor `ranks/shortlist.md` indicates one, ask which résumé to use
  rather than guessing.
- **Config missing required `name`**: stop and collect header details (Step 0).
- **Body too long for one page**: shorten and rerun; never produce a two-page letter.
- **Thin résumé match for a key requirement**: lean on transferable experience honestly; do not
  invent qualifications.
