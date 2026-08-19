# Entra ID and Air-Gapped Lab Evaluation

QECTOR Decoder Workbench v1.0.1 is the **air-gapped product**. Windows,
Linux, and macOS builds are portable and enforce a mandatory zero-egress policy.
They do not authenticate to Microsoft Entra ID, contact a tenant, open a
browser, send telemetry, check for updates, or download packages.

This is deliberate: a truly air-gapped laboratory cannot perform a live Entra
sign-in. The Entra posture is exposed as `disabled` so an evaluator can verify
that identity traffic is unavailable rather than assume it is merely unused.

## Runtime Guarantees

- `compliance.airgap_mode()` is always `True`.
- `main.launch()` installs `EgressGuard` before the GUI, CLI, or MCP server.
- External DNS, TCP connections, HTTP requests, TLS contexts, and URL downloads
  are blocked and written to the local egress log.
- Loopback is the only allowed network scope, for local services bound to
  `127.0.0.1` or `::1`.
- The application UI contains no external-link buttons and never invokes an OS
  browser or mail client.
- The decoder wheel is provisioned from the local bundle only. A missing wheel
  is an installation error; there is no PyPI fallback.
- Entra `status`, `configure`, `login`, `logout`, and entitlement operations
  fail closed with `status="disabled"`.
- No MSAL package is required or shipped in the air-gapped artifact.

## Evidence Commands

Run these commands on each target machine. They do not require internet access.

```text
qector --version
qector entra status --json
qector compliance --json
qector diagnostics
qector hardware
qector --mcp
```

Expected Entra posture:

```json
{
  "status": "disabled",
  "airgapped": true
}
```

Expected compliance posture:

```text
Offline enforced:  YES (mandatory policy)
Egress guard:      ACTIVE
Network sync:      False
Entra ID:          disabled
VERDICT:           COMPLIANT
```

## Negative Network Tests

The release test suite verifies that the guard rejects external DNS, external
TCP connections, HTTP URL access, and TLS context creation while allowing local
loopback traffic. It also verifies that Entra configuration is refused before
any MSAL import or identity request.

```text
python -m pytest tests/test_compliance.py tests/test_entra_auth.py
```

## Microsoft Evaluation Scope

This artifact is ready for review as an **offline/air-gapped lab build**:

- identity integration is explicitly disabled;
- network behavior is fail-closed and test-backed;
- local evidence is machine-readable;
- no tenant credentials, client secrets, refresh tokens, or identity traffic
  are needed.

A live Entra SSO demonstration requires a separate online product variant and
must not be performed with the air-gapped artifact. No Microsoft certification
or tenant registration is granted by the software itself; the Microsoft team
must perform the external review and approve the submitted evidence.
