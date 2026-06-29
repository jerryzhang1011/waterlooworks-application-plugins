#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

function usage() {
  console.error(
    "Usage: node write_jds_from_scrape_json.js --input /path/scrape.json --out jds/cycleN [--replace]"
  );
}

function parseArgs(argv) {
  const args = { replace: false };
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--replace") {
      args.replace = true;
    } else if (arg === "--input" || arg === "--out") {
      args[arg.slice(2)] = argv[++i];
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  if (!args.input || !args.out) {
    usage();
    process.exit(2);
  }
  return args;
}

function escTable(value) {
  return String(value ?? "").replace(/\|/g, "\\|").replace(/\r?\n/g, " ").trim();
}

function sanitizeFilenamePart(text) {
  return String(text || "Untitled")
    .replace(/[\\/]/g, " ")
    .replace(/[\u0000-\u001f\u007f]/g, "")
    .replace(/:/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 180);
}

// Loop-invariant lookup tables, shared across all jobs (built once, not per call).
const SECTION_LABELS = new Map([
  ["JOB POSTING INFORMATION", "Job Posting Information"],
  ["APPLICATION INFORMATION", "Application Information"],
  ["COMPANY INFORMATION", "Company Information"],
  ["SERVICE TEAM", "Service Team"],
]);
const SUB_HEADINGS = new Set([
  "Job Summary:",
  "Job Responsibilities:",
  "Required Skills:",
  "Compensation and Benefits:",
  "Targeted Degrees and Disciplines:",
]);
const DROP_LINES = new Set([
  "View Targeted Degrees and Disciplines",
  "create_new_folder",
  "do_not_disturb",
  "playlist_add",
  "print",
  "close",
]);

function formatDetailText(text) {
  const out = [];
  const lines = String(text || "")
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => line.trimEnd());

  for (const line of lines) {
    const trimmed = line.trim();
    if (DROP_LINES.has(trimmed)) continue;
    if (SECTION_LABELS.has(trimmed)) {
      if (out.length && out[out.length - 1] !== "") out.push("");
      out.push(`## ${SECTION_LABELS.get(trimmed)}`);
      out.push("");
    } else if (SUB_HEADINGS.has(trimmed)) {
      if (out.length && out[out.length - 1] !== "") out.push("");
      out.push(`## ${trimmed.replace(/:$/, "")}`);
      out.push("");
    } else {
      out.push(line);
    }
  }

  while (out.length && out[0] === "") out.shift();
  while (out.length && out[out.length - 1] === "") out.pop();
  return out.join("\n").replace(/\n{3,}/g, "\n\n");
}

function markdownForJob(job) {
  const title = job.title || "Untitled";
  const tableRows = [
    ["ID", job.id],
    ["Organization", job.organization],
    ["Division", job.division],
    ["Openings", job.openings],
    ["City", job.city],
    ["Level", job.level],
    ["Apps", job.apps],
    ["App Deadline", job.appDeadline],
  ];
  const table = [
    "| Field | Value |",
    "| --- | --- |",
    ...tableRows.map(([key, value]) => `| ${key} | ${escTable(value)} |`),
  ].join("\n");
  return `# ${title}\n\n${table}\n\n${formatDetailText(job.detailText)}\n`;
}

function main() {
  const args = parseArgs(process.argv);
  const jobs = JSON.parse(fs.readFileSync(args.input, "utf8"));
  if (!Array.isArray(jobs)) throw new Error("Input JSON must be an array of job objects");
  fs.mkdirSync(args.out, { recursive: true });

  if (args.replace) {
    for (const name of fs.readdirSync(args.out)) {
      if (name.endsWith(".md")) fs.unlinkSync(path.join(args.out, name));
    }
  }

  const sorted = [...jobs].sort((a, b) => Number(b.id) - Number(a.id));
  for (const job of sorted) {
    if (!job.id || !job.title || !job.detailText) {
      const ref = [job.id, job.title].filter(Boolean).join(" - ") || "(no id/title)";
      throw new Error(`Missing required field (id/title/detailText) for job: ${ref}`);
    }
    const filename = `${job.id} - ${sanitizeFilenamePart(job.title)}.md`;
    fs.writeFileSync(path.join(args.out, filename), markdownForJob(job), "utf8");
  }

  console.log(
    JSON.stringify(
      {
        outDir: path.resolve(args.out),
        written: sorted.length,
        first: sorted[0] ? `${sorted[0].id} - ${sanitizeFilenamePart(sorted[0].title)}.md` : null,
        last: sorted.at(-1)
          ? `${sorted.at(-1).id} - ${sanitizeFilenamePart(sorted.at(-1).title)}.md`
          : null,
      },
      null,
      2
    )
  );
}

main();
