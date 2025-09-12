CREATE TABLE blackjack_odds (
    id SERIAL PRIMARY KEY,
    player_total VARCHAR(20) NOT NULL,
    dealer_card_up VARCHAR(10) NOT NULL,
    double_ev FLOAT,
    hit_ev FLOAT,
    stand_ev FLOAT,
    split_ev FLOAT,
    best_action VARCHAR(10),
    dealer_hit_soft_17 BOOLEAN NOT NULL,
    double_after_split BOOLEAN NOT NULL,
    blackjack_pays FLOAT NOT NULL,
    surrender_allowed BOOLEAN NOT NULL,
    UNIQUE (player_total, dealer_card_up, dealer_hit_soft_17, double_after_split, blackjack_pays, surrender_allowed)
);
