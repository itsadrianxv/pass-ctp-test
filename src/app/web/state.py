"""Web 运行时共享对象。"""

import logging

from src.config import settings as config
from src.infra.process import ProcessManager
from src.infra.rpc.client import RpcClient


process_manager = ProcessManager()
rpc = RpcClient(config.RPC_HOST, config.RPC_PORT)
log = logging.getLogger(__name__)
