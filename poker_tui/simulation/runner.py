import random
from collections.abc import Mapping

from poker_tui.domain.enums import PlayerStatus
from poker_tui.domain.player import Player
from poker_tui.domain.table import Table
from poker_tui.engine.events import EventBus, HandEnded, PlayerActed
from poker_tui.engine.game_engine import GameEngine
from poker_tui.simulation.result import SimulationResult
from poker_tui.simulation.stats import SimulationStats
from poker_tui.strategies.base import AbstractStrategy


class SimulationRunner:
    """Runs many bot-vs-bot hands headlessly, collecting stats."""

    def __init__(
        self,
        num_players: int,
        num_hands: int,
        strategies: Mapping[str, AbstractStrategy],
        seed: int | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._num_hands = num_hands
        self._rng = random.Random(seed)
        self._event_bus = event_bus or EventBus()
        strat_map = dict(strategies)

        # Ensure enough player entries.
        player_names = list(strategies.keys())
        if len(player_names) < num_players:
            fallback = list(strategies.values())[0]
            for i in range(len(player_names), num_players):
                name = f"Bot-{i}"
                strat_map[name] = fallback
                player_names.append(name)

        players = [
            Player(name=n, stack=1000, position=i, strategy_name="bot")
            for i, n in enumerate(player_names[:num_players])
        ]
        self._table = Table(players=players)

        self._engine = GameEngine(
            table=self._table,
            strategies=strat_map,
            rng=random.Random(self._rng.randint(0, 2**32)),
            event_bus=self._event_bus,
        )

        self._stats = SimulationStats(num_hands, list(strat_map.keys()))
        self._stats.set_initial_stacks({p.name: p.stack for p in players})
        self._event_bus.subscribe("hand_ended", self._on_hand_ended)
        self._event_bus.subscribe("player_acted", self._on_player_acted)

    def _on_hand_ended(self, event: object) -> None:
        if isinstance(event, HandEnded):
            self._stats.handle_event(event)
            for p in self._table.players:
                self._stats.update_profit(p.name, p.stack)

    def _on_player_acted(self, event: object) -> None:
        if isinstance(event, PlayerActed):
            self._stats.handle_event(event)

    def run(self) -> SimulationResult:
        for _ in range(self._num_hands):
            self._engine.play_hand()
            if sum(1 for p in self._table.players if not p.is_out) <= 1:
                self._reinitialize_players()
        return self._stats.get_result()

    def run_all(self) -> None:
        self.run()

    def run_step(self) -> bool:
        if self._stats.hands_completed >= self._num_hands:
            return False
        self._engine.play_hand()
        if sum(1 for p in self._table.players if not p.is_out) <= 1:
            self._reinitialize_players()
        return self._stats.hands_completed < self._num_hands

    def _reinitialize_players(self) -> None:
        for p in self._table.players:
            p.status = PlayerStatus.ACTIVE
            p.stack = 1000
            p.reset_for_new_hand()

    @property
    def stats(self) -> SimulationStats:
        return self._stats

    @property
    def engine(self) -> GameEngine:
        return self._engine
