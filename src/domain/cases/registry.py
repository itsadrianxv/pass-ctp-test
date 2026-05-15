"""测试用例注册表。"""

from src.domain.cases import case_2_1, case_2_2, case_2_3, case_2_4, case_2_5, case_2_6


CASE_MAP = {
    "2.1.1.1": case_2_1.test_2_1_1_1_normal_connectivity,
    "2.1.1.2": case_2_1.test_2_1_1_2_abnormal_connectivity,
    "2.1.2.1": case_2_1.test_2_1_2_1_open,
    "2.1.2.2": case_2_1.test_2_1_2_2_close,
    "2.1.2.3": case_2_1.test_2_1_2_3_cancel,
    "2.2.1.1": case_2_2.test_2_2_1_1_connect_status,
    "2.2.1.2": case_2_2.test_2_2_1_2_disconnect,
    "2.2.1.3": case_2_2.test_2_2_1_3_reconnect,
    "2.2.3.1": case_2_2.test_2_2_3_1_repeat_open,
    "2.2.3.2": case_2_2.test_2_2_3_2_repeat_close,
    "2.2.3.3": case_2_2.test_2_2_3_3_repeat_cancel,
    "2.3.1.1": case_2_3.test_2_3_1_1_order_threshold,
    "2.3.1.3": case_2_3.test_2_3_1_3_cancel_threshold,
    "2.3.1.5": case_2_3.test_2_3_1_5_repeat_threshold,
    "2.4.1.1": case_2_4.test_2_4_1_1_code_error,
    "2.4.1.2": case_2_4.test_2_4_1_2_price_error,
    "2.4.1.3": case_2_4.test_2_4_1_3_volume_error,
    "2.4.2.1": case_2_4.test_2_4_2_1_fund_error,
    "2.4.2.2": case_2_4.test_2_4_2_2_pos_error,
    "2.4.2.3": case_2_4.test_2_4_2_3_market_error,
    "2.5.1.1": case_2_5.test_2_5_1_1_limit_perms,
    "2.5.1.2": case_2_5.test_2_5_1_2_pause_strategy,
    "2.5.2.1": case_2_5.test_2_5_2_1_cancel_part,
    "2.5.2.2": case_2_5.test_2_5_2_2_cancel_all,
    "2.6.1": case_2_6.test_2_6_1_log_record,
}
