import tempfile
from pathlib import Path

from poker_tui.simulation.result import SimulationResult
from poker_tui.storage.json_storage import JsonStorage


class TestStorage:
    def test_save_and_load(self) -> None:
        result = SimulationResult(
            total_hands=100,
            players=["Bot-0", "Bot-1"],
            player_stats={
                "Bot-0": {"wins": 55, "win_rate": 0.55, "profit": 200},
                "Bot-1": {"wins": 45, "win_rate": 0.45, "profit": -200},
            },
            hand_results=[
                {"hand": 1, "winners": [{"name": "Bot-0", "amount": 0}], "pot": 100},
            ],
            action_frequencies={
                "Bot-0": {"FOLD": 10, "CHECK": 20, "CALL": 15, "BET": 5, "RAISE": 2},
                "Bot-1": {"FOLD": 12, "CHECK": 18, "CALL": 13, "BET": 4, "RAISE": 1},
            },
            seed=42,
        )

        storage = JsonStorage()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
            storage.save(result, path)

        loaded = storage.load(path)
        assert loaded.total_hands == 100
        assert loaded.players == ["Bot-0", "Bot-1"]
        assert loaded.player_stats["Bot-0"]["wins"] == 55
        assert loaded.player_stats["Bot-0"]["win_rate"] == 0.55
        assert loaded.player_stats["Bot-1"]["profit"] == -200
        assert len(loaded.hand_results) == 1
        assert loaded.action_frequencies["Bot-0"]["FOLD"] == 10
        assert loaded.seed == 42

        Path(path).unlink()

    def test_empty_result_roundtrip(self) -> None:
        result = SimulationResult(total_hands=0)
        storage = JsonStorage()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
            storage.save(result, path)

        loaded = storage.load(path)
        assert loaded.total_hands == 0
        assert loaded.players == []
        assert loaded.player_stats == {}

        Path(path).unlink()
