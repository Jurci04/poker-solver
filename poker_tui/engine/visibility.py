from poker_tui.domain.action import Action
from poker_tui.domain.enums import Street
from poker_tui.domain.player import Player
from poker_tui.domain.table import Table
from poker_tui.engine.public_state import PlayerView, PublicGameState


class VisibilityFilter:
    """Centralized visibility filtering for hole cards.

    - `player_state`: shows own cards, hides opponents unless at showdown.
    - `public_state`: shows all or none (for observers/debug).
    """

    @staticmethod
    def public_state(
        table: Table,
        pot_total: int,
        current_bet: int,
        street: Street,
        hand_number: int,
        current_player_name: str,
        show_all: bool = False,
    ) -> PublicGameState:
        players = [
            PlayerView(
                name=p.name, stack=p.stack, position=p.position,
                current_bet=p.current_bet, is_dealer=p.is_dealer,
                is_small_blind=p.is_small_blind, is_big_blind=p.is_big_blind,
                is_active=p.is_active, is_folded=p.is_folded,
                hole_cards=list(p.hand.cards) if show_all else [],
                total_bet_this_hand=p.total_bet_this_hand,
            )
            for p in table.players
        ]
        return PublicGameState(
            community_cards=list(table.community_cards),
            pot_total=pot_total, current_bet=current_bet,
            street=street, hand_number=hand_number,
            players=players, current_player_name=current_player_name,
        )

    @staticmethod
    def player_state(
        table: Table,
        player: Player,
        pot_total: int,
        current_bet: int,
        street: Street,
        hand_number: int,
        legal_actions: list[Action],
        show_opponent_cards: bool = False,
    ) -> PublicGameState:
        players = []
        for p in table.players:
            if p.name == player.name or show_opponent_cards:
                hole = list(p.hand.cards)
            elif street == Street.SHOWDOWN:
                hole = list(p.hand.cards) if not p.is_folded else []
            else:
                hole = []
            players.append(PlayerView(
                name=p.name, stack=p.stack, position=p.position,
                current_bet=p.current_bet, is_dealer=p.is_dealer,
                is_small_blind=p.is_small_blind, is_big_blind=p.is_big_blind,
                is_active=p.is_active, is_folded=p.is_folded,
                hole_cards=hole, total_bet_this_hand=p.total_bet_this_hand,
            ))
        return PublicGameState(
            community_cards=list(table.community_cards),
            pot_total=pot_total, current_bet=current_bet,
            street=street, hand_number=hand_number,
            players=players, current_player_name=player.name,
            legal_actions=list(legal_actions),
        )
