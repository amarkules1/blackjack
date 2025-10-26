from typing import List
import pandas as pd
import blackjack_utils.game_config as gc
import blackjack_utils.shoe as shoe
import blackjack_utils.card as card
import blackjack_utils.deck as deck


def is_soft_count(player_cards):
    aces = sum(1 for card in player_cards if card.rank == 12)
    total = sum(card.get_card_value() for card in player_cards)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total > 10 and aces > 0

def simulate_hand(game_config: gc.GameConfig, player_starting_cards: List[card.Card], dealer_card_up:card.Card, deck: shoe.Shoe, ev_actions: pd.DataFrame, ignore_dealer_blackjack=False):
    """
        uses an EV action table like above to make a decision, then play through the hand
    """
    player_total = game_config.score_hand(player_starting_cards)
    is_paired = player_starting_cards[0].get_card_value() == player_starting_cards[1].get_card_value() and len(player_starting_cards) == 2
    is_soft = is_soft_count(player_starting_cards)
    player_hand_str = f"{player_total}"
    if is_paired and is_soft:
        player_hand_str = "paired_aces"
    elif is_paired:
        player_hand_str = f"paired_{player_total}"
    elif is_soft:
        player_hand_str = f"soft_{player_total}"
        
    if player_total > 20:
        action = 'stand'
    else:
        try:
            action = ev_actions[(ev_actions['player_total'] == player_hand_str) & (ev_actions['dealer_card_up'] == str(dealer_card_up.get_card_value()))]['best_action'].iloc[0]
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
    elif action == 'split':
        player_cards_a = [player_cards[0]]
        player_cards_b = [player_cards[1]]
        player_cards_a.append(deck.draw())
        player_cards_b.append(deck.draw())
        outcome_a = simulate_hand(game_config, player_cards_a, dealer_card_up, deck, ev_actions, ignore_dealer_blackjack)
        outcome_b = simulate_hand(game_config, player_cards_b, dealer_card_up, deck, ev_actions, ignore_dealer_blackjack)
        return outcome_a + outcome_b
    elif action == 'surrender':
        return -0.5
    player_total = game_config.score_hand(player_cards)
    if player_total > 20:
        can_keep_hitting = False
    if can_keep_hitting:
        return simulate_hand(game_config, player_cards, dealer_card_up, deck, ev_actions, ignore_dealer_blackjack)
    return outcome_multiplier * game_config.evaluate(player_cards, [dealer_card_up, deck.draw()], deck, ignore_dealer_blackjack)

def build_combos():
    combos = {}
    for i in range(2, 22):
        combos[str(i)] = []
    for i in range(12, 21):
        combos[f"soft_{i}"] = []
    for i in range(2, 21, 2):
        combos[f'paired_{i}'] = []
    combos['paired_aces'] = []
    deck_1 = deck.Deck()
    deck_2 = deck.Deck()
    for card_1 in deck_1.cards:
        for card_2 in deck_2.cards:
            total = card_1.get_card_value() + card_2.get_card_value()
            if total == 22:
                total = 12
                combos['paired_aces'].append((card_1, card_2)) 
            elif card_1.rank == card_2.rank:
                combos[f'paired_{total}'].append((card_1, card_2))
            elif (card_1.get_card_value() == 11 or card_2.get_card_value() == 11) and total < 21:
                combos[f'soft_{total}'].append((card_1, card_2))
            else:
                combos[str(total)].append((card_1, card_2))
                
    return combos


def determine_best_action(row: pd.Series) -> pd.DataFrame:
    if 'split' in row.index and row['split'] > row['hit'] and row['split'] > row['stand'] and row['split'] > row['double']:
        return 'split'
    if row['double'] > row['hit'] and row['double'] > row['stand']:
        return 'double'
    elif row['hit'] > row['stand']:
        return 'hit'
    else:
        return 'stand'