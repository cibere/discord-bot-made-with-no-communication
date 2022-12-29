
import random


class Card_Deck():
    """52 Playing Card Deck"""

    def __init__(self, shuffle_count: int = 1, use_Joker: bool = False) -> list:
        self._Deck = []

        self._Card_Suites = ['Diamonds', 'Clubs', 'Spades', 'Hearts']
        self._Face_Cards = ['Ace', 'Jack', 'Queen', 'King']
        self._Number_Cards = [str(num) for num in range(2, 11)]
        self._make_Deck(joker=use_Joker)
        self._shuffle(shuffle_count)
        return self._Deck

    def _make_Deck(self, joker: bool) -> dict[str, str]:
        """Creates a Dictionary with a 52 card Deck."""
        print(f'Making a 52 card deck, {"with" if joker else "without"}')
        for suite in self._Card_Suites:
            for fcard in self._Face_Cards:
                self._Deck.append({'Suite': suite, 'Card': fcard})

            for numcard in self._Number_Cards:
                self._Deck.append({'Suite': suite, 'Card': numcard})

        if joker:
            self._Deck.append({'Suite': None, 'Card': 'Joker'})

        return self._Deck

    def _shuffle(self, count: int = 1) -> dict[str, str]:
        """Shuffles the Deck"""
        print(f'Shuffling the Deck {count} {"times" if count > 1 else "time"}')
        while (count > 0):
            random.shuffle(self._Deck)
            count -= 1

    def _draw_Cards(self, count: int= 1) -> dict[str, str]:
        """Draw `count` number of cards."""
        print(f'Drawing {count} {"cards" if count > 1 else "card"}')
        return self._Deck[-count:]
    

    


