import time
import traceback
from src.config import settings as config
from src.domain.engine import TestEngine
from src.domain.cases.helpers import wait_for_reaction, clean_environment, check_contract
from src.infra.logging import log_info, log_error, log_warning
from vnpy.trader.object import OrderRequest, CancelRequest
from vnpy.trader.constant import Direction, OrderType, Offset, Exchange

def test_2_6_1_log_record(engine: TestEngine):
    """
    2.6.1 日志记录功能验证
    """
    log_info("\n>>> [2.6.1] 日志记录验证")
    log_info("请人工检查 log/ 目录下的日志文件。")
    log_info("应包含标签: [Trade], [Order], [Error], [Monitor]")
    log_info("当前控制台显示的日志即证明了日志功能的实时性。")
