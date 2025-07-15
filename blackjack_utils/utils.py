from typing import List
import pandas as pd
import blackjack_utils.game_config as gc
import blackjack_utils.shoe as shoe
import blackjack_utils.card as card
import blackjack_utils.deck as deck

def simulate_hand(game_config: gc.GameConfig, player_starting_cards: List[card.Card], dealer_card_up:card.Card, deck: shoe.Shoe, ev_actions: pd.DataFrame):
    """
        uses an EV action table like above to make a decision, then play through the hand
    """
    player_total = game_config.score_hand(player_starting_cards)
    # is_paired = player_starting_cards[0].get_card_value() == player_starting_cards[1].get_card_value()
    # is_soft = player_starting_cards[0].get_card_value() == 11 or player_starting_cards[1].get_card_value() == 11
    if player_total > 20:
        action = 'stand'
    else:
        try:
            action = ev_actions[(ev_actions['player_total'] == str(player_total)) & (ev_actions['dealer_card_up'] == str(dealer_card_up.get_card_value()))]['best_action'].iloc[0]
        except IndexError:
            action = 'stand'
            print(f"player_total: {player_total}, dealer_card_up: {dealer_card_up.get_card_value()}, ev_actions: {ev_actions}")
    outcome_multiplier = 1
    can_keep_hitting = True
    player_cards = player_starting_cards.copy()
    if action == 'hit':
        player_cards.append(deck.draw())
    elif action == 'double':
        outcome_multiplier = 2
        can_keep_hitting = False
        player_cards.append(deck.draw())
    elif action == 'stand':
        can_keep_hitting = False
    player_total = game_config.score_hand(player_cards)
    if player_total > 20:
        can_keep_hitting = False
    if can_keep_hitting:
        return simulate_hand(game_config, player_cards, dealer_card_up, deck, ev_actions)
    return outcome_multiplier * game_config.evaluate(player_cards, [dealer_card_up, deck.draw()], deck)

def build_combos():
    combos = {}
    for i in range(2, 22):
        combos[str(i)] = []
    for i in range(12, 21):
        combos[f"soft_{i}"] = []
    for i in range(2, 21, 2):
        combos[f'paired_{i}'] = []
    deck_1 = deck.Deck()
    deck_2 = deck.Deck()
    for card_1 in deck_1.cards:
        for card_2 in deck_2.cards:
            total = card_1.get_card_value() + card_2.get_card_value()
            if total == 22:
                total = 12
            if card_1.get_card_value() == card_2.get_card_value():
                combos[f'paired_{total}'].append((card_1, card_2))
            if (card_1.get_card_value() == 11 or card_2.get_card_value() == 11) and total < 21:
                combos[f'soft_{total}'].append((card_1, card_2))
            else:
                combos[str(total)].append((card_1, card_2))
                
    return combos


def determine_best_action(row: pd.Series) -> pd.DataFrame:
    if row['double'] > row['hit'] and row['double'] > row['stand']:
        return 'double'
    elif row['hit'] > row['stand']:
        return 'hit'
    else:
        return 'stand'