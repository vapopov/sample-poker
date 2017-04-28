from collections import OrderedDict

__all__ = ('Hand', 'Card', 'CombinationError')


class Card(object):

    RANKS = ('2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')
    RANK_REPR = {'T': '10', 'J': 'Jack', 'Q': 'Queen', 'K': 'King', 'A': 'Ace'}
    SUITS = {'C': 'Clubs', 'D': 'Diamonds', 'H': 'Hearts', 'S': 'Spades'}

    def __init__(self, card):
        assert isinstance(card, str) and len(card) == 2, "Wrong card entity: '{}'".format(card)
        self._rank, self._suit = card.upper()
        assert self._rank in self.RANKS, "Wrong Rank of: {}".format(card)
        assert self._suit in self.SUITS.keys(), "Wrong Suit of: {}".format(card)

    @property
    def rank(self):
        return self._rank

    @property
    def suit(self):
        return self._suit

    @property
    def priority(self):
        return self.RANKS.index(self._rank)

    def __eq__(self, card):
        return self.rank == card.rank and self.suit == card.suit

    def __hash__(self):
        return hash(self._rank + self._suit)

    def __str__(self):
        return self._rank + self._suit


class _Cards(object):
    """
    Context class with prepared data for comparison of combinations
    """

    def __init__(self, cards):
        self._sorted_cards = sorted(cards, key=lambda _card: _card.priority)
        self._sorted_ranks = [card.rank for card in self._sorted_cards]
        self._similar_ranks = OrderedDict(
            [(card.priority, self.sorted_ranks.count(card.rank)) for card in self._sorted_cards]
        )

    @property
    def sorted_cards(self):
        """ List of sorted cards, from min to max
        :rtype: list[Card]
        """
        return self._sorted_cards

    @property
    def sorted_ranks(self):
        """ List of sorted ranks
        :rtype: list
        """
        return self._sorted_ranks

    @property
    def similar_ranks(self):
        """ Sorted ranks with the data qty of duplicates
        :rtype: dict
        """
        return self._similar_ranks

    def __str__(self):
        return ', '.join(map(str, self._sorted_cards))


class _Combination(object):

    _name = None

    def __init__(self, cards):
        assert self._name, "Combination must have a name"
        self._cards = cards

    @property
    def priority_list(self):
        """ Sorted list of priorities for current combination, uses for comparison
        :rtype: list[int]
        """
        return []

    def _match_suit(self):
        return True

    def _match_ranks(self):
        return True

    def match(self):
        return self._match_suit() and self._match_ranks()

    def __cmp__(self, other):
        assert self.__class__ == other.__class__, "You can only compare the same combinations"
        # We have to compare higher ranks first in priority list (must be reversed)
        self_priority, other_priority = self.priority_list, other.priority_list
        self_priority.reverse()
        other_priority.reverse()
        return cmp(self_priority, other_priority)

    def __str__(self):
        return self._name


class _Straight(_Combination):

    _name = 'Straight'

    def _match_ranks(self):
        # Check that priority is a sequence with step by 1
        sequence = [card.priority for card in self._cards.sorted_cards]
        return all([second - first == 1 for first, second in zip(sequence, sequence[1:])])

    @property
    def priority_list(self):
        return [self._cards.sorted_cards[-1].priority]


class _StraightFlush(_Straight):

    _name = 'Straight Flush'

    def _match_suit(self):
        return len(set([card.suit for card in self._cards.sorted_cards])) == 1


class _RoyalFlush(_StraightFlush):

    _name = 'Royal Flush'

    def _match_ranks(self):
        return self._cards.sorted_ranks == ['T', 'J', 'Q', 'K', 'A']


class _FourOfAKind(_Combination):

    _name = 'Four of a Kind'

    def _match_ranks(self):
        return self._cards.similar_ranks.values().count(4) == 1

    @property
    def priority_list(self):
        return sorted(self._cards.similar_ranks, key=self._cards.similar_ranks.__getitem__)


class _FullHouse(_Combination):

    _name = 'Full House'

    def _match_ranks(self):
        return len(set([card.rank for card in self._cards.sorted_cards])) == 2

    @property
    def priority_list(self):
        return sorted(self._cards.similar_ranks, key=self._cards.similar_ranks.__getitem__)


