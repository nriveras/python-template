"""Self-tests for the template: render it with various answers and check the result.

Two tiers, on purpose:

- Fast "shape" tests render with `skip_tasks=True` and only check which files come out for
  a given set of answers. They don't run `uv sync` or install hooks, so there's no network
  call and no subprocess spawning per test — this is what makes it practical to check many
  answer combinations.
- One slow "integration" test (`-m slow` to select, or run the full suite) lets the
  post-generation tasks run and then actually runs the generated project's own checks
  (pytest, zensical, prek). File-shape checks alone can't catch "the template renders fine
  but what comes out is broken" bugs — e.g. a hook pinned to a `rev:` that doesn't exist, or
  a Jinja whitespace bug that merges two YAML lines into one. Both of those were real bugs
  caught only by actually running a generated project, during this template's own build.
"""

import subprocess
from pathlib import Path

from copier import run_copy

TEMPLATE_DIR = Path(__file__).parent.parent
_REQUIRED = {"project_name": "Test Project"}


def render(tmp_path: Path, skip_tasks: bool = True, **answers: object) -> Path:
    """Render this template into a fresh directory and return its path.

    Args:
        tmp_path: pytest's per-test temporary directory.
        skip_tasks: when True (the default), skip `git init` / `uv sync` / `prek install` —
            fine for checking file shape, not for checking the project actually works.
        **answers: wizard answers overriding the defaults in copier.yml. `project_name` is
            filled in automatically since it has no default.

    Returns:
        Path to the generated project.
    """
    dst = tmp_path / "project"
    run_copy(
        src_path=str(TEMPLATE_DIR),
        dst_path=str(dst),
        data={**_REQUIRED, **answers},
        defaults=True,
        unsafe=True,
        skip_tasks=skip_tasks,
    )
    return dst


def test_defaults_render_the_minimal_project(tmp_path: Path) -> None:
    """Accepting every default produces a working project with no optional extras."""
    project = render(tmp_path)

    assert (project / "pyproject.toml").exists()
    assert (project / "src" / "test_project" / "__init__.py").exists()
    assert (project / "tests" / "test_test_project.py").exists()
    assert (project / ".pre-commit-config.yaml").exists()
    assert (project / ".copier-answers.yml").exists()
    assert (project / ".github" / "workflows" / "ci.yml").exists()
    assert (project / ".github" / "workflows" / "release.yml").exists()

    # use_docs defaults to true; add_cli and use_docker default to false.
    assert (project / "zensical.toml").exists()
    assert (project / ".github" / "workflows" / "docs.yml").exists()
    assert not (project / "Dockerfile").exists()
    assert not (project / ".dockerignore").exists()
    assert not (project / "src" / "test_project" / "cli.py").exists()
    assert not (project / "tests" / "test_cli.py").exists()


def test_every_optional_feature_off(tmp_path: Path) -> None:
    """Turning every toggle off removes every file gated by it."""
    project = render(
        tmp_path, add_cli=False, use_docker=False, use_docs=False
    )

    assert not (project / "Dockerfile").exists()
    assert not (project / ".dockerignore").exists()
    assert not (project / "zensical.toml").exists()
    assert not (project / "docs").exists()
    assert not (project / ".github" / "workflows" / "docs.yml").exists()
    assert not (project / "src" / "test_project" / "cli.py").exists()
    assert not (project / "tests" / "test_cli.py").exists()
    # Always-on files are still there.
    assert (project / "pyproject.toml").exists()
    assert (project / ".github" / "workflows" / "release.yml").exists()


def test_every_optional_feature_on(tmp_path: Path) -> None:
    """Turning every toggle on adds every file gated by it."""
    project = render(
        tmp_path,
        add_cli=True,
        use_docker=True,
        use_docs=True,
        publish_target="github-release",
    )

    assert (project / "Dockerfile").exists()
    assert (project / ".dockerignore").exists()
    assert (project / "zensical.toml").exists()
    assert (project / "docs" / "index.md").exists()
    assert (project / "docs" / "reference.md").exists()
    assert (project / ".github" / "workflows" / "docs.yml").exists()
    assert (project / "src" / "test_project" / "cli.py").exists()
    assert (project / "tests" / "test_cli.py").exists()

    # The "always runs" release job is always there regardless of publish_target.
    release_yml = (project / ".github" / "workflows" / "release.yml").read_text()
    assert "github-release" in release_yml or "github_release" in release_yml.lower()
    assert "docker/build-push-action" in release_yml


def test_slug_and_package_name_are_derived_consistently(tmp_path: Path) -> None:
    """Slug (hyphens) and package name (underscores) derive from project_name by default.

    This matters because a project generated with a slug and package name that don't match
    (e.g. a hyphen where there should be an underscore) fails at import time, not at
    generation time — the kind of mismatch that's easy to introduce by asking for the three
    independently instead of deriving two of them from one answer.
    """
    project = render(tmp_path, project_name="My Cool Project")
    answers = (project / ".copier-answers.yml").read_text()
    assert "project_slug: my-cool-project" in answers
    assert "package_name: my_cool_project" in answers
    assert (project / "src" / "my_cool_project" / "__init__.py").exists()


def test_generated_project_passes_its_own_checks(tmp_path: Path) -> None:
    """End to end: let the real tasks run, then run the checks CI would run.

    Marked implicitly slow by what it does (network + several subprocesses), not by a
    pytest marker — there's only one of these, so a marker would be more ceremony than
    the thing it's organizing.
    """
    project = render(
        tmp_path,
        skip_tasks=False,
        add_cli=True,
        use_docker=True,
        use_docs=True,
    )

    def run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(args, cwd=project, capture_output=True, text=True)

    tests = run("uv", "run", "pytest")
    assert tests.returncode == 0, tests.stdout + tests.stderr

    docs_build = run("uv", "run", "zensical", "build", "--clean")
    assert docs_build.returncode == 0, docs_build.stdout + docs_build.stderr

    quality = run("uv", "run", "prek", "run", "--all-files")
    assert quality.returncode == 0, quality.stdout + quality.stderr
