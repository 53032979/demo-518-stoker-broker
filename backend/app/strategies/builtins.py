from backend.app.domain.models import StrategyTemplate


DEFAULT_TOP_N = 5


def _schema(
    title: str,
    extra_properties: dict | None = None,
    weighting_default: str = "equal",
) -> dict:
    properties = {
        "top_n": {"type": "integer", "minimum": 1, "maximum": 500, "default": DEFAULT_TOP_N},
        "rebalance": {
            "type": "string",
            "enum": ["weekly", "monthly", "quarterly"],
            "default": "monthly",
        },
        "weighting": {
            "type": "string",
            "enum": ["equal", "factor_score"],
            "default": weighting_default,
        },
        "stop_loss": {"type": "number", "minimum": 0, "maximum": 0.8, "default": 0.0},
        "take_profit": {"type": "number", "minimum": 0, "maximum": 5.0, "default": 0.0},
    }
    if extra_properties:
        properties.update(extra_properties)

    return {
        "type": "object",
        "title": title,
        "properties": properties,
        "required": ["top_n", "rebalance", "weighting"],
    }


def get_strategy_templates() -> list[StrategyTemplate]:
    return [
        StrategyTemplate(
            strategy_id="value_quality",
            name="低估值质量组合",
            category="multi_factor",
            description="低 PE/PB 与质量因子过滤的 Top N 组合。",
            parameter_schema=_schema("低估值质量组合参数"),
            default_parameters={"top_n": DEFAULT_TOP_N, "rebalance": "monthly", "weighting": "equal"},
            required_fields=["pe", "pb", "roe"],
        ),
        StrategyTemplate(
            strategy_id="momentum_top_n",
            name="动量 Top N",
            category="momentum",
            description="按近 N 日收益排名选择 Top N。",
            parameter_schema=_schema(
                "动量 Top N 参数",
                {"lookback": {"type": "integer", "minimum": 1, "maximum": 252, "default": 60}},
            ),
            default_parameters={
                "top_n": DEFAULT_TOP_N,
                "rebalance": "monthly",
                "weighting": "equal",
                "lookback": 60,
            },
            required_fields=["close"],
        ),
        StrategyTemplate(
            strategy_id="low_volatility",
            name="低波动组合",
            category="defensive",
            description="选择历史收益波动率较低的标的。",
            parameter_schema=_schema(
                "低波动组合参数",
                {"lookback": {"type": "integer", "minimum": 1, "maximum": 252, "default": 60}},
            ),
            default_parameters={
                "top_n": DEFAULT_TOP_N,
                "rebalance": "monthly",
                "weighting": "equal",
                "lookback": 60,
            },
            required_fields=["close"],
        ),
        StrategyTemplate(
            strategy_id="multi_factor_score",
            name="多因子综合打分",
            category="multi_factor",
            description="价值、质量、动量、低波动、流动性加权评分。",
            parameter_schema=_schema(
                "多因子综合打分参数",
                {
                    "weights": {
                        "type": "object",
                        "default": {
                            "value": 0.25,
                            "quality": 0.25,
                            "momentum": 0.25,
                            "low_volatility": 0.15,
                            "liquidity": 0.10,
                        },
                        "properties": {
                            "value": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.25},
                            "quality": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "default": 0.25,
                            },
                            "momentum": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "default": 0.25,
                            },
                            "low_volatility": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "default": 0.15,
                            },
                            "liquidity": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "default": 0.10,
                            },
                        },
                    }
                },
                weighting_default="factor_score",
            ),
            default_parameters={
                "top_n": DEFAULT_TOP_N,
                "rebalance": "monthly",
                "weighting": "factor_score",
                "weights": {
                    "value": 0.25,
                    "quality": 0.25,
                    "momentum": 0.25,
                    "low_volatility": 0.15,
                    "liquidity": 0.10,
                },
            },
            required_fields=["pe", "pb", "roe", "close", "amount"],
        ),
        StrategyTemplate(
            strategy_id="ma_trend_filter",
            name="均线趋势过滤组合",
            category="timing",
            description="在选股结果上叠加 MA20/MA60 趋势过滤。",
            parameter_schema=_schema(
                "均线趋势过滤组合参数",
                {
                    "ma_fast": {"type": "integer", "minimum": 1, "maximum": 250, "default": 20},
                    "ma_slow": {"type": "integer", "minimum": 1, "maximum": 250, "default": 60},
                },
            ),
            default_parameters={
                "top_n": DEFAULT_TOP_N,
                "rebalance": "monthly",
                "weighting": "equal",
                "ma_fast": 20,
                "ma_slow": 60,
            },
            required_fields=["close"],
        ),
    ]
