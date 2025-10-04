# GitHub Actions Workflow

This repository uses GitHub Actions for automated testing, version checking, and PyPI publishing.

## Workflows

### 1. Tests (`test.yml`)
**Triggers:** On every PR and push to main

**What it does:**
- Runs the full test suite
- Tests against Python 3.8, 3.9, 3.10, 3.11, 3.12
- Generates code coverage reports
- Uploads coverage to Codecov

**Status:** [![Tests](https://github.com/eflee/r53-ddns/actions/workflows/test.yml/badge.svg)](https://github.com/eflee/r53-ddns/actions/workflows/test.yml)

### 2. Version Check (`version-check.yml`)
**Triggers:** On every PR to main

**What it does:**
- Ensures version number has been updated
- Validates semantic versioning format (MAJOR.MINOR.PATCH)
- Confirms new version is greater than current
- Checks version consistency across `__init__.py`, `setup.py`, and `pyproject.toml`

**Status:** [![Version Check](https://github.com/eflee/r53-ddns/actions/workflows/version-check.yml/badge.svg)](https://github.com/eflee/r53-ddns/actions/workflows/version-check.yml)

### 3. Publish to PyPI (`publish.yml`)
**Triggers:** On push to main (after merge)

**What it does:**
- Detects if version number changed in the merge
- If version changed:
  - Builds the Python package
  - Validates the package
  - Publishes to PyPI
  - Creates a GitHub release with tag

**Status:** Runs automatically on version bumps

## Setup Required

### PyPI API Token

To enable automated publishing, you need to set up a PyPI API token:

1. **Create PyPI API Token:**
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token with scope for this project
   - Copy the token (starts with `pypi-`)

2. **Add to GitHub Secrets:**
   - Go to repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Paste your PyPI token
   - Click "Add secret"

### GitHub Token

The `GITHUB_TOKEN` is automatically provided by GitHub Actions for creating releases.

## Workflow Process

### For Contributors (Pull Requests):

1. **Create a branch** for your changes
2. **Update the version** in three files:
   - `__init__.py`
   - `setup.py`
   - `pyproject.toml`
3. **Follow semantic versioning:**
   - MAJOR (x.0.0): Breaking changes
   - MINOR (2.x.0): New features, backwards compatible
   - PATCH (2.0.x): Bug fixes, backwards compatible
4. **Create a PR** to main
5. **Automated checks run:**
   - Tests run on all Python versions
   - Version check validates the version bump
6. **Merge** when checks pass and PR is approved

### After Merge to Main:

1. **Tests run** on the merged code
2. **Version check** detects if version changed
3. **If version changed:**
   - Package is built
   - Published to PyPI
   - GitHub release is created with tag `vX.Y.Z`

## Example: Making a Release

```bash
# 1. Create a feature branch
git checkout -b feature/new-feature

# 2. Make your changes
# ... edit code ...

# 3. Update version in all three files
# __init__.py:     __version__ = '2.1.0'
# setup.py:        version='2.1.0',
# pyproject.toml:  version = "2.1.0"

# 4. Update CHANGELOG.md
# Add your changes under a new version section

# 5. Commit and push
git add -A
git commit -m "Add new feature"
git push origin feature/new-feature

# 6. Create PR on GitHub
# Tests and version check will run automatically

# 7. Merge PR
# After merge, package is automatically published to PyPI
```

## Troubleshooting

### Version Check Fails

**Error:** "Version not updated"
- **Solution:** Update version in `__init__.py`, `setup.py`, and `pyproject.toml`

**Error:** "Version mismatch across files"
- **Solution:** Ensure version is identical in all three files

**Error:** "New version must be greater than current version"
- **Solution:** Increment the version number properly

### PyPI Publish Fails

**Error:** "Invalid or non-existent authentication"
- **Solution:** Check that `PYPI_API_TOKEN` secret is set correctly

**Error:** "File already exists"
- **Solution:** Version already published to PyPI, bump version number

### Tests Fail

- Check test output in GitHub Actions
- Run tests locally: `python -m pytest tests/ -v`
- Fix failing tests before merging

## Manual Publishing (if needed)

If you need to publish manually:

```bash
# Build the package
python -m build

# Check the package
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

## Monitoring

- **Test Results:** Check the Actions tab in GitHub
- **PyPI Releases:** https://pypi.org/project/r53-ddns/
- **GitHub Releases:** https://github.com/eflee/r53-ddns/releases
