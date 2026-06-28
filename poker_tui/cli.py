import logging
import random
from datetime import datetime
from typing import Any

import typer

from poker_tui.domain.player import Player
from poker_tui.domain.table import Table
from poker_tui.engine.events import EventBus
from poker_tui.engine.game_engine import GameEngine
from poker_tui.simulation.runner import SimulationRunner
from poker_tui.storage.json_storage import JsonStorage
from poker_tui.strategies.base import AbstractStrategy
from poker_tui.strategies.simple import SimpleStrategy

app = typer.Typer()
_log = logging.getLogger("poker")


def _setup_logger(engine: GameEngine, log_dir: str = "data/logs") -> None:
    import os
    os.makedirs(log_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    handler = logging.FileHandler(f"{log_dir}/play_{ts}.log")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _log.addHandler(handler)
    _log.setLevel(logging.INFO)

    bus = engine.event_bus
    player_map = {p.name: p for p in engine.state.table.players}

    def _player_state() -> str:
        return ", ".join(
            f"{p.name}=${p.stack}:{p.current_bet}"
            + (" [F]" if p.is_folded else "")
            + (" [O]" if p.is_out else "")
            for p in engine.state.table.players
        )

    def _on_hand_started(e: Any) -> None:
        _log.info("Hand %d started — %s", e.hand_number, _player_state())

    def _on_blinds_posted(e: Any) -> None:
        _log.info("Blinds posted: SB=%d BB=%d — %s", e.small_blind, e.big_blind, _player_state())

    def _on_cards_dealt(e: Any) -> None:
        for name, cards in e.player_cards.items():
            p = player_map.get(name)
            if p and p.strategy_name == "human":
                _log.info("  %s dealt [%s]", name, " ".join(cards))

    def _on_player_acted(e: Any) -> None:
        _log.info("  %s: %s — %s", e.player_name, e.action, _player_state())

    def _on_street_advanced(e: Any) -> None:
        cards = " ".join(str(c) for c in engine.state.table.community_cards)
        _log.info("Street: %s — Board: %s", e.street.value, cards or "none")

    def _on_pot_updated(e: Any) -> None:
        pass

    def _on_showdown_started(e: Any) -> None:
        _log.info("Showdown — %s", _player_state())
        for p in e.players:
            _log.info("  %s: %s", p["name"], " ".join(p["hand"]))

    def _on_hand_ended(e: Any) -> None:
        winners = ", ".join(f'{w["name"]} (${w["amount"]})' for w in e.winners)
        state = _player_state()
        _log.info("Hand %d ended: %s — Pot: $%d — %s", e.hand_number, winners, e.pot_amount, state)

    bus.subscribe("hand_started", _on_hand_started)
    bus.subscribe("blinds_posted", _on_blinds_posted)
    bus.subscribe("cards_dealt", _on_cards_dealt)
    bus.subscribe("player_acted", _on_player_acted)
    bus.subscribe("street_advanced", _on_street_advanced)
    bus.subscribe("pot_updated", _on_pot_updated)
    bus.subscribe("showdown_started", _on_showdown_started)
    bus.subscribe("hand_ended", _on_hand_ended)


def _build_game(
    num_players: int,
    seat: int = 0,
    seed: int | None = None,
    human_name: str = "You",
) -> GameEngine:
    """Create a game engine with one human seat and the rest filled by bots."""
    strategy = SimpleStrategy()
    bot_names = [f"Bot-{i}" for i in range(num_players - 1)]
    all_names = list(bot_names)
    human_idx = min(seat, num_players - 1)
    all_names.insert(human_idx, human_name)

    strategies = {n: strategy for n in all_names if n != human_name}
    players = [
        Player(name=n, stack=1000, position=i, strategy_name="bot" if n != human_name else "human")
        for i, n in enumerate(all_names)
    ]
    return GameEngine(
        table=Table(players=players),
        strategies=strategies,
        rng=random.Random(seed),
        event_bus=EventBus(),
    )


def _make_bot_strategies(count: int) -> dict[str, AbstractStrategy]:
    """Create *count* identical placeholder strategies for bots."""
    s = SimpleStrategy()
    return {f"Bot-{i}": s for i in range(count)}


@app.command()
def play(
    players: int = typer.Option(6, "--players", help="Number of players"),
    seat: int = typer.Option(0, "--seat", help="Your seat position"),
    seed: int | None = typer.Option(None, "--seed", help="RNG seed"),
    debug_show_cards: bool = typer.Option(False, "--debug-show-cards", hidden=True),
) -> None:
    """Play poker against bots (always uses Textual UI)."""
    try:
        from poker_tui.tui.apps.play_app import PlayApp
        engine = _build_game(players, seat, seed)
        _setup_logger(engine)
        _log.info("=== Session started ===")
        PlayApp(engine=engine, show_all=debug_show_cards).run()
    except ImportError as e:
        typer.echo(f"TUI not available: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def observe(
    players: int = typer.Option(6, "--players", help="Number of players"),
    hands: int = typer.Option(100, "--hands", help="Number of hands"),
    seed: int | None = typer.Option(None, "--seed", help="RNG seed"),
    visual: bool = typer.Option(False, "--visual", help="Show TUI observer"),
    debug_show_cards: bool = typer.Option(False, "--debug-show-cards", hidden=True),
) -> None:
    """Observe bot-vs-bot games."""
    strategies = _make_bot_strategies(players)

    if visual:
        try:
            from poker_tui.tui.apps.observe_app import ObserveApp
            runner = SimulationRunner(players, hands, strategies, seed, EventBus())
            ObserveApp(runner=runner, num_hands=hands, show_all=debug_show_cards).run()
        except ImportError as e:
            typer.echo(f"TUI not available: {e}", err=True)
            raise typer.Exit(1)
    else:
        result = SimulationRunner(players, hands, strategies, seed).run()
        typer.echo(f"Completed {result.total_hands} hands")
        for name, s in result.player_stats.items():
            typer.echo(f"  {name}: {s['wins']} wins, ${s['profit']:+d} profit")


@app.command()
def simulate(
    players: int = typer.Option(6, "--players", help="Number of players"),
    hands: int = typer.Option(10000, "--hands", help="Number of hands"),
    seed: int | None = typer.Option(None, "--seed", help="RNG seed"),
    output: str = typer.Option("data/runs/run.json", "--output", help="Output path"),
    visual: bool = typer.Option(False, "--visual", help="Show TUI dashboard"),
) -> None:
    """Run fast bot-vs-bot simulations."""
    strategies = _make_bot_strategies(players)

    if visual:
        try:
            from poker_tui.tui.apps.simulate_app import SimulateApp
            runner = SimulationRunner(players, hands, strategies, seed, EventBus())
            SimulateApp(runner=runner, num_hands=hands).run()
        except ImportError as e:
            typer.echo(f"TUI not available: {e}", err=True)
            raise typer.Exit(1)
    else:
        result = SimulationRunner(players, hands, strategies, seed).run()
        JsonStorage().save(result, output)
        typer.echo(f"Saved {result.total_hands} hand results to {output}")
        for name, s in result.player_stats.items():
            ties = s.get("ties", 0)
            wr = s['win_rate']
            typer.echo(f"  {name}: {s['wins']} wins, {ties} ties ({wr:.1%}), ${s['profit']:+d}")


@app.command()
def stats(
    path: str = typer.Argument(..., help="Path to simulation result JSON"),
    visual: bool = typer.Option(False, "--visual", help="Show TUI stats dashboard"),
) -> None:
    """View simulation statistics."""
    result = JsonStorage().load(path)

    if visual:
        try:
            from poker_tui.tui.apps.stats_app import StatsApp
            StatsApp(result=result).run()
        except ImportError as e:
            typer.echo(f"TUI not available: {e}", err=True)
            raise typer.Exit(1)
    else:
        typer.echo(f"Results from {path}")
        typer.echo(f"Total hands: {result.total_hands}\n")
        for name, s in result.player_stats.items():
            typer.echo(f"  {name}:")
            typer.echo(f"    Wins: {s['wins']} ({s['win_rate']:.1%})")
            typer.echo(f"    Profit: ${s['profit']:+d}")
        if result.action_frequencies:
            typer.echo("\nAction Frequencies:")
            for name, actions in result.action_frequencies.items():
                total = sum(actions.values())
                if total == 0:
                    continue
                parts = [f"{act}: {cnt} ({cnt/total:.0%})" for act, cnt in sorted(actions.items())]
                typer.echo(f"  {name}: {', '.join(parts)}")


if __name__ == "__main__":
    app()
