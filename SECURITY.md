# Security policy

## Supported versions

OmniCLI is alpha software. Security fixes are applied to the latest release and the `main` branch; older versions may not receive patches.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use the repository's [private security advisory form](https://github.com/leandroclf/OmniCLI/security/advisories/new) and include:

- affected version or commit;
- impact and realistic attack scenario;
- minimal reproduction steps;
- suggested mitigation, if known.

Do not include real secrets or personal data. Maintainers should acknowledge a complete report within seven days and coordinate disclosure after a fix or documented mitigation is available.

## Security posture

OmniCLI does not provide a sandbox. Provider CLIs run with the current user's permissions and may send content to external services. The project does not execute generated code or mutate repositories in the current conception workflow. Review the [threat model](docs/threat-model.md) for boundaries and residual risks.
