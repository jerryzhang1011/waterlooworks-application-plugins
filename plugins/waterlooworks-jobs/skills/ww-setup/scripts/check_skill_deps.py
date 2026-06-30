#!/usr/bin/env python3
"""Detect and check the tool dependencies used by the skills under a skills root.

This script does the deterministic part of the ww-setup skill: it walks the
skills tree, figures out what external tools each skill actually needs (language
runtimes, third-party Python/npm packages, and MCP servers), checks whether each is
installed, and classifies every *missing* dependency so the caller knows how to act:

  - "light"  : safe to auto-install via a user-level package manager (e.g. pip).
  - "heavy"  : needs a system/Homebrew/sudo install -> confirm with the user first.
  - "user"   : can't be installed from the CLI at all (e.g. an MCP server) -> ask the user.

It only DETECTS and REPORTS. Installing is left to the caller so the install policy
(auto light / confirm heavy / hand off user) stays in one place. Output is a human
table by default, or machine-readable JSON with --json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

# --- knowledge the detector needs -------------------------------------------------

# Node core modules (a require() of one of these needs no install). Not exhaustive,
# but covers everything the skills here use plus the common ones.
NODE_BUILTINS = {
    "assert", "buffer", "child_process", "cluster", "console", "crypto", "dgram",
    "dns", "events", "fs", "http", "http2", "https", "net", "os", "path",
    "process", "punycode", "querystring", "readline", "stream", "string_decoder",
    "timers", "tls", "tty", "url", "util", "v8", "vm", "zlib",
}

# External command-line tools a skill may shell out to (in docs or via subprocess).
# These aren't language imports, so the import scan misses them. We only look for
# *distinctive, separately-installable* tools — names unlikely to appear as ordinary
# prose — so a plain mention is a reliable signal. Ubiquitous POSIX tools (base64, tr,
# sed, awk, curl, grep...) are deliberately omitted: they're effectively always present,
# so flagging them is noise. binary -> (package, install hint).
CLI_TOOLS = {
    "pdftotext": ("poppler", "brew install poppler"),
    "pdfinfo": ("poppler", "brew install poppler"),
}

# Signal in markdown that a skill depends on a browser connector we cannot install
# from the CLI: a name, a regex to match in the docs, and a setup hint for the user.
MCP_NAME = "Claude in Chrome (MCP browser automation)"
MCP_RE = re.compile(r"claude\s+in\s+chrome|mcp__claude_in_chrome|logged-in chrome session", re.I)
MCP_HINT = (
    "Connect the Claude in Chrome MCP server (install the Chrome extension and "
    "enable the connector), then make sure Chrome is open and logged in."
)


def stdlib_names() -> set[str]:
    return set(sys.stdlib_module_names) | {"__future__"}


# Directories that hold scaffolding/examples/build output rather than a skill's real
# runtime code. Walking into these would invent phantom dependencies — e.g. a package
# only an eval fixture imports, or one vendored under node_modules — so prune them. The
# pruning never applies to the root itself, so pointing --root straight at one of these
# (e.g. a fixtures dir during testing) still works.
IGNORE_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build",
    "evals", "fixtures",
}


def _ignored_dir(name: str) -> bool:
    return name in IGNORE_DIRS or name.endswith("-workspace")


def iter_files(root: str, exts: tuple[str, ...]):
    for dirpath, dirs, files in os.walk(root):
        # prune in place so os.walk doesn't descend into ignored subtrees
        dirs[:] = [d for d in dirs if not _ignored_dir(d)]
        for fn in files:
            if fn.endswith(exts):
                yield os.path.join(dirpath, fn)


def read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def skill_name_for(path: str, root: str) -> str:
    """Best-effort: the skill folder name is the path component right under root."""
    rel = os.path.relpath(path, root)
    parts = rel.split(os.sep)
    return parts[0] if parts and parts[0] != ".." else os.path.basename(os.path.dirname(path))


# --- detection --------------------------------------------------------------------

_PY_IMPORT_RE = re.compile(r"^\s*(?:from\s+([A-Za-z0-9_]+)|import\s+([A-Za-z0-9_]+(?:\s*,\s*[A-Za-z0-9_]+)*))", re.M)
_JS_REQUIRE_RE = re.compile(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)")
_SHEBANG_RE = re.compile(r"^#!.*?\b(python3|python|node)\b")


def detect(root: str):
    stdlib = stdlib_names()

    # Don't analyze the analyzer: this skill's own files enumerate tool / MCP names as
    # detection *data*, which would otherwise register as phantom dependencies of this
    # skill. Skip its directory when scanning a broader root that merely contains it.
    # But if the user points --root *inside* this skill (e.g. at the eval fixtures),
    # honor that and scan normally.
    self_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
    root_real = os.path.realpath(root)
    scanning_self = root_real == self_dir or root_real.startswith(self_dir + os.sep)

    def keep(path: str) -> bool:
        return scanning_self or not os.path.realpath(path).startswith(self_dir + os.sep)

    py_files = [p for p in iter_files(root, (".py",)) if keep(p)]
    js_files = [p for p in iter_files(root, (".js", ".mjs", ".cjs")) if keep(p)]
    md_files = [p for p in iter_files(root, (".md",)) if keep(p)]
    sh_files = [p for p in iter_files(root, (".sh",)) if keep(p)]

    # local module names = basenames of py/js files (these are intra-skill imports, not deps)
    local_modules = {os.path.splitext(os.path.basename(p))[0] for p in py_files + js_files}

    runtimes: dict[str, set[str]] = {}      # name -> {skills}
    pip_pkgs: dict[str, set[str]] = {}      # import-name -> {skills}
    npm_pkgs: dict[str, set[str]] = {}      # pkg -> {skills}

    def need_runtime(name: str, skill: str):
        runtimes.setdefault(name, set()).add(skill)

    for path in py_files:
        skill = skill_name_for(path, root)
        need_runtime("python3", skill)
        src = read(path)
        m = _SHEBANG_RE.match(src)
        if m and m.group(1) in ("python", "python3"):
            need_runtime("python3", skill)
        for from_mod, import_mods in _PY_IMPORT_RE.findall(src):
            mods = [from_mod] if from_mod else [x.strip() for x in import_mods.split(",")]
            for mod in mods:
                top = mod.split(".")[0]
                if not top or top in stdlib or top in local_modules:
                    continue
                pip_pkgs.setdefault(top, set()).add(skill)

    for path in js_files:
        skill = skill_name_for(path, root)
        need_runtime("node", skill)
        src = read(path)
        m = _SHEBANG_RE.match(src)
        if m and m.group(1) == "node":
            need_runtime("node", skill)
        for mod in _JS_REQUIRE_RE.findall(src):
            if mod.startswith(".") or mod.startswith("/"):
                continue  # relative import
            top = mod.split("/")[0]
            if top.startswith("@"):  # scoped pkg @scope/name
                top = "/".join(mod.split("/")[:2])
            base = top[1:] if top.startswith("@") else top.split("/")[0]
            if base in NODE_BUILTINS:
                continue
            npm_pkgs.setdefault(top, set()).add(skill)

    mcp: dict[str, tuple[set[str], str]] = {}
    for path in md_files:
        if MCP_RE.search(read(path)):
            mcp.setdefault(MCP_NAME, (set(), MCP_HINT))[0].add(skill_name_for(path, root))

    # CLI tools: scan all text the skill ships (docs + scripts) for distinctive tool names.
    cli: dict[str, set[str]] = {}   # binary -> {skills}
    tool_res = {tool: re.compile(r"(?<![\w-])" + re.escape(tool) + r"(?![\w-])") for tool in CLI_TOOLS}
    for path in py_files + js_files + md_files + sh_files:
        skill = skill_name_for(path, root)
        src = read(path)
        for tool, rx in tool_res.items():
            if rx.search(src):
                cli.setdefault(tool, set()).add(skill)

    return runtimes, pip_pkgs, npm_pkgs, mcp, cli


# --- availability checks ----------------------------------------------------------

def runtime_version(name: str) -> str | None:
    exe = shutil.which(name)
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=15)
        return (out.stdout or out.stderr).strip() or "installed"
    except Exception:
        return "installed"


def py_module_present(import_name: str) -> bool:
    py = shutil.which("python3") or shutil.which("python")
    if not py:
        return False
    try:
        r = subprocess.run(
            [py, "-c", f"import importlib.util,sys; sys.exit(0 if importlib.util.find_spec({import_name!r}) else 1)"],
            capture_output=True, timeout=20,
        )
        return r.returncode == 0
    except Exception:
        return False


def npm_module_present(pkg: str) -> bool:
    node = shutil.which("node")
    if not node:
        return False
    try:
        r = subprocess.run(
            [node, "-e", f"require.resolve('{pkg}')"], capture_output=True, timeout=20
        )
        return r.returncode == 0
    except Exception:
        return False


# --- report -----------------------------------------------------------------------

def build_report(root: str):
    runtimes, pip_pkgs, npm_pkgs, mcp, cli = detect(root)

    report = {"root": root, "runtimes": [], "pip_packages": [], "npm_packages": [], "cli_tools": [], "mcp": []}

    for name in sorted(runtimes):
        ver = runtime_version(name)
        report["runtimes"].append({
            "name": name,
            "required_by": sorted(runtimes[name]),
            "installed": ver is not None,
            "version": ver,
            # a missing runtime is a system install -> heavy (confirm first)
            "class": None if ver is not None else "heavy",
            "install_cmd": None if ver is not None else f"brew install {name.replace('python3', 'python')}",
        })

    py_ok = shutil.which("python3") or shutil.which("python")
    for imp in sorted(pip_pkgs):
        present = py_module_present(imp) if py_ok else False
        install = imp
        report["pip_packages"].append({
            "import": imp,
            "install": install,
            "required_by": sorted(pip_pkgs[imp]),
            "installed": present,
            "class": None if present else "light",
            "install_cmd": None if present else f"python3 -m pip install {install}",
        })

    node_ok = shutil.which("node")
    for pkg in sorted(npm_pkgs):
        present = npm_module_present(pkg) if node_ok else False
        report["npm_packages"].append({
            "package": pkg,
            "required_by": sorted(npm_pkgs[pkg]),
            "installed": present,
            # global npm install is a system-ish change -> confirm first
            "class": None if present else "heavy",
            "install_cmd": None if present else f"npm install -g {pkg}",
        })

    for tool in sorted(cli):
        package, install = CLI_TOOLS[tool]
        present = shutil.which(tool) is not None
        report["cli_tools"].append({
            "name": tool,
            "package": package,
            "required_by": sorted(cli[tool]),
            "installed": present,
            # a missing CLI tool is a system/Homebrew install -> heavy (confirm first)
            "class": None if present else "heavy",
            "install_cmd": None if present else install,
        })

    for name, (skills, hint) in sorted(mcp.items()):
        report["mcp"].append({
            "name": name,
            "required_by": sorted(skills),
            "installed": None,        # not CLI-checkable from here
            "class": "user",
            "note": hint,
        })

    missing_light = [d for d in report["pip_packages"] if not d["installed"]]
    missing_heavy = [d for d in report["runtimes"] + report["npm_packages"] + report["cli_tools"] if not d["installed"]]
    needs_user = report["mcp"]
    report["summary"] = {
        "missing_light": len(missing_light),
        "missing_heavy": len(missing_heavy),
        "needs_user": len(needs_user),
        "all_cli_ok": len(missing_light) == 0 and len(missing_heavy) == 0,
    }
    return report


def print_human(report: dict):
    def mark(ok):
        return "OK " if ok else "MISSING"

    print(f"Skill dependency check for: {report['root']}\n")

    print("Runtimes:")
    for d in report["runtimes"]:
        ver = f" ({d['version']})" if d["installed"] else ""
        print(f"  [{mark(d['installed'])}] {d['name']}{ver}  <- {', '.join(d['required_by'])}")
        if not d["installed"]:
            print(f"            confirm-then-run: {d['install_cmd']}")
    if not report["runtimes"]:
        print("  (none)")

    print("\nPython packages (pip):")
    for d in report["pip_packages"]:
        print(f"  [{mark(d['installed'])}] {d['import']} (pip: {d['install']})  <- {', '.join(d['required_by'])}")
        if not d["installed"]:
            print(f"            auto-install: {d['install_cmd']}")
    if not report["pip_packages"]:
        print("  (none)")

    print("\nNode packages (npm):")
    for d in report["npm_packages"]:
        print(f"  [{mark(d['installed'])}] {d['package']}  <- {', '.join(d['required_by'])}")
        if not d["installed"]:
            print(f"            confirm-then-run: {d['install_cmd']}")
    if not report["npm_packages"]:
        print("  (none — scripts use only Node built-ins)")

    print("\nCLI tools (shelled out to by the skills):")
    for d in report["cli_tools"]:
        pkg = f" (pkg: {d['package']})" if d["package"] != d["name"] else ""
        print(f"  [{mark(d['installed'])}] {d['name']}{pkg}  <- {', '.join(d['required_by'])}")
        if not d["installed"]:
            print(f"            confirm-then-run: {d['install_cmd']}")
    if not report["cli_tools"]:
        print("  (none)")

    print("\nMCP / external (cannot install from CLI — ask the user):")
    for d in report["mcp"]:
        print(f"  [USER] {d['name']}  <- {', '.join(d['required_by'])}")
        print(f"            {d['note']}")
    if not report["mcp"]:
        print("  (none)")

    s = report["summary"]
    print(
        f"\nSummary: {s['missing_light']} auto-installable, {s['missing_heavy']} need confirmation, "
        f"{s['needs_user']} need the user. "
        + ("All CLI deps satisfied." if s["all_cli_ok"] else "Action required.")
    )


def main():
    ap = argparse.ArgumentParser(description="Detect and check tool dependencies used by skills.")
    ap.add_argument("--root", default=".claude/skills", help="skills root to scan (default: .claude/skills)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of a table")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print(f"error: skills root not found: {args.root}", file=sys.stderr)
        sys.exit(2)

    report = build_report(args.root)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human(report)
    # exit 0 if all CLI deps satisfied (MCP/user deps don't fail the check), else 1
    sys.exit(0 if report["summary"]["all_cli_ok"] else 1)


if __name__ == "__main__":
    main()
