# Tasks

## 1. Deny outward tools

- [x] 1.1 Add `OUTWARD_TOOLS` to `harness/routing.py` and fold it into the routing rig's `DISALLOWED_TOOLS`. The list covers Artifact, ArtifactComments, ArtifactData, SendMessage, ListAgents, PushNotification, RemoteTrigger, CronCreate, CronDelete, ScheduleWakeup and DesignSync. Verify: an L0 test that the routing deny list contains each of them.
- [x] 1.2 Make `host_command` in `harness/claude_runner.py` pass `--disallowed-tools` with `OUTWARD_TOOLS`. Verify: an L0 test that the dev-runner command denies each of them, still allows WebFetch, WebSearch, Skill and the subagent tools the verifier needs, and keeps the budget flag outside the variadic list.
- [x] 1.3 One live check with a model that publishes when it can: `uv run poe dev supervise_scope --model haiku --isolated --keep`. Verify: the saved stream shows no outward tool in the host's tool list and no publish. CronDelete and ListAgents were still listed and were added in 1.1.

## 2. README

- [x] 2.1 Update "For supervisors":
  - the supervise paragraph gains the claim checks with the fresh verifier, the workload check with cut options, format remarks staying in the review, the one lookup question, and the measured model note;
  - the review sentence names six substance tests.

  Verify: by reading it, and the README tests pass.

## 3. Close

- [x] 3.1 `uv run poe test`, `uv run poe specs` green. Routing and model results are recorded in `measurement.md`.
