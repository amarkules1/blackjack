import pandas as pd
import blackjack_utils.game_config as gc
import blackjack_utils.shoe as shoe
from blackjack_utils.utils import simulate_hand

OUTPUT_FILE_NAME = 'data2/standard_hit_soft_17_odds.csv'
DEALER_HIT_SOFT_17 = True
DOUBLE_AFTER_SPLIT = False
SURRENDER_ALLOWED = True
BLACKJACK_PAYS = 1.5

SAMPLE_SIZE = 100_000

data = pd.read_csv(OUTPUT_FILE_NAME, dtype={'dealer_card_up': str})
game_config = gc.GameConfig(decks_in_shoe=6, dealer_hit_soft_17=DEALER_HIT_SOFT_17, double_after_split=DOUBLE_AFTER_SPLIT, surrender_allowed=SURRENDER_ALLOWED, blackjack_pays=BLACKJACK_PAYS)

outcomes = 0.0
for i in range(SAMPLE_SIZE):
    deck = shoe.Shoe(6)
    deck.shuffle()
    player_cards = [deck.draw(), deck.draw()]
    dealer_card_up = deck.draw()
    outcomes += simulate_hand(game_config, player_cards, dealer_card_up, deck, data)

print(outcomes / SAMPLE_SIZE)