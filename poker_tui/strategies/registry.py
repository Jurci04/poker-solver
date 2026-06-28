from collections.abc import Callable

from poker_tui.strategies.base import AbstractStrategy
from poker_tui.strategies.placeholder import PlaceholderStrategy
from poker_tui.strategies.simple import SimpleStrategy

StrategyFactory = Callable[[], AbstractStrategy]

STRATEGIES: dict[str, StrategyFactory] = {
    "simple": SimpleStrategy,
    "placeholder": PlaceholderStrategy,
}


def strategy_names() -> str:
    return ", ".join(sorted(STRATEGIES))


def make_strategy(name: str) -> AbstractStrategy:
    try:
        return STRATEGIES[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown strategy '{name}'. Available: {strategy_names()}") from exc
