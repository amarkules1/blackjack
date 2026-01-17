import pandas as pd
import blackjack_utils.game_config as gc
import blackjack_utils.shoe as shoe
from blackjack_utils.utils import simulate_hand

import multiprocessing
import time

OUTPUT_FILE_NAME = 'data2/6-5_hit_soft_17_odds.csv' 
DEALER_HIT_SOFT_17 = True
DOUBLE_AFTER_SPLIT = False
SURRENDER_ALLOWED = True
BLACKJACK_PAYS = 6/5

SAMPLE_SIZE = 4_000_000

def run_simulation_batch(batch_size, game_config, data):
    """Runs a batch of simulations and returns the total outcome."""
    local_outcomes = 0.0
    for _ in range(batch_size):
        deck = shoe.Shoe(6)
        deck.shuffle()
        player_cards = [deck.draw(), deck.draw()]
        dealer_card_up = deck.draw()
        local_outcomes += simulate_hand(game_config, player_cards, dealer_card_up, deck, data)
    return local_outcomes

if __name__ == '__main__':
    data = pd.read_csv(OUTPUT_FILE_NAME, dtype={'dealer_card_up': str})
    game_config = gc.GameConfig(
        decks_in_shoe=6, 
        dealer_hit_soft_17=DEALER_HIT_SOFT_17, 
        double_after_split=DOUBLE_AFTER_SPLIT, 
        surrender_allowed=SURRENDER_ALLOWED, 
        blackjack_pays=BLACKJACK_PAYS
    )

    num_processes = multiprocessing.cpu_count()
    batch_size = SAMPLE_SIZE // num_processes
    
    # Handle any remainder
    batch_sizes = [batch_size] * num_processes
    batch_sizes[-1] += SAMPLE_SIZE % num_processes

    # Prepare arguments for each process
    # Note: passing large dataframes can be slow due to pickling, but for this size it should be fine.
    # Alternatively, we could load data inside the worker if it was read-only and loaded from disk, 
    # but here we pass it.
    args = [(b, game_config, data) for b in batch_sizes]

    start_time = time.time()
    print(f"Starting simulation at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    print(f"Running {SAMPLE_SIZE:,} simulations across {num_processes} processes.")
    print(f"Target simulations per process: {batch_size:,} (last process takes remainder: {batch_sizes[-1]:,})")

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.starmap(run_simulation_batch, args)

    total_outcomes = sum(results)
    print(f"Result: {total_outcomes / SAMPLE_SIZE}")
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Finished at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    print(f"Total duration: {duration:.2f} seconds")