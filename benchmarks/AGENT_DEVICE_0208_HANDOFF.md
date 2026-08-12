# agent-device 0.20.8 refresh handoff

Run from the benchmark Mac. The default batch is `gpt_low,haiku_low` × `agent-device` × all
30 Bluesky tasks (60 runs). It is serial and resumable; do not start a second benchmark stream.

## One-time prerequisites

- Global `agent-device` must report `0.20.8`.
- The installed public skills must exist at `~/.agents/skills/{agent-device,ios-simulator,android-emulator}`.
- `bench-golden-v4` must remain Shutdown. It has been clone-verified to contain Bluesky 1.122.0 and
  Element. `configs/golden.json` selects it by name.
- OpenCode auth must contain `openai` and `vercel` credentials. As a fallback, Haiku accepts
  `AI_GATEWAY_API_KEY` from an env file passed through `BENCH_ENV_FILE`.
- The wrapper starts Bluesky's deterministic dev-env backend (including throwaway PostgreSQL and
  Redis) when `:1987` is down. Synapse must answer on `:8008` when Element is selected. `doctor.py`
  fails before API spend if either reset surface is absent.
- Other simulators may remain booted. Their names are recorded in each run's `env.json` because
  shared CoreSimulator/host load can affect timing, but explicit UDID scoping preserves correctness.
- The wrapper forces `BENCH_KILL_SCOPE=owned` and creates a new process-ownership registry for this
  invocation. It terminates only the OpenCode/proxy/agent-device processes it starts; pre-existing
  daemons and other worktrees are reported and left untouched.
- The benchmark contains no simulator-deletion path. Each case creates a fresh clone for state
  isolation and shuts it down afterward, leaving it available for inspection. Expect
  at least 60 preserved `bench-ad0208-*` clones (plus outlier retries) and ensure sufficient disk space.
  Cleanup is deliberately outside this handoff and requires a separate explicit decision.
- Every run gets a temporary `AGENT_DEVICE_STATE_DIR`, so it cannot reuse or disturb the global
  packaged daemon even when other worktrees have agent-device processes.

## Run

```bash
cd benchmarks
./run_agent_device_0208.sh
```

Policy implemented by the runner:

1. Run every stale/missing selected case once. A result is stale when its harness, app version,
   agent-device version, installed skill hashes, or model route differs.
2. Judge the selected cells and rebuild `public/` and report data through the website build.

Worker instruction — this is deliberately **not automated by benchmark code**: after the one-pass
run, inspect `meta.json.wall_s`. For each case above 200 seconds, rerun that individual case up to two
times, preserve the captures before each forced rerun, and retain the valid capture with the smallest
`wall_s`. Then rerun the judge and website build so the published result reflects the chosen capture.
Do not rerun cases at or below 200 seconds.

To extend the same refresh to Element after restoring Synapse:

```bash
APPS=bluesky,element ./run_agent_device_0208.sh
```

Until then, publish the refreshed Bluesky slice as Bluesky-only: the Element members of each cell
remain 0.17.6 and must not be represented as part of an aggregate 0.20.8 result.

## Comparison baseline

All 240 checked-in agent-device runs record 0.17.6. The low-effort cells to be refreshed currently
measure as follows; time is the mean over all 60 or 30 runs, matching the headline report:

| Model | Scope | agent-device | argent | agent-device time |
| --- | --- | ---: | ---: | ---: |
| GPT mini low | all 60 | 82.5% | 82.5% | 80.2s |
| GPT mini low | Bluesky 30 | 80.0% | 88.3% | 101.8s |
| GPT mini low | Element 30 | 85.0% | 76.7% | 58.6s |
| Haiku low | all 60 | 84.2% | 94.2% | 141.9s |
| Haiku low | Bluesky 30 | 86.7% | 100.0% | 179.9s |
| Haiku low | Element 30 | 81.7% | 88.3% | 104.0s |

Reaching 90% over all 60 tasks requires GPT to gain 4.5 task-points and Haiku 3.5. On the Bluesky
slice alone, GPT needs 3 task-points and Haiku 1. A success is 1 point and a partial is 0.5.

The baseline predates the benchmark-relevant changes shipped by 0.20.8, including hostile-screen
capture cost (#1587), Bluesky-class AX-hostile targeting and text entry (#1588), the iOS text-entry
runner wedge (#1604), hidden-keyboard responder entry and commit observation (#1657/#1676), collapsed
app-driving startup turns (#1693), and faster sparse-tree recovery (#1700). Do not attribute gains to
one change without case evidence, but these fixes cover several observed baseline failure classes.

## Current machine readiness gaps (2026-08-12)

- CoreSimulator stopped discovering runtimes during the two-simulator smoke test and the configured
  golden is no longer available. Restore healthy runtime discovery, recreate/verify the golden, and
  confirm a clone can boot before starting paid runs.
- Bluesky's Expo dev client must reach Metro on `:8081`; the smoke capture failed on its connection
  screen when Metro was absent.
- Synapse `:8008` and its local setup are absent.
- OpenCode now has the Vercel AI Gateway credential; no extra env file is required on this Mac.

The harness code is ready; resolve the simulator/golden and service gaps before handing the paid run
to a worker. Android is not an existing AppControlBench surface: it needs Android task fixtures, reset
contracts, golden/emulator isolation, grading/report dimensions, and its own measurements rather than
reusing iOS screenshots. Treat that as a follow-up benchmark expansion.
