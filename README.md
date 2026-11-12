# python-template

A [Copier](https://copier.readthedocs.io/) template for Python projects: `uv` for dependencies,
`ruff` + `ty` for linting/type-checking, `prek` + `pysentry` + `gitleaks` for pre-commit checks,
`pytest` + `pytest-cov` for testing, `zensical` for docs, and GitHub Actions for CI/CD —
generated from a few questions, no cloning required.

## Usage

**macOS / Linux:**

```bash
command -v uvx >/dev/null 2>&1 || { curl -LsSf https://astral.sh/uv/install.sh | sh && source "$HOME/.local/bin/env"; } && uvx copier copy --trust gh:nriveras/python-template my-project
```

**Windows (PowerShell):**

```powershell
if (-not (Get-Command uvx -ErrorAction SilentlyContinue)) { powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"; $env:Path = "$env:USERPROFILE\.local\bin;$env:Path" }; uvx copier copy --trust gh:nriveras/python-template my-project
```

Answer the prompts; the project is ready to use when it's done (dependencies installed,
git repo initialized, commit hooks installed).

To pull in template improvements later, from inside a generated project:

```bash
uvx copier update --trust
```

(This only works once the project — and the template version it was generated from — are
committed to git with a tag; see [Copier's update docs](https://copier.readthedocs.io/en/stable/updating/).)

## What each question controls

| Question | Effect |
|---|---|
| `project_name` | Human-readable name; everything else derives from it unless overridden |
| `project_slug` | PyPI / repo name (lowercase, hyphens) |
| `package_name` | Python import name (lowercase, underscores) |
| `python_version` | `requires-python` and the CI/Docker Python version |
| `license` | Picks the `LICENSE` file content |
| `add_cli` | Adds a [Typer](https://typer.tiangolo.com/) CLI stub + `[project.scripts]` entry |
| `use_docker` | Adds a multi-stage `Dockerfile` + a `ghcr.io` push job in `release.yml` |
| `use_docs` | Adds a [zensical](https://zensical.org/) docs site + a GitHub Pages deploy job |
| `publish_target` | `pypi` (trusted publishing) or `github-release` (artifacts on the release only) |
| `coverage_threshold` | `pytest --cov-fail-under` value |

## Developing this template

This repo is the wizard itself — `copier.yml` plus `template/`. Everything else (this README,
`tests/`, `.github/workflows/test-template.yml`) tests the wizard; none of it is copied into a
generated project (see `_subdirectory: template` in `copier.yml`).

```bash
uv sync                 # install this repo's own dev dependencies
uv run pytest           # render the template with various answers and check the result
```
