import pandas as pd
import blackjack_utils.game_config as gc
import blackjack_utils.shoe as shoe
import blackjack_utils.card as card
import random
import blackjack_utils.deck as deck
from blackjack_utils.utils import simulate_hand, build_combos, determine_best_action
import threading
import multiprocessing
import time

def simulate_player_total_worker(args):
    """Worker function for player total simulation"""
    num_iterations, dealer_card_rank, combos_for_total, game_config, data_hit, data_double, data_stand, data_split = args
    local_hit_total = 0
    local_double_total = 0
    local_stand_total = 0
    local_split_total = 0
    
    for _ in range(num_iterations):
        deck = shoe.Shoe(6)
        deck.shuffle()
        player_cards = list(random.choice(combos_for_total))
        dealer_card_up = card.Card().from_ints(dealer_card_rank, 0)
        deck.remove(player_cards[0])
        deck.remove(player_cards[1])
        deck.remove(dealer_card_up)
        local_hit_total += simulate_hand(game_config, player_cards, dealer_card_up, deck, data_hit)
        local_double_total += simulate_hand(game_config, player_cards, dealer_card_up, deck, data_double)
        local_stand_total += simulate_hand(game_config, player_cards, dealer_card_up, deck, data_stand)
        local_split_total += simulate_hand(game_config, player_cards, dealer_card_up, deck, data_split)
    
    return (local_hit_total, local_double_total, local_stand_total, local_split_total)

def main():
    print("Starting odds generation...")
    start_time = time.time()
    num_threads = 12
    iterations_per_thread = 50_000 // num_threads
    player_totals_start_time = time.time()

    game_config = gc.GameConfig(6, True, True, True, 1.5)

    # stand 
    data = pd.read_csv('odds.csv')
    data['player_total'] = data['player_total'].astype(str)
    data['dealer_card_up'] = data['dealer_card_up'].astype(str)
    data = data[~data['player_total'].str.startswith('paired')]

    combos = build_combos()
    # now do it for 19-12
    for player_amt in ['paired_18', 'paired_16', 'paired_14', 'paired_12', 'paired_10', 'paired_8', 'paired_6', 'paired_4', 'paired_aces']:
        print(f"Processing player total {player_amt}...")
        player_total_start = time.time()
        
        data_stand = data[data['player_total'] == '20'].copy()
        data_stand['player_total'] = player_amt
        data_stand.drop_duplicates(subset=['player_total', 'dealer_card_up'], inplace=True)
        data_stand['best_action'] = 'stand'
        data_double = data_stand.copy()
        data_double['best_action'] = 'double'
        data_hit = data_double.copy()
        data_hit['best_action'] = 'hit'
        data_split = data_hit.copy()
        data_split['best_action'] = 'split'
        
        data_stand = pd.concat([data, data_stand], ignore_index=True)
        data_double = pd.concat([data, data_double], ignore_index=True)
        data_hit = pd.concat([data, data_hit], ignore_index=True)
        data_split = pd.concat([data, data_split], ignore_index=True)
        
        combos_for_total = combos[player_amt]
        game_config = gc.GameConfig(6, True, True, True, 1.5)
        
        for dealer_card_rank in list(range(9)) + [12]:
            pool_args = [(iterations_per_thread, dealer_card_rank, combos_for_total, game_config, data_hit, data_double, data_stand, data_split) for _ in range(num_threads)]

            with multiprocessing.Pool(processes=num_threads) as pool:
                results = pool.map(simulate_player_total_worker, pool_args)

            hit_total = 0
            double_total = 0
            stand_total = 0
            split_total = 0
            for res_hit, res_double, res_stand, res_split in results:
                hit_total += res_hit
                double_total += res_double
                stand_total += res_stand
                split_total += res_split
            
            total_iterations = num_threads * iterations_per_thread
            data = pd.concat([data, pd.DataFrame({'player_total': [str(player_amt)], 'dealer_card_up': [str(card.Card().from_ints(dealer_card_rank, 0).get_card_value())], 'double': [double_total/total_iterations], 'hit': [hit_total/total_iterations], 'stand': [stand_total/total_iterations], 'split': [split_total/total_iterations]})], ignore_index=True)
            data['best_action'] = data.apply(determine_best_action, axis=1)
            print(f"  Completed dealer card {card.Card().from_ints(dealer_card_rank, 0).get_card_value()}")
        
        player_total_end = time.time()
        print(f"Player total {player_amt} completed in {player_total_end - player_total_start:.2f} seconds")
            
    data.to_csv('odds.csv', index=False)

    player_totals_end_time = time.time()
    print(f"\nPLAYER TOTALS simulations completed in {player_totals_end_time - player_totals_start_time:.2f} seconds\n")

    end_time = time.time()
    total_time = end_time - start_time
    print(f"\n=== TIMING SUMMARY ===")
    print(f"Player totals simulations: {player_totals_end_time - player_totals_start_time:.2f} seconds")
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Results saved to odds.csv")

if __name__ == '__main__':
    main()