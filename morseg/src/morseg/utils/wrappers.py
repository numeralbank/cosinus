from __future__ import annotations

from collections import defaultdict
from csv import DictReader
from linse.typedsequence import Word, Morpheme


class WordWrapper(Word):
    def __init__(self, tokens, **kwargs):
        if type(tokens) is WordWrapper:
            self.gold_segmented = tokens.gold_segmented
            self.unsegmented = tokens.unsegmented
            self.num_tokens = len(self.unsegmented[0])
            super().__init__(tokens, **kwargs)
        else:
            self.gold_segmented = Word(tokens)
            self.unsegmented = Word(sum(self.gold_segmented))
            self.num_tokens = len(self.unsegmented[0])
            super().__init__(sum(self.gold_segmented), **kwargs)

    def copy(self) -> WordWrapper:
        return WordWrapper(self)

    def update(self, other):
        super().__init__(other)

    def split(self, index):
        """
        adds a morpheme boundary at given index.
        :param index: index to add the morpheme boundary
        :param wp_token: the special token for the WordPiece algorithm
        """

        # TODO add error/warning when index is out of bounds?

        if self.has_split_at(index) or index < 1 or index >= self.num_tokens:
            return

        i = 0
        for j, morpheme in enumerate(self):
            for k in range(len(morpheme)):
                if i == index:
                    left, right = morpheme[:k], morpheme[k:]
                    self.pop(j)
                    self.insert(j, right)
                    self.insert(j, left)
                i += 1

    def has_split_at(self, index):
        counter = 0
        for i, m in enumerate(self):
            counter += len(m)
            if counter == index and i != (len(self) - 1):
                return True

        return False

    def get_splits(self, ignore_token=None):
        splits = []

        i = 0
        for m in self:
            if ignore_token:
                m = Morpheme(m)
                while ignore_token in m:
                    m.remove(ignore_token)
            i += len(m)
            splits.append(i)

        return splits[:-1]

    def get_gold_splits(self):
        splits = []

        i = 0
        for m in self.gold_segmented:
            i += len(m)
            splits.append(i)

        return splits[:-1]

    def merge(self, left, right, wp_token=None):
        i = 0
        while i < (len(self) - 1):
            m1 = self[i]
            m2 = self[i + 1]
            if m1 == left and m2 == right:
                if wp_token and wp_token in m2:
                    m2 = Morpheme(m2)  # copy object to avoid manipulation of underlying eval-data
                    m2.remove(wp_token)
                self.pop(i)  # remove left
                self.pop(i)  # remove right
                self.insert(i, m1 + m2)
            i += 1

    def remove_split(self, index):
        if not self.has_split_at(index):
            return

        counter = 0
        for i in range(len(self) - 1):
            left = self[i]
            right = self[i + 1]
            counter += len(left)
            if counter == index:
                self.pop(i)  # remove left
                self.pop(i)  # remove right
                self.insert(i, left + right)
                break

    def split_everywhere(self):
        """
        Insert a morpheme boundary between all tokens.
        Preprocessing method used by bottom-up joining models like BPE or WordPiece.
        """
        for i in range(1, self.num_tokens):
            self.split(i)

    def add_wp_token(self, wp_token="##"):
        for i in range(1, len(self)):
            self[i].insert(0, wp_token)

    def remove_wp_token(self, wp_token="##"):
        for i in range(1, len(self)):
            if wp_token in self[i]:
                self[i].remove(wp_token)

    def __eq__(self, other):
        if type(other) is not WordWrapper:
            return False

        return super().__eq__(other) and self.gold_segmented == other.gold_segmented

    def __hash__(self):
        return hash(repr(self))


