from textual.widgets import Static


class ActionLogWidget(Static):
    """A scrollable action log that keeps only the last *MAX_LINES* entries."""

    MAX_LINES = 50

    def __init__(self) -> None:
        super().__init__("")
        self._lines: list[str] = []

    def add_line(self, line: str) -> None:
        self._lines.append(line)
        if len(self._lines) > self.MAX_LINES:
            self._lines = self._lines[-self.MAX_LINES:]
        self.update("\n".join(self._lines))
