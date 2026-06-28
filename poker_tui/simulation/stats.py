from collections import defaultdict
from typing import Any

from poker_tui.engine.events import HandEnded, PlayerActed
from poker_tui.simulation.result import SimulationResult


class SimulationStats:
    """Collects per-player statistics by consuming engine events."""

    def __init__(self, total_hands: int, player_names: list[str]) -> None:
        self.total_hands = total_hands
        self.hands_completed = 0
        self.player_names = list(player_names)
        self._wins: dict[str, int] = defaultdict(int)
        self._ties: dict[str, int] = defaultdict(int)
        self._profit: dict[str, int] = defaultdict(int)
        self._actions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._hand_results: list[dict[str, Any]] = []
        self._initial_stacks: dict[str, int] = {}

    def set_initial_stacks(self, stacks: dict[str, int]) -> None:
        self._initial_stacks = dict(stacks)

    def handle_event(self, event: object) -> None:
        if isinstance(event, HandEnded):
            self.hands_completed += 1
            if len(event.winners) == 1:
                self._wins[event.winners[0]["name"]] += 1
            else:
                for w in event.winners:
                    self._ties[w["name"]] += 1
            self._hand_results.append({
                "hand": event.hand_number,
                "winners": event.winners,
                "pot": event.pot_amount,
            })
        elif isinstance(event, PlayerActed):
            self._actions[event.player_name][event.action.action_type.name] += 1

    def update_profit(self, player_name: str, current_stack: int) -> None:
        if player_name in self._initial_stacks:
            self._profit[player_name] = current_stack - self._initial_stacks[player_name]

    def get_result(self) -> SimulationResult:
        return SimulationResult(
            total_hands=self.total_hands,
            players=list(self.player_names),
            player_stats={
                name: {
                    "wins": self._wins.get(name, 0),
                    "ties": self._ties.get(name, 0),
                    "win_rate": self._wins.get(name, 0) / max(self.hands_completed, 1),
                    "profit": self._profit.get(name, 0),
                }
                for name in self.player_names
            },
            hand_results=self._hand_results[-100:],
            action_frequencies={
                name: dict(actions) for name, actions in self._actions.items()
            },
        )
