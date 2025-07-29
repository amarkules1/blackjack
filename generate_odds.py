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

def simulate_stand_worker(args):
    """Worker function for stand simulation"""
    num_iterations, dealer_card_up, base_deck, player_cards, game_config = args
    local_results = []
    for _ in range(num_iterations):
        deck_copy = shoe.Shoe(6)
        deck_copy.cards = base_deck.cards.copy()
        deck_copy.shuffle()
        dealer_cards = [dealer_card_up, deck_copy.draw()]
        result = game_config.evaluate(player_cards, dealer_cards, deck_copy)
        local_results.append(result)
    return local_results

def simulate_hit_worker(args):
    """Worker function for hit/double simulation"""
    num_iterations, dealer_card_up, base_deck, player_cards, game_config = args
    local_results = []
    local_results_double = []
    for _ in range(num_iterations):
        deck_copy = shoe.Shoe(6)
        deck_copy.cards = base_deck.cards.copy()
        deck_copy.shuffle()
        dealer_cards = [dealer_card_up, deck_copy.draw()]
        player_cards_copy = player_cards.copy()
        player_cards_copy.append(deck_copy.draw())
        result = game_config.evaluate(player_cards_copy, dealer_cards, deck_copy)
        local_results.append(result)
        local_results_double.append(result * 2)
    return local_results, local_results_double

def simulate_player_total_worker(args):
    """Worker function for player total simulation"""
    num_iterations, dealer_card_rank, combos_for_total, game_config, data_hit, data_double, data_stand = args
    local_hit_total = 0
    local_double_total = 0
    local_stand_total = 0
    
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
    
    return (local_hit_total, local_double_total, local_stand_total)

