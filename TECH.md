# termedu Tech Stack

## Purpose

This document gives implementation agents concrete technical instructions for building `termedu`. It complements `VISION.md` and should be treated as the default engineering baseline for version 1.

When `VISION.md` and `TECH.md` both apply:

- `VISION.md` defines product behavior
- `TECH.md` defines implementation constraints and preferred tooling

## Language And Runtime

- The app must be written in `Python`.
- Target modern Python, preferably `Python 3.12+`.
- Prefer the Python standard library unless an external dependency provides clear value.
- Keep the dependency footprint very small.

## Dependency And Environment Management

- Use `uv` for project management, virtual environment management, dependency installation, and command execution.
- The repository should be set up so common commands can be run with `uv`.

Recommended commands:

```text
uv sync
uv run termedu
uv run pytest
```

Preferred project metadata:

- use `pyproject.toml`
- define runtime and test dependencies there
- avoid legacy setup files unless they are strictly needed

## Packaging And Entry Point

The app should expose a terminal command named:

```text
termedu
```

### Entry point requirements

- The `termedu` entry point must work independently of the current working directory.
- Do not rely on being run from the repository root.
- All file access must resolve from stable locations such as:
  - the user home directory
  - package/module location
  - explicit absolute paths
- Never assume relative paths from the current shell directory for config, logging, or internal assets.

### Installation expectation

The main script may be linked into the user’s local bin directory so it can be run from any folder. This does not need special runtime logic beyond correct packaging and path handling, but it should be documented in `README.md`.

Examples of acceptable approaches:

- a console script entry point defined in `pyproject.toml`
- a small executable wrapper script that imports the package and calls `main()`

Preferred approach: use a console script entry point via `pyproject.toml`.

## Project Structure

Prefer a small package-based layout similar to:

```text
pyproject.toml
README.md
VISION.md
TECH.md
src/termedu/
src/termedu/__init__.py
src/termedu/cli.py
src/termedu/config.py
src/termedu/lesson.py
src/termedu/session.py
src/termedu/logging_utils.py
tests/
```

Exact module names may vary, but the code should be split by responsibility rather than placed in one large file.

## Configuration Format

- Read user configuration from `~/.termedu`.
- Use a standard config file format.
- Preferred format: `TOML`.

### Parsing guidance

- Prefer the standard library `tomllib` for reading TOML.
- If write support is ever needed later, add a minimal dependency only if justified. Version 1 only needs to read config.
- Expand `~` using reliable home-directory resolution, such as `Path.home()`.

## Testing

- Include unit tests.
- Use `pytest`.
- Keep tests focused on behavior and correctness of the core logic.

### Minimum test coverage expectations

Add tests for at least:

- config loading with defaults
- config loading with valid TOML
- invalid config handling
- CLI name overriding config name
- question generation for ranged operands
- question generation with `fixed_left`
- question generation with `fixed_right`
- correct answer evaluation
- incorrect answer evaluation
- streak tracking for 5 correct answers
- streak tracking for 3 incorrect answers
- session completion after 24 correct answers
- log file naming behavior

### Testing boundaries

- Prefer unit tests for pure logic.
- Keep terminal I/O thin so it can be tested with simple mocking or stream capture.
- Avoid overbuilding integration test infrastructure for version 1.

## CLI And I/O Guidance

- Use straightforward terminal I/O.
- Prefer standard library tools such as `input()`, `print()`, `argparse`, `pathlib`, `random`, and `datetime`.
- Keep CLI parsing minimal.
- If `--help` is implemented, keep it short.

### Output behavior

- Match the behavior defined in `VISION.md`.
- Ensure the answer verdict appears on the same line as the user’s entered answer.
- Keep terminal output plain text and portable.

## Logging Implementation Guidance

- Each session must produce a plain-text log file in the user’s home directory.
- Use a filesystem-safe timestamp in the filename.
- Sanitize the learner name for filename use.
- If no learner name is available, use `anonymous`.

Preferred standard library tools:

- `pathlib`
- `datetime`
- `re` for simple filename sanitization if needed

## Randomness

- Use Python’s standard `random` module for question selection in version 1.
- Keep question generation isolated enough that tests can inject a seeded RNG or stub randomness if needed.

## Code Quality Guidance

- Prefer simple functions and small classes over abstraction-heavy design.
- Separate pure logic from terminal side effects.
- Use type hints throughout the codebase.
- Keep public behavior explicit and easy to test.
- Add concise docstrings where they clarify non-obvious behavior.

## Error Handling

- Config errors should produce clear, human-readable messages.
- Runtime failures should not dump confusing internal details for normal user mistakes.
- Non-numeric input should follow the product behavior from `VISION.md`.

## Recommended Standard Library Usage

Prefer these built-in modules where applicable:

- `argparse`
- `dataclasses`
- `datetime`
- `pathlib`
- `random`
- `re`
- `tomllib`
- `typing`

## Non-Goals

Do not introduce these for version 1 unless explicitly required:

- web frameworks
- GUI frameworks
- databases
- heavyweight CLI frameworks
- async architecture
- plugin systems
- telemetry services

## README Expectations

The `README.md` should eventually include:

- what `termedu` does
- how to install dependencies with `uv`
- how to run it with `uv`
- how to run tests
- where config is stored
- the fact that the `termedu` script can be linked into the user’s local bin directory so it is runnable from any folder

## Acceptance Criteria

An implementation aligns with this document when:

1. The codebase is Python-based and managed with `uv`.
2. The project uses `pyproject.toml`.
3. The app exposes a `termedu` entry point.
4. The entry point works regardless of the current working directory.
5. Config is read from `~/.termedu` using a standard format, preferably TOML.
6. The project includes unit tests using `pytest`.
7. The implementation keeps dependencies minimal and uses the standard library where practical.
