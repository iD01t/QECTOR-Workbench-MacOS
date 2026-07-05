QECTOR Workbench v3.1.0-pro — Release Notes

Build: v3.1.0-pro
Build date (local): 2026-07-04

Summary
- Major: Professional documentation generator (JSON/MD/HTML/LaTeX/PDF/SVG) with provenance metadata.
- Major: Polished application UI, About/Help dialogs, high-DPI plotting defaults.
- Packaging: PyInstaller-built Windows installer and zipped release package.

Included artifacts
- Installer: dist\QectorWorkbenchSetup.exe
- Release ZIP: QectorWorkbench_v3_final_package.zip
- Documentation exports: exports\*.{html,pdf,svg,md,tex,json}
- README: README_v3.md

Changelog (high level)
- Rewrote `doc_generator.py` as `ProfessionalDocGenerator` with publication-quality figure exports and Tanner graph support.
- Centralized version metadata in `version.py` and updated `QectorWorkbench.spec` for pro branding.
- Improved `app.py` plotting defaults via `_configure_plotting()` and resolved UI font consistency via `theme.py`.
- Ran tests (`test_upgrades.py`) — all tests passed.
- Built installer using system Python + PyInstaller; created final ZIP package.

Signing status
- Attempted local signing but no signing tool (`signtool.exe`) or code signing certificate file (.pfx/.p12) found in the repository.
- The distributed installer currently is NOT code-signed.

How to sign locally (recommended)
- If you have a PFX certificate and password, run (PowerShell):

  signtool sign /f "C:\path\to\certificate.pfx" /p "<password>" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 ".\dist\QectorWorkbenchSetup.exe"

- Alternatively, use Windows Certificate Store with `signtool sign /n "Your Cert Subject" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 ".\dist\QectorWorkbenchSetup.exe"`

If you want me to sign the installer, provide the `.pfx` file and password (or grant access to a certificate in the Windows store) and I will perform signing and repackage the ZIP.

Notes and next steps
- I included this release notes file in the updated ZIP.
- If you'd like a timestamped signed ZIP or an Authenticode-signed installer, provide signing credentials or tell me to use a signing service.

Acknowledgements
- Build created with PyInstaller 6.21.0 on system Python 3.12.0 (Windows).