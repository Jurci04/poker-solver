from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Input, Static

from poker_tui.domain.action import Action
from poker_tui.domain.enums import ActionType


class ActionPanelWidget(Static):
    """Shows action buttons during play, or result + Next Hand when hand ends."""

    BTN_IDS = {ActionType.FOLD: "fold", ActionType.CHECK: "check",
               ActionType.CALL: "call", ActionType.BET: "bet", ActionType.RAISE: "raise"}

    def compose(self) -> ComposeResult:
        with Horizontal(id="play-btns"):
            yield Button("Fold", id="fold", variant="error")
            yield Button("Check", id="check", variant="primary")
            yield Button("Call", id="call", variant="primary")
            yield Button("Bet", id="bet", variant="warning")
            yield Button("Raise", id="raise", variant="warning")
        with Horizontal(id="amount-row"):
            yield Input(placeholder="Amount", id="amount-input", type="integer")
        with Horizontal(id="result-btns", classes="hidden"):
            yield Static(id="result-text")
            yield Button("Next Hand", id="next_hand", variant="success")

    def set_legal_actions(self, actions: list[Action]) -> None:
        self.query_one("#play-btns").remove_class("hidden")
        self.query_one("#amount-row").remove_class("hidden")
        self.query_one("#result-btns").add_class("hidden")
        legal = {a.action_type for a in actions}
        for atype, btn_id in self.BTN_IDS.items():
            self._set_enabled(btn_id, atype in legal)
        self._set_enabled("amount-input", ActionType.BET in legal or ActionType.RAISE in legal)

    def disable_all(self) -> None:
        for btn_id in list(self.BTN_IDS.values()) + ["amount-input"]:
            self._set_enabled(btn_id, False)

    def get_amount(self) -> str:
        try:
            return self.query_one("#amount-input", Input).value
        except Exception:
            return ""

    def show_result(self, text: str) -> None:
        self.query_one("#play-btns").add_class("hidden")
        self.query_one("#amount-row").add_class("hidden")
        self.query_one("#result-btns").remove_class("hidden")
        self.query_one("#result-text", Static).update(text)

    def _set_enabled(self, btn_id: str, enabled: bool) -> None:
        try:
            self.query_one(f"#{btn_id}", Button).disabled = not enabled
        except Exception:
            pass
