```markdown
# QECTOR Workbench v3.1.0-pro: Release Notes

**Build:** v3.1.0-pro  
**Build date (local):** 2026-07-04

## Summary

Major improvements in this release:

- Professional documentation generator supporting JSON, Markdown, HTML, LaTeX, PDF, and SVG with full provenance metadata.
- Polished application UI including About and Help dialogs plus improved high-DPI plotting defaults.
- Packaging: PyInstaller-built Windows installer and zipped release package.

## Included Artifacts

- Installer: `dist\QectorWorkbenchSetup.exe`
- Release ZIP: `QectorWorkbench_v3_final_package.zip`
- Documentation exports: `exports\*.{html,pdf,svg,md,tex,json}`
- README: `README_v3.md`

## Changelog (High Level)

- Rewrote `doc_generator.py` as `ProfessionalDocGenerator` with publication-quality figure exports and Tanner graph support.
- Centralized version metadata in `version.py` and updated `QectorWorkbench.spec` for professional branding.
- Improved `app.py` plotting defaults via `_configure_plotting()` and resolved UI font consistency via `theme.py`.
- All tests in `test_upgrades.py` passed.
- Built installer using system Python and PyInstaller. Created final ZIP package.

## Signing Status

Local code signing was attempted but no signing tool (`signtool.exe`) or code signing certificate (`.pfx` / `.p12`) was found in the repository.

The distributed installer is currently **not code-signed**.

## How to Sign Locally (Recommended)

If you have a PFX certificate and password, run the following in PowerShell:

```powershell
signtool sign /f "C:\path\to\certificate.pfx" /p "<password>" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 ".\dist\QectorWorkbenchSetup.exe"
```

Alternatively, use the Windows Certificate Store:

```powershell
signtool sign /n "Your Cert Subject" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 ".\dist\QectorWorkbenchSetup.exe"
```

If you want me to sign the installer, provide the `.pfx` file and password (or grant access to a certificate in the Windows store). I will perform signing and repackage the ZIP.

## Notes and Next Steps

- This release notes file is included in the updated ZIP.
- Timestamped signed ZIP or Authenticode-signed installer is available on request. Provide signing credentials or approve use of a signing service.

## Acknowledgements

Build created with PyInstaller 6.21.0 on system Python 3.12.0 (Windows).
```
