import pytest

from poker_tui.cli import _build_game, _make_bot_strategies
from poker_tui.strategies.placeholder import PlaceholderStrategy
from poker_tui.strategies.registry import make_strategy, strategy_names
from poker_tui.strategies.simple import SimpleStrategy


def test_registry_builds_known_strategies() -> None:
    assert isinstance(make_strategy("simple"), SimpleStrategy)
    assert isinstance(make_strategy("placeholder"), PlaceholderStrategy)


def test_registry_rejects_unknown_strategy() -> None:
    with pytest.raises(ValueError, match="Available"):
        make_strategy("missing")
    assert "simple" in strategy_names()


def test_cli_helpers_wire_selected_strategy() -> None:
    strategies = _make_bot_strategies(2, "placeholder")
    assert all(isinstance(strategy, PlaceholderStrategy) for strategy in strategies.values())

    engine = _build_game(3, bot_strategy="placeholder")
    bots = [p for p in engine.state.table.players if p.name != "You"]
    assert {p.strategy_name for p in bots} == {"placeholder"}
