from blackjack_utils.card import Card
from blackjack_utils.deck import Deck

import random


class Shoe(Deck):
    def __init__(self, decks_in_shoe=6):
        """
        :param decks_in_shoe: the number of 52 card decks in the shoe
        Initializes a shoe comprised of a number of 52 card decks
        """
        self.cards = []
        for i in range(decks_in_shoe):
            for suit in [0, 1, 2, 3]:
                for value in range(0, 13):
                    self.cards.append(Card().from_ints(value, suit))

    def shuffle(self):
        """
        Shuffles the deck randomly
        :return:
        """
        random.shuffle(self.cards)

    def draw(self):
        """
        Removes a card from the deck and returns it
        :return: the card drawn
        """
        return self.cards.pop()

    def remove(self, card):
        """
        Removes a specific card from the deck
        :param card: the card to be removed
        :return:
        """
        self.cards.remove(card)

    def __len__(self):
        return len(self.cards)

    def __str__(self):
        return str([str(card) for card in self.cards])
