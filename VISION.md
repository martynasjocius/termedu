# termedu Vision

## Purpose

`termedu` is a very simple terminal-based educational app for kids. The first version teaches basic math with short interactive sessions, immediate feedback, and minimal distractions.

This document is intended for AI agents that will design and implement the app. Favor clarity, simplicity, predictable behavior, and a pleasant terminal experience over extensibility or feature breadth.

## Product Summary

The app launches in a terminal, asks the child one math question at a time, accepts the answer on the same line, checks it when Enter is pressed, and immediately proceeds to the next question.

Example prompt:

```text
4 x 3 = _
```

The child types the answer in place of `_` and presses Enter.

If the answer is correct, print `YES` on that same line before moving on.

If the answer is incorrect, print `NO` on that same line before moving on.

The session ends after the child gives 24 correct answers total.

## Core Experience

The first version should feel like a tiny command-line lesson:

1. Start the app.
2. Load configuration from the user config file.
3. Determine the learner name from CLI argument or config.
4. Ask one randomly chosen math question at a time.
5. Check each answer immediately on Enter.
6. Show simple encouragement or disappointment based on streaks.
7. Finish after 24 correct answers.
8. Write a session log file.

The app should be fast to start, have no unnecessary menus, and require no mouse interaction.

## Configuration

The app must read settings from:

```text
~/.termedu
```

Use a standard config file format. Prefer `TOML` because it is simple, readable, and widely supported. If implementation constraints make another standard format materially better, it must still be a well-known format such as `INI`, `TOML`, `JSON`, or `YAML`. Default recommendation: `TOML`.

Recommended example:

```toml
name = "Mia"
operation = "multiplication"
left_max = 12
right_max = 12

# Optional fixed operand mode
fixed_left = 4
# fixed_right = 7
```

### Config fields

- `name`: optional learner name
- `operation`: optional math operation, default `multiplication`
- `left_max`: maximum left operand when using a range, default `12`
- `right_max`: maximum right operand when using a range, default `12`
- `fixed_left`: optional fixed left operand instead of using `0..left_max`
- `fixed_right`: optional fixed right operand instead of using `0..right_max`

### Config rules

- If no config file exists, the app should still run with defaults.
- If the config file exists but is invalid, the app should fail with a clear human-readable error.
- CLI argument for learner name overrides config `name`.
- If neither CLI arg nor config provides a name, the session still runs.
- For version 1, default `operation` is `multiplication`.

## CLI

The app accepts an optional first positional argument:

```text
termedu [name]
```

Behavior:

- If `name` is passed, use it as the learner name.
- If not passed, fall back to config `name`.
- If neither is set, run anonymously.

No other CLI behavior is required in version 1 unless implementation needs a minimal `--help`.

## Lesson Model

Version 1 uses a fixed lesson domain for one operation and one operand matrix.

### Defaults

- Operation: multiplication
- Left range: `0..12`
- Right range: `0..12`
- Session completion target: 24 correct answers

### Operand selection

Questions use two operands, conceptually from a matrix:

- left side from `0..N`
- right side from `0..M`

By default:

- `N = 12`
- `M = 12`

The pair for each question is chosen randomly from the configured lesson space.

### Fixed operand mode

The lesson may use a fixed operand instead of a full range.

Example:

- if `fixed_left = 4`, then questions are of the form `4 x 0`, `4 x 1`, `4 x 2`, and so on
- if `fixed_right = 7`, then questions are of the form `0 x 7`, `1 x 7`, `2 x 7`, and so on

Rules:

- Support either side being fixed.
- If both sides are fixed, the lesson repeatedly asks that one fact in version 1 unless a later implementation chooses to reject this as a degenerate lesson. Preferred behavior for v1: allow it.
- If a side is fixed, the opposite side still uses its configured range.

## Interaction Rules

Each question should be shown in a simple readable form.

For multiplication, display using:

```text
<left> x <right> = 
```

The user enters a numeric answer and presses Enter.

### Answer evaluation

- If correct, print `YES` on the same line.
- If incorrect, print `NO` on the same line.
- Then move to the next question, unless the session has ended.

“On the same line” means the terminal output should preserve the original question line and append the result after the entered answer, rather than printing the verdict on a separate new line.

Example:

```text
4 x 3 = 12 YES
4 x 5 = 18 NO
```

