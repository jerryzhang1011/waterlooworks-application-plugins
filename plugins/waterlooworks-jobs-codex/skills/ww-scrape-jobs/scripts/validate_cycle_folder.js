#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const folder = process.argv[2];
const expectedIndex = process.argv.indexOf("--expected");
const expected =
  expectedIndex >= 0 && process.argv[expectedIndex + 1]
    ? Number(process.argv[expectedIndex + 1])
    : null;

if (!folder) {
  console.error("Usage: node validate_cycle_folder.js jds/cycleN [--expected 237]");
  process.exit(2);
}

const files = fs
  .readdirSync(folder)
  .filter((name) => name.endsWith(".md"))
  .sort();

const issues = [];
if (expected !== null && files.length !== expected) {
  issues.push(`Expected ${expected} markdown files, found ${files.length}`);
}

for (const name of files) {
  const fullPath = path.join(folder, name);
  const text = fs.readFileSync(fullPath, "utf8");
  if (!/^# .+/m.test(text)) issues.push(`${name}: missing title`);
  for (const required of [
    "| Field | Value |",
    "| ID |",
    "## Job Posting Information",
    "## Application Information",
    "## Company Information",
  ]) {
    if (!text.includes(required)) issues.push(`${name}: missing ${required}`);
  }
  if (/\n{3,}/.test(text)) issues.push(`${name}: contains triple blank lines`);
}

const result = {
  folder: path.resolve(folder),
  files: files.length,
  first: files[0] || null,
  last: files.at(-1) || null,
  issues,
};

console.log(JSON.stringify(result, null, 2));
if (issues.length) process.exit(1);
