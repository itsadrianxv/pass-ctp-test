import os
import unittest

from src.web.process_manager import PROJECT_ROOT, ProcessManager, _build_worker_env


class _FakeProcess:
    def __init__(self):
        self._poll = None
        self.kill_called = False
        self.wait_timeout = None

    def poll(self):
        return self._poll

    def kill(self):
        self.kill_called = True
        self._poll = 1

    def wait(self, timeout=None):
        self.wait_timeout = timeout
        return self._poll


class ProcessManagerTests(unittest.TestCase):
    def test_build_worker_env_prepends_project_root(self):
        env = _build_worker_env({"PYTHONPATH": os.pathsep.join(["C:\\custom", PROJECT_ROOT])})
        parts = env["PYTHONPATH"].split(os.pathsep)

        self.assertEqual(parts[0], "C:\\custom")
        self.assertIn(PROJECT_ROOT, parts)

        env_without_root = _build_worker_env({"PYTHONPATH": "C:\\custom"})
        self.assertEqual(env_without_root["PYTHONPATH"].split(os.pathsep)[0], PROJECT_ROOT)

    def test_kill_worker_waits_and_clears_process_handle(self):
        manager = ProcessManager()
        fake_process = _FakeProcess()
        manager.process = fake_process

        self.assertTrue(manager.kill_worker(timeout_s=1.5))
        self.assertTrue(fake_process.kill_called)
        self.assertEqual(fake_process.wait_timeout, 1.5)
        self.assertIsNone(manager.process)


if __name__ == "__main__":
    unittest.main()
