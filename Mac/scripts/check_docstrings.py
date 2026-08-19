"""scripts/check_docstrings.py — Check API for missing docstrings.

Scans the backend module and flags exported functions/classes
missing docstrings.
"""
import inspect
import sys
import backend as be

def main():
    print("Checking backend for missing docstrings...")
    missing = []
    
    # Check all exported items
    for name in dir(be):
        if name.startswith("_"):
            continue
        obj = getattr(be, name)
        if inspect.isfunction(obj) or inspect.isclass(obj):
            if not obj.__doc__:
                missing.append(name)
                
    if missing:
        print("MISSING DOCSTRINGS FOUND:", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        sys.exit(1)
        
    print("All exported functions and classes have docstrings.")
    sys.exit(0)

if __name__ == "__main__":
    main()
