# termedu

`termedu` is a simple terminal app for short kid-focused math practice sessions. It asks one question at a time, checks the answer immediately, and reads optional learner settings from `~/.termedu`.

## Setup

Install the project dependencies with:

```bash
uv sync
```

## Run

Run the packaged entry point with:

```bash
uv run termedu
```

You can also run the repository wrapper script from the repo root:

```bash
./termedu
```

Both commands accept an optional learner name:

```bash
uv run termedu Mia
./termedu Mia
```

## Test

Run the test suite with:

```bash
uv run pytest
```

## Configuration

Optional settings are loaded from `~/.termedu` in TOML format.

Example:

```toml
name = "Mia"
operation = "multiplication"
left_max = 12
right_max = 12
coin_target = 1.0
correct_reward = 0.05
wrong_penalty = 0.1

# Optional fixed operand mode
fixed_left = 4
# fixed_right = 7
```

Public config keys:

- `name`: optional learner name
- `operation`: optional math operation, defaults to `multiplication`
- `left_max`: maximum left operand when using a range
- `right_max`: maximum right operand when using a range
- `coin_target`: earned-coin goal required before the session ends
- `correct_reward`: coins added for each correct answer
- `wrong_penalty`: coins subtracted for each incorrect answer
- `fixed_left`: optional fixed left operand
- `fixed_right`: optional fixed right operand