## Streak Feedback

The app should track consecutive correct and incorrect answers.

### Happy feedback

If the learner answers correctly 5 times in a row:

- print a happy kaomoji
- place one blank line above it
- place one blank line below it

### Sad feedback

If the learner answers incorrectly 3 times in a row:

- print a sad kaomoji
- place one blank line above it
- place one blank line below it

### Streak reset behavior

- A correct answer increments the correct streak and resets the incorrect streak to 0.
- An incorrect answer increments the incorrect streak and resets the correct streak to 0.
- After printing the related kaomoji, the streak may continue naturally or reset depending on implementation choice, but this must be consistent and documented. Preferred v1 behavior: reset only the opposite streak as usual and leave the triggering streak intact.

### Kaomoji guidance

Use simple friendly text kaomoji that render in plain terminals. Examples:

- happy: `(^_^)`
- sad: `(T_T)`

Exact kaomoji may vary, but should stay simple and readable.

## Session End

The game ends when the learner has given 24 correct answers in the current session.

Important:

- This is 24 total correct answers, not necessarily consecutive.
- After the 24th correct answer, the app should exit gracefully.
- A short completion message is acceptable but not required.

## Logging

Every session must be logged to a file named:

```text
~/termedu-<name>-<datetime>.txt
```

### Logging rules

- Create one log file per session.
- If learner name is unavailable, use a safe placeholder such as `anonymous`.
- `<datetime>` should be filesystem-safe and sortable, for example `2026-04-26T14-32-09`.
- The file must be written in the user home directory.

### Log contents

The exact format is flexible, but it should be plain text and include at least:

- session start timestamp
- learner name, if known
- effective configuration used
- every question asked
- learner answer
- whether the answer was correct
- total correct answers at end
- session end timestamp

Recommended line-oriented format:

```text
session_start: 2026-04-26T14:32:09
name: Mia
operation: multiplication
left_max: 12
right_max: 12
fixed_left: 4
question: 4 x 3
answer: 12
result: correct
...
session_end: 2026-04-26T14:36:41
total_correct: 24
```

## Defaults Summary

If nothing is configured:

- operation = multiplication
- left range = `0..12`
- right range = `0..12`
- no fixed operand
- no learner name
- finish after 24 correct answers

## Non-Goals For Version 1

Do not add these unless explicitly requested later:

- multiple screens or menus
- scoring systems beyond the specified streak behavior
- persistence of progress across sessions
- graphics or non-terminal UI
- adaptive difficulty
- multiplayer or teacher dashboards
- advanced analytics
- multiple operations in one session

## Implementation Guidance For Agents

Optimize for a tiny reliable CLI program.

### Requirements

- Keep dependencies minimal.
- Prefer standard library support where possible.
- Keep input/output logic straightforward and testable.
- Separate config loading, question generation, answer evaluation, streak tracking, and logging into clean units.

### Behavioral priorities

1. Correct config handling.
2. Correct question generation from ranges or fixed operands.
3. Correct streak handling.
4. Correct session termination after 24 correct answers.
5. Correct per-session log file creation.
6. Pleasant terminal output.

### Edge cases to handle

- missing config file
- invalid config file
- non-numeric answer input
- empty answer input
- anonymous session logging
- fixed operand plus custom ranges

For non-numeric or empty input, preferred v1 behavior is to treat it as incorrect, print `NO`, and continue.

## Acceptance Criteria

An implementation should be considered correct when all of the following are true:

1. Running `termedu` without config starts a playable multiplication session using `0..12` by `0..12`.
2. Running `termedu Alice` uses `Alice` as the learner name.
3. Config values in `~/.termedu` override defaults.
4. CLI name overrides config name.
5. The app asks one random question at a time and checks the answer on Enter.
6. Correct answers append `YES` on the same line.
7. Incorrect answers append `NO` on the same line.
8. Five correct answers in a row print a happy kaomoji with one blank line above and below.
9. Three incorrect answers in a row print a sad kaomoji with one blank line above and below.
10. The session ends after 24 correct answers total.
11. A log file is created in the user home directory for every session.
12. Fixed operand mode works for either side.

## Future Direction

Later versions may add subtraction, addition, division, different lesson types, and more structured progress tracking. Version 1 should not be overengineered for that future, but the code should avoid making such extensions unnecessarily hard.
