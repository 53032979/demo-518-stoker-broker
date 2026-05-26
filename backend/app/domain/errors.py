class QuantLabError(Exception):
    code = "quant_lab_error"
    message = "系统错误"

    def __init__(self, message: str | None = None, details: dict | None = None):
        effective_message = message or self.message
        super().__init__(effective_message)
        self.message = effective_message
        self.details = details or {}


class DataValidationError(QuantLabError):
    code = "data_validation_error"
    message = "数据校验失败"


class StrategyValidationError(QuantLabError):
    code = "strategy_validation_error"
    message = "策略参数校验失败"


class BacktestRuntimeError(QuantLabError):
    code = "backtest_runtime_error"
    message = "回测运行失败"
