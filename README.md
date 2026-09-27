# termedu

`termedu` is a simple terminal app for short kid-focused math practice sessions. It asks one question at a time, checks the answer immediately, and reads optional learner settings from `~/.config/termedu/config.toml`.

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

Settings are loaded from `~/.config/termedu/config.toml` in TOML format. On the first run, termedu creates this file if it is missing, with the main settings set to their defaults and commented examples for every optional setting. Edit the values or uncomment an example to customize your next session. Existing files are preserved. If `XDG_CONFIG_HOME` is set to an absolute path, termedu uses `$XDG_CONFIG_HOME/termedu/config.toml` instead. To keep settings from an older installation, move `~/.termedu` to the new path before running termedu.

Example:

```toml
name = "Mia"
operation = "multiplication"
question_mode = "mixed"
missing_symbol = "_"
left_min = 0
left_max = 12
right_min = 0
right_max = 12
max_numbers = 3
coin_target = 1.0
correct_reward = 0.05
wrong_penalty = 0.1
greeting_messages = ["Ready?", "Let's practice!"]
success_messages = ["Nice work", "You got it"]
failure_messages = ["Try again", "Keep thinking"]
final_success_message = """
Great work today!
You reached your coin target.
"""

# Optional fixed operand mode
fixed_left = 4
# fixed_right = 7
```

Public config keys:

- `name`: optional learner name
- `operation`: optional math operation, either `multiplication`, `addition`, or `mixed`; defaults to `multiplication`
- `question_mode`: `result` (default), `missing_operand`, or `mixed` to randomly combine both question styles. For example, result questions show `2 x 6 = `; missing-operand questions show `2 x _ = 12  -->  _ = ` and expect `6`. Either operand can be hidden, including in mixed-operation expressions. Blanks always have a unique answer; if no operand can be hidden (such as `0 x 0`), a result question is used instead.
- `left_max`: maximum left operand when using a range
- `left_min`: minimum left operand, defaults to `0`; must be no greater than `left_max`
- `missing_symbol`: non-empty text marking a missing operand, defaults to `_`; for example, `"?"` or `"□"`
- `right_max`: maximum right operand when using a range
- `right_min`: minimum right operand, defaults to `0`; must be no greater than `right_max`
- `max_numbers`: maximum numbers in a mixed-operation question, defaults to `3`
- `coin_target`: earned-coin goal required before the session ends
- `correct_reward`: coins added for each correct answer
- `wrong_penalty`: coins subtracted for each incorrect answer
- `yes_message`: supports `%a` for the correct answer; feedback for a correct answer, defaults to `Yes!`
- `no_message`: supports `%a` for the correct answer; feedback for an incorrect answer, defaults to `No... %a`
- `greeting_messages`: optional greetings printed before practice starts
- `success_messages`: optional feedback choices for correct answers
- `failure_messages`: optional feedback choices for incorrect answers
- `final_success_message`: optional message printed after reaching `coin_target`; TOML multiline strings are supported
- `fixed_left`: optional fixed left operand
- `fixed_right`: optional fixed right operand
