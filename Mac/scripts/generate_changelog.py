"""scripts/generate_changelog.py — Automate changelog generation.

Generates a draft changelog from git history since the last tag.
"""
import subprocess
import sys
from datetime import datetime

def main():
    try:
        # Get the latest tag
        latest_tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], text=True).strip()
    except Exception:
        latest_tag = None
        
    log_cmd = ["git", "log", "--pretty=format:- %s (%h)"]
    if latest_tag:
        log_cmd.append(f"{latest_tag}..HEAD")
        print(f"Generating changelog since {latest_tag}...")
    else:
        print("No tags found. Generating full changelog...")
        
    try:
        log_output = subprocess.check_output(log_cmd, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to get git log: {e}", file=sys.stderr)
        sys.exit(1)
        
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n## [Unreleased] - {today}")
    if log_output:
        print(log_output)
    else:
        print("- No changes since last release.")

if __name__ == "__main__":
    main()