class WordlistWrapper(list):
    def __init__(self, forms):
        """
        Wraps forms into WordWrapper objects. Forms are expected to be already sanitized (not containing slash notation,
            gap symbols, etc.)
        :param forms: the forms of the wordlist as a list of either strings or iterable segments.
        """
        if not all(type(f) is WordWrapper for f in forms):
            forms = [WordWrapper(f) for f in forms]
        self.form_dict = {f.unsegmented: f for f in forms}
        super().__init__(forms)

    def copy(self) -> WordlistWrapper:
        return WordlistWrapper([word.copy() for word in self])

    def __getitem__(self, item):
        if type(item) is Word:
            return self.form_dict.get(item)

        return super().__getitem__(item)

    def unsegmented(self):
        for form in self:
            yield form.unsegmented

    def gold_segmented(self):
        for form in self:
            yield form.gold_segmented

    def merge(self, left, right, wp_token=None):
        for x in self:
            x.merge(left, right, wp_token=wp_token)

    def split_everywhere(self):
        for x in self:
            x.split_everywhere()

    def add_wp_token(self, wp_token="##"):
        for x in self:
            x.add_wp_token(wp_token=wp_token)

    def remove_wp_token(self, wp_token="##"):
        for x in self:
            x.remove_wp_token(wp_token=wp_token)

    def unigram_counts(self):
        vocabulary = defaultdict(int)
        for form in self:
            for m in form:
                vocabulary[m] += 1

        return vocabulary

    def bigram_counts(self):
        vocabulary = defaultdict(int)
        for form in self:
            for i in range(len(form) - 1):
                pair = (form[i], form[i+1])
                vocabulary[pair] += 1

        return vocabulary

    def f1_score(self, ignore_token=None):
        """
        Calculate precision, recall and f1 score as defined in Virpioja et al. (2011)
        """
        pred_splits = [form.get_splits(ignore_token=ignore_token) for form in self]
        gold_splits = [form.get_gold_splits() for form in self]
        correct_splits = [set(pred) & set(gold) for pred, gold in zip(pred_splits, gold_splits)]

        pred_total = sum(len(x) for x in pred_splits)
        gold_total = sum(len(x) for x in gold_splits)
        correct_total = sum(len(x) for x in correct_splits)

        precision = correct_total / pred_total if pred_total > 0 else 0.0
        recall = correct_total / gold_total if gold_total > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return f1, precision, recall

    @classmethod
    def from_file(cls, fp, col_name="TOKENS", delimiter="\t", underlying=False):
        forms = []

        with open(fp) as f:
            reader = DictReader(f, delimiter=delimiter)
            for line in reader:
                form = line[col_name]
                if form and form not in forms:
                    forms.append(form)

        forms = cls.preprocess(forms, underlying=underlying)

        return cls(forms)

    @classmethod
    def preprocess(cls, forms, morpheme_separator=Word.item_separator, underlying=False):
        preprocessed_forms = []

        idx = 1 if underlying else 0

        for f in forms:
            # each form is a string segmented by whitespaces, such as 'a b + c'
            word = []
            morphemes = f.split(morpheme_separator)
            for m in morphemes:
                m = m.split()
                # resolve slash notation: only take part left (or right, underlying) of the slash, ignore if it is a gap symbol
                clean_morpheme = []
                for segment in m:
                    if "/" in segment:
                        segment = segment.split("/")[idx]
                        if segment == "-":
                            continue
                    clean_morpheme.append(segment)
                word.append(clean_morpheme)
            preprocessed_forms.append(word)

        return preprocessed_forms


if __name__ == "__main__":
    ################################
    # ad hoc testing - WordWrapper #
    ################################

    w = WordWrapper([["a", "b", "c"], ["a"], ["b"]])
    for i in range(1, len(w[0])):
        w.split(i)
        print(w)
    w.merge(Morpheme(["a"]), Morpheme(["b"]))
    print(w)
    print(w.has_split_at(0))  # False
    print(w.has_split_at(2))  # True
    print(w.has_split_at(4))  # False
    print(w.has_split_at(5))  # False

    ####################################
    # ad hoc testing - WordlistWrapper #
    ####################################

    wl = w = WordlistWrapper(
        [
            [["a", "b", "c"], ["a"], ["b"]],
            [["d", "e"], ["g"]]
        ]
    )

    for x in wl:
        print(x)

    for x in wl.gold_segmented():
        print(x)

    wl[0].split(1)
    wl[0].split(2)
    wl[0].split(3)
    wl[0].split(4)

    print(wl[0])

    wl.merge(Morpheme(["a"]), Morpheme(["b"]))
    print(wl[0])
