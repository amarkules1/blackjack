from typing import List
from card import Card
from shoe import Shoe

class GameConfig:
    decks_in_shoe = 6
    dealer_hit_soft_17 = True
    double_after_split = True
    surrender_allowed = True
    blackjack_pays = 1.5
    #probably more to add later
    
    def __init__(self, decks_in_shoe=6, dealer_hit_soft_17=True, double_after_split=True, surrender_allowed=True, blackjack_pays=1.5):
        self.decks_in_shoe = decks_in_shoe
        self.dealer_hit_soft_17 = dealer_hit_soft_17
        self.double_after_split = double_after_split
        self.surrender_allowed = surrender_allowed
        self.blackjack_pays = blackjack_pays
    
    def evaluate(self, player_final_hand: List[Card], dealer_hand: List[Card], remaining_shoe: Shoe):
        """
        :param player_final_hand (List[Card]): the final hand of the player
        :param dealer_hand (List[Card]): the 2 cards of the dealer (before dealer play)
        :param remaining_shoe (Shoe): the remaining cards in the shoe (after player play)
        :return float: the result of the game (-1 for loss, 0 for push, 1 for win, blackjack_pays amount for blackjack)
        """
        # hit for dealer
        while self.does_dealer_hit(dealer_hand):
            dealer_hand.append(remaining_shoe.draw())
        
        #pay out blackjack
        if self.hand_is_blackjack(player_final_hand):
            if self.hand_is_blackjack(dealer_hand):
                return 0
            return self.blackjack_pays
        
        # score hands
        player_score = self.score_hand(player_final_hand)
        dealer_score = self.score_hand(dealer_hand)
        
        if player_score > 21:
            return -1
        if dealer_score > 21:
            return 1
        if player_score > dealer_score:
            return 1
        if player_score < dealer_score:
            return -1
        return 0
    
    def score_hand(self, hand: List[Card]):
        # sum of cards with ace as 11
        hand_value = sum(card.get_card_value() for card in hand)
        # number of aces
        num_aces = sum(1 for card in hand if card.rank == 12)
        # adjust for aces
        while hand_value > 21 and num_aces > 0:
            hand_value -= 10
            num_aces -= 1
        return hand_value
    
    def does_dealer_hit(self, hand: List[Card]):
        dealer_hand_score = self.score_hand(hand)
        if dealer_hand_score < 17:
            return True
        if dealer_hand_score > 17:
            return False
        
    def is_soft_17(self, hand: List[Card]):
        hand_value = sum(card.get_card_value() for card in hand)
        num_aces = sum(1 for card in hand if card.rank == 12)
        while hand_value > 21 and num_aces > 0:
            hand_value -= 10
            num_aces -= 1
        return hand_value == 17 and num_aces > 0
    
    def hand_is_blackjack(self, hand: List[Card]):
        return len(hand) == 2 and self.score_hand(hand) == 21