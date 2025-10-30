import os
import os
import psycopg2
from psycopg2 import extras
import pandas as pd
from dotenv import load_dotenv
import numpy as np

def create_table(conn):
    """Creates the blackjack_odds table using the schema.sql file."""
    with conn.cursor() as cur:
        print("Creating table from schema.sql...")
        with open('schema.sql', 'r') as f:
            # Drop the table if it exists to ensure a clean slate
            cur.execute("DROP TABLE IF EXISTS blackjack_odds;")
            cur.execute(f.read())
        print("Table 'blackjack_odds' created successfully.")
    conn.commit()

def parse_filename(filename):
    """Parses the CSV filename to extract game rules."""
    rules = {
        'dealer_hit_soft_17': False,
        'double_after_split': False,
        'blackjack_pays': 1.5,
        'surrender_allowed': True  # Based on generate_odds.py, this is always true
    }
    
    if 'hit_soft_17' in filename:
        rules['dealer_hit_soft_17'] = True
    if 'double_after_splitting' in filename or 'double_after_split' in filename:
        rules['double_after_split'] = True
    if '6-5' in filename:
        rules['blackjack_pays'] = 1.2 # 6/5
        
    return rules

def main():
    """Main function to load data from CSVs into the PostgreSQL database."""
    load_dotenv()
    db_conn_string = os.getenv("DATABASE_CONN_STRING")
    if not db_conn_string:
        print("Error: DATABASE_CONN_STRING environment variable not set.")
        return

    conn = None
    try:
        print("Connecting to the database...")
        conn = psycopg2.connect(db_conn_string)
        print("Database connection successful.")

        # create_table(conn)

        data_dir = 'data2'
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

        with conn.cursor() as cur:
            for csv_file in csv_files:
                print(f"Processing {csv_file}...")
                rules = parse_filename(csv_file)
                
                file_path = os.path.join(data_dir, csv_file)
                df = pd.read_csv(file_path)

                # Add rule columns
                df['dealer_hit_soft_17'] = rules['dealer_hit_soft_17']
                df['double_after_split'] = rules['double_after_split']
                df['blackjack_pays'] = rules['blackjack_pays']
                df['surrender_allowed'] = rules['surrender_allowed']

                # Rename columns to match DB schema
                df.rename(columns={
                    'double': 'double_ev',
                    'hit': 'hit_ev',
                    'stand': 'stand_ev',
                    'split': 'split_ev'
                }, inplace=True)
                
                # Ensure all required columns are present
                if 'split_ev' not in df.columns:
                    df['split_ev'] = np.nan

                # Reorder columns to match the table definition for insertion
                df = df[['player_total', 'dealer_card_up', 'double_ev', 'hit_ev', 'stand_ev', 'split_ev', 
                         'best_action', 'dealer_hit_soft_17', 'double_after_split', 'blackjack_pays', 'surrender_allowed']]

                # Convert DataFrame to list of tuples for insertion
                data_to_insert = [tuple(row) for row in df.itertuples(index=False)]

                # SQL INSERT statement
                insert_query = """
                INSERT INTO blackjack_odds (player_total, dealer_card_up, double_ev, hit_ev, stand_ev, split_ev, 
                                          best_action, dealer_hit_soft_17, double_after_split, blackjack_pays, surrender_allowed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_total, dealer_card_up, dealer_hit_soft_17, double_after_split, blackjack_pays, surrender_allowed) 
                DO UPDATE SET 
                double_ev = EXCLUDED.double_ev,
                hit_ev = EXCLUDED.hit_ev,
                stand_ev = EXCLUDED.stand_ev,
                split_ev = EXCLUDED.split_ev,
                best_action = EXCLUDED.best_action;
                """
                
                # Insert data row by row
                for record in data_to_insert:
                    cur.execute(insert_query, record)
                print(f"  -> Inserted {len(data_to_insert)} rows from {csv_file}.")

        conn.commit()
        print("\nAll data has been successfully loaded into the database.")

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    main()