class _Flush(_Combination):

    _name = 'Flush'

    def _match_suit(self):
        return len(set([card.suit for card in self._cards.sorted_cards])) == 1

    @property
    def priority_list(self):
        return sorted([card.priority for card in self._cards.sorted_cards])


class _TreeOfAKind(_Combination):

    _name = 'Tree Of a Kind'

    def _match_ranks(self):
        return self._cards.similar_ranks.values().count(3) == 1

    @property
    def priority_list(self):
        return sorted(self._cards.similar_ranks, key=self._cards.similar_ranks.__getitem__)


class _TwoPair(_Combination):

    _name = 'Two Pair'

    def _match_ranks(self):
        return self._cards.similar_ranks.values().count(2) == 2

    @property
    def priority_list(self):
        return sorted(self._cards.similar_ranks, key=self._cards.similar_ranks.__getitem__)


class _OnePair(_Combination):

    _name = 'One Pair'

    def _match_ranks(self):
        return self._cards.similar_ranks.values().count(2) == 1

    @property
    def priority_list(self):
        return sorted(self._cards.similar_ranks, key=self._cards.similar_ranks.__getitem__)


class _HighCard(_Combination):

    _name = 'High Card'

    @property
    def priority_list(self):
        return sorted([card.priority for card in self._cards.sorted_cards])


class CombinationError(Exception):
    pass


class Hand(object):

    CARDS_QTY = 5

    COMBINATIONS = (_HighCard,
                    _OnePair,
                    _TwoPair,
                    _TreeOfAKind,
                    _Straight,
                    _Flush,
                    _FullHouse,
                    _FourOfAKind,
                    _StraightFlush,
                    _RoyalFlush)

    def __init__(self, card_list):
        assert filter(lambda card: isinstance(card, Card), card_list), "Wrong type of object, only Card is supported"
        assert len(card_list) == self.CARDS_QTY, "Cards can\'t be more or less than {}".format(self.CARDS_QTY)
        assert len(set(card_list)) == self.CARDS_QTY, "Cards can\'t be the equal: {}".format(map(str, card_list))
        self._cards = _Cards(card_list)
        self._combination = self.match_combination(self._cards)

    @classmethod
    def from_string(cls, cards):
        """ Initiate hand by string of cards list
        :type cards: str
        :rtype: list[Card]
        """
        assert isinstance(cards, str), "cards must be a string"
        return cls([Card(card) for card in cards.split()])

    @classmethod
    def match_combination(cls, cards):
        """ Get combination for current list of cards
        :type cards: _Cards
        :rtype: _Combination
        """
        for comb_cls in reversed(cls.COMBINATIONS):
            combination = comb_cls(cards)
            if combination.match():
                return combination

        raise CombinationError("Combination wasn't found")

    @property
    def combination(self):
        """ Current combination for a hand
        :rtype: _Combination
        """
        return self._combination

    @property
    def priority(self):
        """ Current priority of combination
        :rtype: int
        """
        return self.COMBINATIONS.index(self.combination.__class__)

    def __cmp__(self, other):
        assert isinstance(other, self.__class__), "Wrong comparison objects"

        if self.priority == other.priority:
            return cmp(self.combination, other.combination)

        return cmp(self.priority, other.priority)

    def __str__(self):
        return "<hand [{cards}], '{combination}'>".format(
            cards=self._cards,
            combination=self._combination
        )


if __name__ == '__main__':
    for hand in sorted([
        Hand.from_string('6D 3D 5d 4d 2D'),
        Hand.from_string('AS JS QS KS TS'),
        Hand.from_string('KD KS QS KC KH'),
        Hand.from_string('JD 8C 5D 3H TS'),
        Hand.from_string('5H 5C QD QC QS'),
        Hand.from_string('2D 3D 7D QD AD'),
        Hand.from_string('4D 5D 6D 7H 8D'),
        Hand.from_string('JD JC JH 5H 8D'),
        Hand.from_string('JD JC 5D 5H TS'),
        Hand.from_string('JD JC 5D AH TS'),
        Hand.from_string('JD AC 5D 3H TS'),
        Hand.from_string('JD JC JH 3H 8D'),
        Hand.from_string('QD TS QS 2C KH'),
        Hand.from_string('KD KS QS KC KH'),
        Hand.from_string('QD QS QH QC KH')
    ], reverse=True):
        print hand
