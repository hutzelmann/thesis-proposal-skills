## Why

`run_claude` starts the CLI without closing stdin, so the child inherits whatever the runner was given. When the runner is invoked backgrounded or with its output redirected — the normal way to run several scenarios — stdin is a non-tty that never delivers data. The CLI waits, warns `no stdin data received in 3s`, and the run can exit non-zero, which the runner surfaces as `claude failed`.

The failure does not look like a runner failure. An attribution batch of four runs produced no verdicts at all and was initially read as the scenarios breaking; a sonnet run of `check_report` failed outright and was read as a model difference. Both were this.

It also puts every earlier measurement in question. All the phantom-write observations — runs that produced no proposal file — were taken under exactly these conditions, so a run dying early on stdin is a live alternative explanation to the model failing to write. That cannot be settled while the defect is present.

## What Changes

- The runner closes the child's stdin, so a scenario's outcome does not depend on how the runner itself was invoked.

## Capabilities

None. Runner plumbing with no change to what any verdict asserts or any skill does; `skip_specs` is set accordingly.

## Impact

- `harness/claude_runner.py`: one argument to the subprocess call.
- Unblocks a clean re-measurement of the phantom write, which is the point of fixing it now rather than later.
