"""Worker 进程入口。"""

import time
import traceback

from src.app.worker.controller import WorkerController
from src.infra.logging import log_error, log_info, setup_logger
from src.infra.rpc.server import CommandServer


def main() -> None:
    """启动 Worker 进程。"""
    setup_logger()
    log_info("=== 交易进程 (Worker) 启动 ===")

    controller = None
    server = None
    try:
        log_info("正在初始化 MainEngine/TestApp...")
        controller = WorkerController()
        server = CommandServer(controller)
        server.start()

        time.sleep(1.0)
        if not server.is_alive():
            log_error("RPC Server 未能成功启动（可能端口被占用），Worker 即将退出。")
            if controller:
                controller.stop()
            return

        log_info("交易进程就绪，等待指令...")
        while server.is_alive():
            time.sleep(1)

        log_error("RPC Server 已停止，Worker 即将退出。")

    except KeyboardInterrupt:
        log_info("交易进程收到退出信号。")
    except Exception as exc:
        log_error(f"交易进程发生未捕获异常: {exc}")
        log_error(traceback.format_exc())
    finally:
        try:
            if server:
                server.stop()
        except Exception:
            pass
        try:
            if controller:
                controller.stop()
        except Exception:
            pass


if __name__ == "__main__":
    main()
