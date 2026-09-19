# Release and distribution

## Local installation

For development:

```bash
python -m pip install -e '.[dev]'
```

For an isolated user installation after publication:

```bash
pipx install omnicli
```

The bootstrap script remains the recommended path for contributors and local
pilots. It does not install provider CLIs or authenticate accounts.

## Release checklist

1. Update `__version__`, `pyproject.toml`, and `CHANGELOG.md`.
2. Run the complete CI validation, including `pip-audit`.
3. Build and inspect the wheel and source distribution.
4. Review the generated manifest behavior with hash-only input retention.
5. Tag the release using `vX.Y.Z`.
6. Publish the GitHub release artifacts.
7. When PyPI trusted publishing is configured, publish the same artifacts with
   the release workflow and verify `pipx install omnicli` in a clean environment.

## Supply-chain controls

- Keep GitHub Actions permissions minimal.
- Review Dependabot updates before merging.
- Prefer pinned or reviewed action versions for release workflows.
- Run dependency auditing before release.
- Generate and retain an SBOM with the release artifacts when the distribution
  environment supports it.
