#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = os.environ.get("PROFILE_OWNER", "DiwasKhatri07")
WORK = Path("/tmp/profile-repos")
WORK.mkdir(parents=True, exist_ok=True)

skip_dirs = {".git", "node_modules", "dist", "build", "coverage", "vendor", "decoded", "__pycache__", ".next", "target"}
code_exts = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts", ".go", ".rs", ".c", ".h", ".cpp", ".cc", ".cs", ".php", ".rb", ".swift", ".dart", ".html", ".css", ".scss", ".sass", ".sql", ".sh", ".ps1", ".vue", ".astro", ".xml", ".json", ".yaml", ".yml"}

repos = subprocess.check_output(["gh", "api", "--paginate", f"users/{OWNER}/repos?per_page=100", "--jq", ".[] | select(.fork==false and .archived==false) | .clone_url"], text=True).splitlines()
total = 0
files = 0
for url in repos:
    name = url.rsplit("/", 1)[-1].removesuffix(".git")
    destination = WORK / name
    if not destination.exists():
        subprocess.run(["git", "clone", "--depth", "1", "--quiet", url, str(destination)], check=False)
    for current, dirs, filenames in os.walk(destination):
        dirs[:] = [directory for directory in dirs if directory not in skip_dirs]
        for filename in filenames:
            path = Path(current) / filename
            if path.suffix.lower() not in code_exts:
                continue
            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue
            total += sum(1 for line in text.splitlines() if line.strip())
            files += 1
print(total)
print(f"counted {total:,} non-blank code lines across {files:,} files", file=__import__("sys").stderr)
