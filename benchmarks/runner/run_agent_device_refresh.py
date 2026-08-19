#!/usr/bin/env python3
"""Run one resumable refresh pass for the selected agent-device cells.

Current tool/app/skill provenance is skipped and stale results are replaced. Slow-outlier reruns are
an operator instruction, deliberately not automated by this script.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench, isolation, ledger, sim_device


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="gpt_low,haiku_low")
    ap.add_argument("--apps", default="bluesky")
    ap.add_argument("--task", help="one task id (debug/resume aid)")
    ap.add_argument("--wait-lock", action="store_true")
    args = ap.parse_args()

    models = [x for x in args.models.split(",") if x]
    unknown = [x for x in models if x not in bench.MODELS]
    if unknown:
        ap.error(f"unknown models: {', '.join(unknown)}")
    apps = {x for x in args.apps.split(",") if x}
    tasks = [t for t in bench.load_tasks()
             if t["app"] in apps and t["app"] in bench.APPS and not t.get("annulled")
             and (not args.task or t["id"] == args.task)]
    if not tasks:
        ap.error("no tasks selected")

    isolation.acquire_lock(wait=args.wait_lock, label="agent-device refresh")
    sim_device.check_golden()

    print(f"== one pass: {len(models)} cells x {len(tasks)} tasks ==", flush=True)
    for model in models:
        for task in tasks:
            try:
                bench.run_one(model, "agent-device", task)
            except (isolation.TeardownError, isolation.ResetError, sim_device.DeviceError):
                raise
            except Exception as e:
                print(f"  {model}:agent-device/{task['id']} ERROR {e}", flush=True)

    # Fail if the supposedly complete refresh still contains gaps or stale provenance.
    missing = []
    for model in models:
        for task in tasks:
            if ledger.needs_run(bench.RESULTS, model, "agent-device", task["id"],
                                bench.harness_for("agent-device"),
                                {**bench.run_versions("agent-device", task["app"]),
                                 "model_route": bench.model_route(model)}):
                missing.append(f"{model}:agent-device/{task['id']}")
    if missing:
        raise RuntimeError(f"refresh incomplete ({len(missing)}): {', '.join(missing[:10])}")
    print("== agent-device refresh complete ==", flush=True)


if __name__ == "__main__":
    main()
