from poker_tui.simulation.runner import SimulationRunner
from poker_tui.strategies.placeholder import PlaceholderStrategy


class TestSimulation:
    def test_simulation_completes(self) -> None:
        strategy = PlaceholderStrategy()
        strategies = {f"Bot-{i}": strategy for i in range(3)}
        runner = SimulationRunner(
            num_players=3,
            num_hands=10,
            strategies=strategies,
            seed=42,
        )
        result = runner.run()
        assert result.total_hands == 10

    def test_result_has_player_stats(self) -> None:
        strategy = PlaceholderStrategy()
        strategies = {f"Bot-{i}": strategy for i in range(3)}
        runner = SimulationRunner(
            num_players=3,
            num_hands=5,
            strategies=strategies,
            seed=42,
        )
        result = runner.run()
        assert len(result.player_stats) == 3

    def test_result_has_action_frequencies(self) -> None:
        strategy = PlaceholderStrategy()
        strategies = {f"Bot-{i}": strategy for i in range(2)}
        runner = SimulationRunner(
            num_players=2,
            num_hands=5,
            strategies=strategies,
            seed=42,
        )
        result = runner.run()
        assert len(result.action_frequencies) > 0

    def test_large_simulation_completes(self) -> None:
        strategy = PlaceholderStrategy()
        strategies = {f"Bot-{i}": strategy for i in range(4)}
        runner = SimulationRunner(
            num_players=4,
            num_hands=100,
            strategies=strategies,
            seed=42,
        )
        result = runner.run()
        assert result.total_hands == 100
        assert len(result.player_stats) == 4

    def test_seed_produces_same_result(self) -> None:
        strategy = PlaceholderStrategy()
        strategies = {f"Bot-{i}": strategy for i in range(2)}
        runner1 = SimulationRunner(
            num_players=2, num_hands=10, strategies=strategies, seed=42,
        )
        runner2 = SimulationRunner(
            num_players=2, num_hands=10, strategies=strategies, seed=42,
        )
        r1 = runner1.run()
        r2 = runner2.run()
        assert r1.total_hands == r2.total_hands
