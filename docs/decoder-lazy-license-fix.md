# qector-decoder-v3: make the `cryptography` license dependency lazy

**Applies to the SEPARATE `qector-decoder-v3` package, not this repo.**

## Why this matters

`qector-decoder-v3` 0.6.8 introduced an **import-time hard dependency** on `cryptography`:

- `qector_decoder_v3/__init__.py` (~line 130) runs `from .license import verify_license_token` unconditionally at package import.
- `qector_decoder_v3/license.py` (line 4) runs `from cryptography.hazmat.primitives import serialization` at module import.

So merely doing `import qector_decoder_v3` raises `ModuleNotFoundError: No module named 'cryptography'` whenever `cryptography` isn't present.

This is fatal for the QECTOR Workbench, which:
- provisions the decoder wheel with `pip install --no-deps` (so `cryptography` is *not* pulled in), and
- runs frozen (PyInstaller), where only explicitly-bundled packages exist.

Result: every fresh install bricked on boot (Windows **and** Linux). An import-time hard dep on an *optional* feature (license verification) is the root cause. The fix: import `cryptography` **only when license verification is actually called**, and never let a missing optional dep break `import qector_decoder_v3`.

The Workbench side is already hardened (bundles `cryptography`, verifies wheels in the real runtime, self-heals to the last importable version), but the durable fix belongs upstream so any consumer — `--no-deps`, frozen, minimal env — can import the decoder unconditionally.

---

## Patch 1 — `qector_decoder_v3/license.py`: import `cryptography` on call, not on import

```diff
--- a/qector_decoder_v3/license.py
+++ b/qector_decoder_v3/license.py
@@ -1,7 +1,4 @@
-from cryptography.hazmat.primitives import serialization
-
-
-def verify_license_token(token, *args, **kwargs):
+def verify_license_token(token, *args, **kwargs):
+    # Import cryptography lazily: license verification is an optional feature, so
+    # a missing `cryptography` must never break `import qector_decoder_v3`
+    # (consumers install the wheel with --no-deps / run frozen without it).
+    try:
+        from cryptography.hazmat.primitives import serialization
+    except ImportError as exc:  # pragma: no cover - depends on install extras
+        raise RuntimeError(
+            "License verification requires the 'cryptography' package. "
+            "Install it with:  pip install qector-decoder-v3[license]  "
+            "(or:  pip install cryptography)."
+        ) from exc
+
     ...  # existing body unchanged; `serialization` is now a local name
```

> Move **every** top-level `cryptography.*` import in `license.py` inside the function(s) that use them (same `try/except ImportError` guard). If several functions need it, factor a small helper:
>
> ```python
> def _load_serialization():
>     try:
>         from cryptography.hazmat.primitives import serialization
>         return serialization
>     except ImportError as exc:
>         raise RuntimeError(
>             "License verification requires 'cryptography' "
>             "(pip install qector-decoder-v3[license])."
>         ) from exc
> ```
> and call `serialization = _load_serialization()` at the top of each function.

---

## Patch 2 — `qector_decoder_v3/__init__.py`: never let the license import kill package import

```diff
--- a/qector_decoder_v3/__init__.py
+++ b/qector_decoder_v3/__init__.py
@@ -127,7 +127,16 @@
-from .license import verify_license_token
+# License verification is optional; importing it must never break
+# `import qector_decoder_v3`. `license.py` no longer imports cryptography at
+# module load, but stay defensive so any future heavy import there still
+# degrades gracefully instead of bricking every consumer.
+try:
+    from .license import verify_license_token
+except Exception:  # pragma: no cover - optional feature
+    def verify_license_token(*args, **kwargs):
+        raise RuntimeError(
+            "License verification is unavailable in this environment "
+            "(install extras:  pip install qector-decoder-v3[license])."
+        )
```

Also make sure `verify_license_token` stays exported if it's in `__all__` (it now always exists — real function or stub).

---

## Patch 3 — `pyproject.toml`: declare cryptography (as an extra + a soft default)

Make license verification installable via an extra, and keep a normal-install default so `pip install qector-decoder-v3` (without `--no-deps`) still pulls it:

```diff
--- a/pyproject.toml
+++ b/pyproject.toml
@@ [project]
 dependencies = [
     "numpy>=1.24",
+    "cryptography>=41.0",
 ]
+
+[project.optional-dependencies]
+license = ["cryptography>=41.0"]
```

> If you prefer cryptography to be *strictly* optional (not installed by default), drop it from `dependencies` and keep only the `[project.optional-dependencies] license` extra. Either way, Patches 1 & 2 guarantee `import qector_decoder_v3` succeeds without it.

---

## Apply & test

```bash
# in the qector-decoder-v3 repo
git switch -c fix/lazy-license-crypto
# apply Patches 1–3 (adjust line numbers to the real files)

# 1. import must succeed with cryptography ABSENT
python -m venv /tmp/nocrypto && /tmp/nocrypto/bin/pip install -e . --no-deps
/tmp/nocrypto/bin/pip install numpy         # decoder's real runtime dep only
/tmp/nocrypto/bin/python -c "import qector_decoder_v3 as q; print('import OK', q.__version__)"
#   -> prints "import OK 0.6.9"  (previously: ModuleNotFoundError: cryptography)

# 2. calling the optional feature without cryptography fails LOUDLY, not on import
/tmp/nocrypto/bin/python -c "import qector_decoder_v3 as q; q.verify_license_token('x')"
#   -> RuntimeError: License verification requires 'cryptography' ...

# 3. with the extra installed, it works
/tmp/nocrypto/bin/pip install 'cryptography>=41.0'
/tmp/nocrypto/bin/python -c "import qector_decoder_v3 as q; print(callable(q.verify_license_token))"

# build & ship as 0.6.9
python -m build
twine upload dist/*
```

Ship this as **0.6.9**. Once published, Workbench installs already in the field self-heal on next launch (they pin to the newest importable release), and any `--no-deps` / frozen / minimal-env consumer can `import qector_decoder_v3` unconditionally again.