def main():
    print("Starting odds generation...")
    start_time = time.time()
    num_threads = 12
    iterations_per_thread = 400_000 // num_threads

    data = pd.DataFrame(columns=['player_total', 'action', 'dealer_card_up', 'expected_value'])
    player_cards = [card.Card().from_ints(11, 0), card.Card().from_ints(10, 0)]

    game_config = gc.GameConfig(6, True, True, True, 1.5)

    # stand 
    print("\nStarting STAND simulations...")
    stand_start_time = time.time()
    for i in list(range(9)) + [12]:
        dealer_card_up = card.Card().from_ints(i, 0)
        deck = shoe.Shoe(6)
        deck.remove(player_cards[0])
        deck.remove(player_cards[1])
        deck.remove(dealer_card_up)
        
        pool_args = [(iterations_per_thread, dealer_card_up, deck, player_cards, game_config) for _ in range(num_threads)]

        with multiprocessing.Pool(processes=num_threads) as pool:
            results = pool.map(simulate_stand_worker, pool_args)

        all_results = []
        for res in results:
            all_results.extend(res)
        
        mean = sum(all_results) / len(all_results)
        data = pd.concat([data, pd.DataFrame({'player_total': [game_config.score_hand(player_cards)], 'action': ['stand'], 'dealer_card_up': [dealer_card_up.get_card_value()], 'expected_value': [mean]})], ignore_index=True)
        print(f"Completed stand simulation for dealer card {dealer_card_up.get_card_value()}")

    stand_end_time = time.time()
    print(f"STAND simulations completed in {stand_end_time - stand_start_time:.2f} seconds\n")

    # hit/double 
    print("Starting HIT/DOUBLE simulations...")
    hit_start_time = time.time()
    for i in list(range(9)) + [12]:
        dealer_card_up = card.Card().from_ints(i, 0)
        deck = shoe.Shoe(6)
        deck.remove(player_cards[0])
        deck.remove(player_cards[1])
        deck.remove(dealer_card_up)
        
        pool_args = [(iterations_per_thread, dealer_card_up, deck, player_cards, game_config) for _ in range(num_threads)]

        with multiprocessing.Pool(processes=num_threads) as pool:
            results = pool.map(simulate_hit_worker, pool_args)

        all_results = []
        all_results_double = []
        for res_hit, res_double in results:
            all_results.extend(res_hit)
            all_results_double.extend(res_double)
        
        mean = sum(all_results) / len(all_results)
        mean_double = sum(all_results_double) / len(all_results_double)
        data = pd.concat([data, pd.DataFrame({'player_total': [game_config.score_hand(player_cards)], 'action': ['hit'], 'dealer_card_up': [dealer_card_up.get_card_value()], 'expected_value': [mean]})], ignore_index=True)
        data = pd.concat([data, pd.DataFrame({'player_total': [game_config.score_hand(player_cards)], 'action': ['double'], 'dealer_card_up': [dealer_card_up.get_card_value()], 'expected_value': [mean_double]})], ignore_index=True)
        print(f"Completed hit/double simulation for dealer card {dealer_card_up.get_card_value()}")

    hit_end_time = time.time()
    print(f"HIT/DOUBLE simulations completed in {hit_end_time - hit_start_time:.2f} seconds\n")

    print("Processing results...")
    data.sort_values(by=['player_total', 'dealer_card_up', 'action'])
    data = data.pivot_table(index=['player_total', 'dealer_card_up'], columns='action', values='expected_value')
    data['player_total'] = data.index.get_level_values(0)
    data['dealer_card_up'] = data.index.get_level_values(1)
    data.reset_index(drop=True, inplace=True)
    data['best_action'] = data.apply(determine_best_action, axis=1)
    data['player_total'] = data['player_total'].astype(str)
    data['dealer_card_up'] = data['dealer_card_up'].astype(str)

    print("\nStarting PLAYER TOTALS simulations...")
    player_totals_start_time = time.time()

    combos = build_combos()
    # now do it for 19-12
    for player_amt in ['19', '18', '17', '16', '15', '14', '13', '12', '11', '10',
                    'soft_20', 'soft_19', 'soft_18', 'soft_17', 'soft_16', 'soft_15', 'soft_14', 'soft_13', 
                    '9', '8', '7', '6', '5',
                    'paired_18', 'paired_16', 'paired_14', 'paired_12', 'paired_10', 'paired_8', 'paired_6', 'paired_4', 'paired_aces']:
        print(f"Processing player total {player_amt}...")
        player_total_start = time.time()
        
        data_stand = data.copy()
        data_stand['player_total'] = player_amt
        data_stand.drop_duplicates(subset=['player_total', 'dealer_card_up'], inplace=True)
        data_stand['best_action'] = 'stand'
        data_double = data_stand.copy()
        data_double['best_action'] = 'double'
        data_hit = data_double.copy()
        data_hit['best_action'] = 'hit'
        
        data_stand = pd.concat([data, data_stand], ignore_index=True)
        data_double = pd.concat([data, data_double], ignore_index=True)
        data_hit = pd.concat([data, data_hit], ignore_index=True)
        
        combos_for_total = combos[player_amt]
        game_config = gc.GameConfig(6, True, True, True, 1.5)
        
        for dealer_card_rank in list(range(9)) + [12]:
            pool_args = [(iterations_per_thread, dealer_card_rank, combos_for_total, game_config, data_hit, data_double, data_stand) for _ in range(num_threads)]

            with multiprocessing.Pool(processes=num_threads) as pool:
                results = pool.map(simulate_player_total_worker, pool_args)

            hit_total = 0
            double_total = 0
            stand_total = 0
            for res_hit, res_double, res_stand in results:
                hit_total += res_hit
                double_total += res_double
                stand_total += res_stand
            
            total_iterations = num_threads * iterations_per_thread
            data = pd.concat([data, pd.DataFrame({'player_total': [str(player_amt)], 'dealer_card_up': [str(card.Card().from_ints(dealer_card_rank, 0).get_card_value())], 'double': [double_total/total_iterations], 'hit': [hit_total/total_iterations], 'stand': [stand_total/total_iterations]})], ignore_index=True)
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
    print(f"Stand simulations: {stand_end_time - stand_start_time:.2f} seconds")
    print(f"Hit/Double simulations: {hit_end_time - hit_start_time:.2f} seconds")
    print(f"Player totals simulations: {player_totals_end_time - player_totals_start_time:.2f} seconds")
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Results saved to odds.csv")

if __name__ == '__main__':
    main()