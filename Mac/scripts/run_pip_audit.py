"""scripts/run_pip_audit.py — Security vulnerability scanning script.

Runs pip-audit on the environment or requirements.txt.
"""
import subprocess
import sys

def main():
    print("Running pip-audit...")
    try:
        import pip_audit  # noqa
    except ImportError:
        print("pip-audit not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pip-audit"], check=True)

    result = subprocess.run(
        [sys.executable, "-m", "pip_audit", "-r", "requirements.txt"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if result.returncode != 0:
        print("pip-audit found vulnerabilities!", file=sys.stderr)
        sys.exit(1)
    else:
        print("pip-audit found no vulnerabilities.")
        sys.exit(0)

if __name__ == "__main__":
    main()
