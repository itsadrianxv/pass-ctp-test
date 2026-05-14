import os
import subprocess
import sys
import time


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKER_ENTRY = os.path.join(PROJECT_ROOT, "src", "app", "worker", "main.py")


def _build_worker_env(base_env: dict | None = None) -> dict:
    """构造 Worker 子进程环境变量。"""
    env = dict(base_env or os.environ)
    project_root_norm = os.path.normcase(os.path.abspath(PROJECT_ROOT))

    raw_pythonpath = env.get("PYTHONPATH", "")
    pythonpath_parts = [part for part in raw_pythonpath.split(os.pathsep) if part]
    normalized_parts = {
        os.path.normcase(os.path.abspath(part))
        for part in pythonpath_parts
    }

    if project_root_norm not in normalized_parts:
        pythonpath_parts.insert(0, PROJECT_ROOT)

    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    return env


class ProcessManager:
    """管理 Worker 子进程。"""

    def __init__(self):
        """初始化进程管理器。"""
        self.process = None
        self.disconnect_mode = False

    def _clear_finished_process(self) -> None:
        """清理已退出的进程引用。"""
        if self.process is not None and self.process.poll() is not None:
            self.process = None

    def is_running(self) -> bool:
        """判断 Worker 是否运行中。"""
        self._clear_finished_process()
        return self.process is not None and self.process.poll() is None

    def start_worker(self, force: bool = False) -> bool:
        """启动 Worker 进程。"""
        if self.disconnect_mode and not force:
            return False

        if self.is_running():
            return True

        self.process = subprocess.Popen(
            [sys.executable, WORKER_ENTRY],
            cwd=PROJECT_ROOT,
            env=_build_worker_env(),
        )
        return True

    def kill_worker(self, timeout_s: float = 5.0) -> bool:
        """终止 Worker 进程。"""
        if not self.process:
            return True

        process = self.process
        exited = process.poll() is not None
        try:
            if not exited:
                process.kill()
                process.wait(timeout=timeout_s)
            exited = process.poll() is not None
            return exited
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return process.poll() is not None
        finally:
            if process.poll() is not None:
                self.process = None

    def restart_worker(self) -> bool:
        """重启 Worker 进程。"""
        self.disconnect_mode = False
        if not self.kill_worker():
            return False
        time.sleep(0.2)
        return self.start_worker(force=True)

    def enter_disconnect_mode(self):
        """进入断线模式。"""
        self.disconnect_mode = True

    def exit_disconnect_mode(self):
        """退出断线模式。"""
        self.disconnect_mode = False
