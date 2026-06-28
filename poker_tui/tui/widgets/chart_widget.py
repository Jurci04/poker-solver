from textual.widgets import Static


class ChartWidget(Static):
    """Simple terminal charts using unicode block characters. No matplotlib needed."""

    BAR = "█"

    def show_horizontal_bars(self, data: dict[str, float], max_width: int = 40) -> None:
        if not data:
            self.update("[dim]No data[/]")
            return
        m = max(abs(v) for v in data.values()) if any(data.values()) else 1
        lines = [
            f"{label}: [{self._color(v)}]"
            f"{self.BAR * int(abs(v) / m * max_width) if m else ''}[/]"
            f" ${v:+d}"
            for label, v in data.items()
        ]
        self.update("\n".join(lines))

    def show_percentage_bars(self, data: dict[str, float], max_width: int = 40) -> None:
        if not data:
            self.update("[dim]No data[/]")
            return
        lines = []
        for label, val in data.items():
            bar = self.BAR * int(val * max_width) if val > 0 else ""
            color = "green" if val >= 0.5 else "yellow" if val >= 0.2 else "red"
            lines.append(f"{label}: [{color}]{bar}[/] {val:.1%}")
        self.update("\n".join(lines))

    def show_sparkline(self, data: list[float], max_width: int = 40) -> None:
        if not data:
            self.update("[dim]No data[/]")
            return
        if len(data) > max_width:
            step = len(data) / max_width
            data = [data[int(i * step)] for i in range(max_width)]

        mn, mx = min(data), max(data)
        span = mx - mn if mx != mn else 1
        chars = []
        for v in data:
            idx = int((v - mn) / span * 7)
            chars.append("█▇▆▅▄▃▂▁"[min(idx, 7)])
        self.update(f"[green]{''.join(chars)}[/]")

    @staticmethod
    def _color(val: float) -> str:
        return "green" if val > 0 else "red" if val < 0 else "white"
