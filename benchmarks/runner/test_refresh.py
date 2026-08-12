#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench_env
import gen_configs
import isolation
import ledger
import sim_device


class ProvenanceTests(unittest.TestCase):
    def test_global_npm_symlink_resolves_package_root(self):
        with tempfile.TemporaryDirectory() as d:
            package = os.path.join(d, "lib", "node_modules", "agent-device")
            os.makedirs(os.path.join(package, "bin"))
            with open(os.path.join(package, "package.json"), "w") as f:
                json.dump({"name": "agent-device", "version": "0.20.8"}, f)
            target = os.path.join(package, "bin", "agent-device.mjs")
            open(target, "w").close()
            os.makedirs(os.path.join(d, "bin"))
            link = os.path.join(d, "bin", "agent-device")
            os.symlink(target, link)
            with mock.patch.dict(os.environ, {"BENCH_AGENT_DEVICE": link}, clear=False):
                os.environ.pop("BENCH_AGENT_DEVICE_DIR", None)
                self.assertEqual(bench_env.agent_device_dir(), os.path.realpath(package))

    def test_version_or_skill_change_makes_result_runnable(self):
        with tempfile.TemporaryDirectory() as d:
            out = ledger.result_dir(d, "gpt_low", "agent-device", "bsky-01")
            os.makedirs(out)
            open(os.path.join(out, "final.png"), "wb").close()
            with open(os.path.join(out, "meta.json"), "w") as f:
                json.dump({"returncode": 0, "versions": {"harness": "h", "tool": "0.17.6",
                                                          "skill_hashes": {"agent-device": "old"}}}, f)
            self.assertTrue(ledger.needs_run(d, "gpt_low", "agent-device", "bsky-01", "h",
                                             {"tool": "0.20.8", "skill_hashes": {"agent-device": "new"}}))

    def test_skill_manifest_includes_references(self):
        with tempfile.TemporaryDirectory() as d:
            skill = os.path.join(d, "agent-device")
            os.makedirs(os.path.join(skill, "references"))
            with open(os.path.join(skill, "SKILL.md"), "w") as f:
                f.write("router")
            ref = os.path.join(skill, "references", "workflow.md")
            with open(ref, "w") as f:
                f.write("v1")
            with mock.patch.object(gen_configs, "_skill_sources", return_value=([skill], None, None)):
                before = gen_configs.skill_manifest("agent-device")
                with open(ref, "w") as f:
                    f.write("v2")
                after = gen_configs.skill_manifest("agent-device")
            self.assertNotEqual(before, after)


class SharedMachineSafetyTests(unittest.TestCase):
    def test_conflict_check_never_mutates_simulators(self):
        devices = [
            {"name": "Personal iPhone", "udid": "P", "state": "Shutdown", "runtime": "iOS"},
            {"name": "Already Booted", "udid": "B", "state": "Booted", "runtime": "iOS"},
        ]
        with mock.patch.object(sim_device, "_devices", return_value=devices), \
             mock.patch.object(sim_device, "_simctl") as simctl:
            self.assertEqual(sim_device.check_device_conflicts(), ["Already Booted (B)"])
            simctl.assert_not_called()

    def test_preserve_policy_shuts_down_but_does_not_delete_clone(self):
        shutdown = mock.Mock(returncode=0, stderr="")
        devices = [{"name": "bench-ad0208", "udid": "B", "state": "Shutdown", "runtime": "iOS"}]
        with mock.patch.object(sim_device, "_simctl", return_value=shutdown) as simctl, \
             mock.patch.object(sim_device, "_devices", return_value=devices):
            self.assertTrue(sim_device.destroy("B"))
            self.assertEqual(simctl.call_args_list, [mock.call("shutdown", "B", timeout=60)])

    def test_close_uses_only_the_per_run_daemon_state(self):
        with mock.patch.object(isolation, "KILL_PATTERNS", []), \
             mock.patch.object(isolation, "_owned_pids", return_value=set()), \
             mock.patch.object(isolation.subprocess, "run") as run:
            isolation.teardown_all(
                "post", adev="agent-device", adev_udid="B", adev_state_dir="/tmp/bench-state")
            self.assertEqual(run.call_args.kwargs["env"]["AGENT_DEVICE_STATE_DIR"], "/tmp/bench-state")


if __name__ == "__main__":
    unittest.main()
