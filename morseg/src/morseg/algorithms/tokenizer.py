"""
Tokenizers are methods that work with pure wordlists.
"""
import math

from typing import List
import random
from linse.typedsequence import Word, Morpheme
from morseg.utils.wrappers import WordWrapper, WordlistWrapper
from morseg.datastruct import Trie

import collections

try:
    import morfessor
except ImportError:
    morfessor = False


class Tokenizer:

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def _copy_forms(self, words: WordlistWrapper):
        self.forms = words.copy()

    def _preprocess(self, **kwargs):
        self.training_data = self.forms

    def _train(self, **kwargs):
        pass

    def _postprocess(self):
        pass

    def train(
            self,
            words: WordlistWrapper,
            **kwargs):
        self._copy_forms(words)
        self._preprocess(**kwargs)
        self._train(**kwargs)
        self._postprocess()

    def _tokenize(self, word, **kwargs):
        return self.forms[word]

    def __call__(self, word: Word, **kwargs) -> Word:
        return self._tokenize(word, **kwargs)

    def tokenize(
            self,
            words: List[Word],
            **kwargs
    ):
        for word in words:
            yield self(word, **kwargs)

    def get_segmentations(self):
        for form in self.forms:
            yield form


class RandomTokenizer(Tokenizer):
    """
    Tokenize words randomly.

    Notes
    -----
    This tokenizer proceeds in a very simple fashion by using one parameter
    that decides about the splitting of a word into morphemes. This parameter
    decides about the maximum number of break points in relation to a word.
    """

    def __init__(self, morpheme_ratio=0.5):
        Tokenizer.__init__(self, morpheme_ratio=morpheme_ratio)

    def _tokenize(self, word: Word, **kwargs):
        # get number of break points
        new_word = []
        for morpheme in word:
            new_word += list(morpheme)
        idxs = list(range(len(new_word)))
        break_point_number = random.randint(
            0,
            int((len(new_word) - 2) * self.kwargs["morpheme_ratio"] + 0.5))
        break_points = random.sample(idxs[1:-1], break_point_number)
        out = Word([""])
        for i in range(len(new_word)):
            if i in break_points:
                out.append(new_word[i])
            else:
                out[-1].append(new_word[i])
        return out


class PairEncoding(Tokenizer):
    """

    Notes
    -----
    Code taken with modifications from https://www.geeksforgeeks.org/byte-pair-encoding-bpe-in-nlp/
    """

    def __init__(self, **kwargs):
        Tokenizer.__init__(self, **kwargs)

    def _preprocess(self, **kwargs):
        self.training_data = self.forms
        self.training_data.split_everywhere()

    def _train(
            self,
            iterations=60,
            threshold=3,
            **kwargs
    ):
        callbacks = kwargs.get("callbacks")
        if callbacks:
            self.training_history = collections.defaultdict(list)

        # merge most frequent bigram
        for _ in range(iterations):
            pairs = self.training_data.bigram_counts()
            if len(pairs) == 0:
                break
            best_pair = max(pairs, key=pairs.get)
            if pairs[best_pair] < threshold:
                break
            self.training_data.merge(*best_pair)

            # update training history
            if callbacks:
                if "alphabet_size" in callbacks:
                    self.training_history["alphabet_size"].append(len(self.training_data.unigram_counts()))
                if "f1" in callbacks:
                    f1, precision, recall = self.training_data.f1_score()
                    self.training_history["f1"].append(f1)
                    self.training_history["precision"].append(precision)
                    self.training_history["recall"].append(recall)


class WordPiece(Tokenizer):
    def _preprocess(self, wp_prefix="##", **kwargs):
        self.training_data = self.forms
        self.training_data.split_everywhere()
        if wp_prefix:
            self.training_data.add_wp_token(wp_token=wp_prefix)

    def _train(self, iterations=60, threshold=0, wp_prefix="##", **kwargs):
        alphabet = self.training_data.unigram_counts()

        callbacks = kwargs.get("callbacks")
        if callbacks:
            self.training_history = collections.defaultdict(list)

        for _ in range(iterations):
            # count bigram frequencies
            bigram_freq = self.training_data.bigram_counts()

            # get pair with best score
            best_score = 0.0
            best_pair = None
            best_pair_freq = 0

            for pair, freq in bigram_freq.items():
                s1, s2 = pair
                score = freq / (alphabet[s1] * alphabet[s2])
                if score > best_score:
                    best_score = score
                    best_pair = pair
                    best_pair_freq = freq

            # stop merging if no score exceeds the threshold, or if there is nothing left to merge
            if best_score < threshold or not best_pair:
                break

            # update alphabet frequencies
            best_first, best_second = best_pair
            alphabet[best_first] -= best_pair_freq
            alphabet[best_second] -= best_pair_freq

            # remove special prefix from second part, add merged pair to the alphabet
            stripped_second = best_second.copy()
            if wp_prefix:
                stripped_second.remove(wp_prefix)
            alphabet[best_first + stripped_second] = best_pair_freq

            self.training_data.merge(best_first, best_second, wp_token=wp_prefix)

            # update training history
            if callbacks:
                if "alphabet_size" in callbacks:
                    alphabet_size = len([x for x in alphabet if alphabet[x] > 0])
                    self.training_history["alphabet_size"].append(alphabet_size)
                if "f1" in callbacks:
                    f1, precision, recall = self.training_data.f1_score(ignore_token=wp_prefix)
                    self.training_history["f1"].append(f1)
                    self.training_history["precision"].append(precision)
                    self.training_history["recall"].append(recall)

        # remove special prefix token from vocabulary
        if wp_prefix:
            self.training_data.remove_wp_token(wp_token=wp_prefix)


class UnigramSentencePiece(Tokenizer):
    def __init__(self):
        super().__init__()

    def _preprocess(self, vocab_size=60, count_single_characters=False, **kwargs):
        super()._preprocess(**kwargs)
        self.vocab = collections.Counter()
        self.vocab_size = vocab_size
        self._create_ngrams()
        if not count_single_characters:
            self.vocab_size += len({x for x in self.vocab if len(x) == 1})
        self._compute_probs()
    
    def _create_ngrams(self):
        for word in self.training_data:
            word = word.unsegmented[0]
            for i in range(len(word)):
                for j in range(i + 1, len(word) + 1):
                    subword = word[i:j]
                    self.vocab[subword] += 1
        return self.vocab

    def _compute_probs(self):
        self.model = {}
        total_count = sum(self.vocab.values())
        for token in self.vocab:
            self.model[token] = -math.log((self.vocab[token]) / total_count)

    def _loss(self, segmentation):
        """
        calculate the negative log-likelihood for a given segmentation
        """
        score = 0
        for token in segmentation:
            if token in self.model:
                score += self.model[token]
            else:
                return math.inf

        return score
    
    def _score(self):
        """
        Calculates scores for each n-gram (with n > 1). Scores indicate how much the loss would increase when this
        n-gram would be removed from the vocabulary -- n-grams with high scores are therefore more important for the
        model.
        """
        scores = collections.defaultdict(float)
        for word in self.training_data:
            word = word.unsegmented[0]
            # get all segmentations for word, retrieve the lowest loss
            segmentations = self._segment_word(word)
            best_score = math.inf
            best_segmentation = None
            for s in segmentations:
                score = self._loss(s)
                if score < best_score:
                    best_score = score
                    best_segmentation = s
            # now calculate the best loss under the assumption that an n-gram is removed from the vocabulary
            for token in best_segmentation:
                valid_segmentations = [s for s in segmentations if token not in s]
                best_remaining_score = math.inf
                for s in valid_segmentations:
                    best_remaining_score = min(best_remaining_score, self._loss(s))
                scores[token] += best_remaining_score - best_score

        # a token that does not occur in any of the best segmentations has a score of 0
        return {token: scores[token] for token in self.vocab if len(token) > 1}

    def _log_likelihood(self):
        return sum([self._tokenize(w.unsegmented[0])[1] for w in self.training_data])
    
    def _prune_vocab(self, percent_to_remove=0.1):
        scores = self._score()
        sorted_scores = list(sorted(scores.items(), key=lambda x: x[1]))
        cutoff_idx = int(len(sorted_scores) * percent_to_remove)
        for token, _ in sorted_scores[:cutoff_idx]:
            self.vocab.pop(token)
            if len(self.vocab) <= self.vocab_size:
                break

        self._compute_probs()

    def _train(self, max_iterations=60, convergence_threshold=1e-4, percent_to_remove=0.1, **kwargs):
        prev_likelihood = self._log_likelihood()

        for i in range(max_iterations):
            self._prune_vocab()
            likelihood = self._log_likelihood()
            if abs(likelihood - prev_likelihood) < convergence_threshold or len(self.vocab) <= self.vocab_size:
                break
            prev_likelihood = likelihood

    def _postprocess(self):
        for form in self.forms:
            segmented, _ = self._tokenize(form.unsegmented[0])
            form.update(segmented)

    def _segment_word(self, word): #Can be replaced with the Viterbi algorithm.
        segmentations = self._backtrack(0, [], word)
        return segmentations

    def _backtrack(self, idx, path, word):
        if idx == len(word):
            return [path]
        segmentations = []
        for j in range(idx + 1, len(word) + 1):
            subword = word[idx:j]
            if subword in self.vocab:
                segmentations += self._backtrack(j, path + [subword], word)
        return segmentations
    
    def _tokenize(self, word, **kwargs):
        segmentations = self._segment_word(word)
        best_seg = min(segmentations, key=lambda seg: self._loss(seg))
        best_loss = self._loss(best_seg)
        return best_seg, best_loss


class Morfessor(Tokenizer):
    def _preprocess(self, **kwargs):
        if not morfessor:
            raise ValueError("You must install the morfessor software package")
        self.training_data = [(1, tuple(m[0])) for m in self.forms.unsegmented()]

    def _train(self, **kwargs):
        # sanitize kwargs
        kws = set(kwargs.keys())
        for kw in kws:
            if kw not in ["algorithm", "algorithm_params", "finish_threshold", "max_epochs"]:
                kwargs.pop(kw)

        self.model = morfessor.BaselineModel()
        self.model.load_data(self.training_data)
        self.model.train_batch(**kwargs)

    def _postprocess(self):
        """
        Store segmentations from Morfessor in own model.
        """
        for f in self.forms:
            res = self.model.segment(tuple(f.unsegmented[0]))
            f.update(res)


class LSVTokenizer(Tokenizer):
    # the possible values for each parameter.
    # the first value doubles as default option.
    param_options = {
        "method": ["type", "entropy", "max_drop", "normalized"],
        "strategy": ["peak", "rise", "threshold", "subword"]
    }

    def __init__(self, **kwargs):
        self.params = {}

        for param, values in self.param_options.items():
            if param in kwargs:
                if kwargs[param] in values:
                    self.params[param] = kwargs[param]
                else:
                    raise ValueError(f"Invalid value for argument {param}: '{kwargs[param]}'")
            else:
                self.params[param] = values[0]

        if self.params["strategy"] == "threshold":
            if "threshold" in kwargs:
                self.params["threshold"] = kwargs["threshold"]
            else:
                raise ValueError("A threshold is required for the threshold segmentation strategy.")

        super().__init__(**kwargs)

    def _preprocess(self, **kwargs):
        self.training_data = Trie(self.forms)

    def _calculate_type_variety(self, token_variety: list):
        return [len(x) for x in token_variety]

    def _calculate_successor_entropy(self, token_variety: list):
        entropies = []

        for varieties in token_variety:
            entropy = 0.0
            sum_varieties = sum(varieties)
            for v in varieties:
                p = v / sum_varieties
                entropy -= p * math.log2(p)
            entropies.append(entropy)

        return entropies

    def _calculate_successor_max_drop(self, token_variety: list):
        return [1 - max(x) / sum(x) for x in token_variety]

    def _calculate_exp_lsv(self):
        # calculate regular LSV first
        type_varieties = [[len(x) for x in token_variety] for token_variety in self.token_varieties.values()]

        # sort variety arrays by their length in descending order
        type_varieties.sort(key=lambda x: len(x), reverse=True)

        self.expected_sv = []

        for i in range(len(type_varieties[0])):
            num_sv = 0
            sum_sv = 0
            for sv in type_varieties:
                if i >= len(sv):
                    break
                num_sv += 1
                sum_sv += sv[i]
            self.expected_sv.append(sum_sv / num_sv)

    def _calculate_norm_lsv(self, token_variety: list):
        """
        Normalized LSV as proposed by Çöltekin (2010).
        """
        # calculate regular LSV first
        norm_sv = self._calculate_type_variety(token_variety)

        # TODO check whether this works properly, oversegmentation is suspiciously strong

        for i in range(len(norm_sv)):
            norm_sv[i] /= self.expected_sv[i]

        return norm_sv

    def _get_token_varieties(self):
        return {word.unsegmented: self.training_data.get_token_variety(word) for word in self.forms}

    def _train(self, **kwargs):
        # cache segmentations with specified parameters
        self.token_varieties = self._get_token_varieties()

        var_func_mapping = {
            "type": self._calculate_type_variety,
            "entropy": self._calculate_successor_entropy,
            "max_drop": self._calculate_successor_max_drop,
            "normalized": self._calculate_norm_lsv
        }

        # get the corresponding function to calculate variety values
        var_func = var_func_mapping.get(self.params["method"], self._calculate_type_variety)

        # preprocessing step for normalized LSV
        if self.params["method"] == "normalized":
            self._calculate_exp_lsv()

        # calculate variety values for each word
        self.varieties = {}
        for word, token_var in self.token_varieties.items():
            self.varieties[word] = var_func(token_var)

    def _get_splits_at_peak(self, varieties):
        """
        Peak and plateau segmentation strategy, as formalized by Hafer and Weiss (1974).
        Splits a word at index i iff the varieties[i] >= varieties[i+1] and varieties[i] >= varieties[i-1].
        Does not introduce splits if LSV == 1 for type frequency.
        """
        splits = []

        for i in range(1, len(varieties) - 1):
            if varieties[i] >= varieties[i - 1] and varieties[i] >= varieties[i + 1]:
                splits.append(i)

        return splits

    def _get_splits_at_rise(self, varieties):
        """
        Benden (2005)'s **First Algorithm**.
        Introduces a split wherever the variety value is higher than its immediate predecessor.
        """
        splits = []

        for i in range(1, len(varieties)):
            if varieties[i] > varieties[i - 1]:
                splits.append(i)

        return splits

    def _get_splits_by_threshold(self, varieties):
        splits = []

        for i, variety in enumerate(varieties):
            if variety > self.params["threshold"]:
                splits.append(i)

        return splits

    def _get_splits_by_subword(self, word):
        subwords = self.training_data.get_subwords(word)
        return [len(x) for x in subwords]

    def _get_splits(self):
        split_func_mapping = {
            "peak": self._get_splits_at_peak,
            "rise": self._get_splits_at_rise,
            "threshold": self._get_splits_by_threshold,
            "subword": self._get_splits_by_subword
        }

        strategy = self.params["strategy"]
        split_func = split_func_mapping.get(strategy, self._get_splits_at_peak)

        splits_by_word = {}

        for word, varieties in self.varieties.items():
            if strategy == "subword":
                splits = split_func(word)
            else:
                splits = split_func(varieties)
            splits_by_word[word] = splits

        return splits_by_word

    def _postprocess(self):
        splits_by_word = self._get_splits()

        for word, splits in splits_by_word.items():
            for i in splits:
                if self.training_data.is_branching(word[0][:i]):
                    self.forms[word].split(i)

    def _tokenize(self, word, **kwargs):
        if (kwargs.get("method", self.params["method"]) == self.params["method"] and
                kwargs.get("strategy", self.params["strategy"]) == self.params["strategy"]):
            return super()._tokenize(word)  # returns the cached segmentation
        else:
            # TODO calculate segmentation on the fly based on the passed parameters
            pass


class LPVTokenizer(LSVTokenizer):
    def _preprocess(self, **kwargs):
        self.training_data = Trie(self.forms, reverse=True)

    def _get_token_varieties(self):
        token_varieties = {}

        for word in self.forms:
            reversed_word = Morpheme(word.unsegmented[0])
            reversed_word.reverse()
            reversed_word = Word(reversed_word)
            token_varieties[reversed_word] = self.training_data.get_token_variety(word)

        return token_varieties

    def _postprocess(self):
        splits_by_word = self._get_splits()

        # word is unsegmented (all segments are in one morpheme)
        for reversed_word, splits in splits_by_word.items():
            word = Morpheme(reversed_word[0])
            word.reverse()
            word_len = len(word)
            word = Word(word)

            for i in splits:
                split_idx = word_len - i
                if self.training_data.is_branching(reversed_word[0][:i]):
                    self.forms[word].split(split_idx)


class LSPVTokenizer(Tokenizer):
    def __init__(self, lsv: LSVTokenizer = None, lpv: LPVTokenizer = None, **kwargs):
        self.lsv = lsv or LSVTokenizer(**kwargs)
        self.lpv = lpv or LPVTokenizer(**kwargs)

        super().__init__(**kwargs)

    def _train(self, **kwargs):
        self.lsv.train(self.forms)
        self.lpv.train(self.forms)

    def _postprocess(self):
        for f in self.forms:
            splits = self.lsv.forms[f.unsegmented].get_splits() + self.lpv.forms[f.unsegmented].get_splits()
            for i in splits:
                f.split(i)


class SquareEntropyTokenizer(Tokenizer):
    """
    Determines segment boundaries based on the number of squares, economy, and entropy measures (Medina-Urrea 2007).
    This implementation follows the best segmentation strategy reported in Méndez-Cruz et al. (2016; S13)
    with an adjustable threshold.
    """

    def _preprocess(self, **kwargs):
        # major parts of the method rely on measure about shared prefixes or suffixes;
        # so storing the forms as tries (in both directions) seems to be the most convenient eval-data structure
        self.prefix_trie = Trie(self.forms)
        self.suffix_trie = Trie(self.forms, reverse=True)

        # a dictionary in which all possible splits are stored
        self.training_data = collections.defaultdict(list)

        for form in self.forms:
            word = form.unsegmented[0]
            for i in range(1, len(word)):
                self.training_data[word].append((word[:i], word[i:]))

        # set up a dictionary in which affixality metrics will be stored
        self.metrics = collections.defaultdict(lambda: collections.defaultdict(list))

    def _normalize(self, values):
        return [x / max(values) for x in values] if max(values) > 0 else len(values) * [0.0]

    def _count_squares(self):
        empty_morpheme = Morpheme()

        for word, splits in self.training_data.items():
            squares = []
            for prefix, suffix in splits:
                num_squares = 0
                suffix_candidates = [x[len(prefix):] for x in self.prefix_trie.query(prefix)]
                suffix_candidates.remove(suffix)
                while empty_morpheme in suffix_candidates:
                    suffix_candidates.remove(empty_morpheme)

                prefix_candidates = [x[len(suffix):] for x in self.suffix_trie.query(suffix[::-1])]
                prefix_candidates.remove(prefix[::-1])
                while empty_morpheme in prefix_candidates:
                    prefix_candidates.remove(empty_morpheme)

                for pre in prefix_candidates:
                    for suf in suffix_candidates:
                        if WordWrapper(pre[::-1] + suf) in self.forms:
                            num_squares += 1

                squares.append(num_squares)

            self.metrics[word]["squares"] = self._normalize(squares)

    def _calculate_economy(self):
        for word, splits in self.training_data.items():
            suffix_economy_values = []
            prefix_economy_values = []

            for prefix, suffix in splits:
                # calculate suffix economy
                if self.prefix_trie.is_branching(prefix):
                    # get base candidates by removing likely actual prefixes
                    suffix_candidates = self.prefix_trie.query(prefix)
                    base_candidates = [x[::-1] for x in self.suffix_trie.query(suffix[::-1])]
                    suffix_freq = self.suffix_trie.get_count(suffix[::-1])
                    for x in base_candidates:
                        if self.prefix_trie.get_count(x) > suffix_freq:
                            base_candidates.remove(x)
                    suffix_economy_values.append(len(base_candidates) / len(suffix_candidates))
                else:
                    suffix_economy_values.append(0)

                # calculate prefix economy
                if self.suffix_trie.is_branching(suffix):
                    # get base candidates by removing likely actual suffixes
                    prefix_candidates = [x[::-1] for x in self.suffix_trie.query(suffix[::-1])]
                    base_candidates = self.prefix_trie.query(prefix)
                    prefix_freq = self.prefix_trie.get_count(prefix)
                    for x in base_candidates:
                        if self.suffix_trie.get_count(x[::-1]) > prefix_freq:
                            base_candidates.remove(x)
                    prefix_economy_values.append(len(base_candidates) / len(prefix_candidates))
                else:
                    prefix_economy_values.append(0)

            # normalize economy values by dividing by the highest respective value per word
            norm_suffix_economy = self._normalize(suffix_economy_values)
            norm_prefix_economy = self._normalize(prefix_economy_values)

            self.metrics[word]["economy"] = [norm_suffix_economy, norm_prefix_economy]

    def _entropy(self, distribution):
        entropy = 0.0
        total = sum(distribution)

        if total == 0:
            return 0.0

        for v in distribution:
            p = v / total
            entropy -= p * math.log2(p)

        return entropy

    def _calculate_entropy(self):
        for word, splits in self.training_data.items():
            # get token successor varieties
            suffix_token_varieties = self.prefix_trie.get_token_variety(word)
            prefix_token_varieties = self.suffix_trie.get_token_variety(word)[::-1]

            # calculate entropies
            suffix_entropies = [self._entropy(x) for x in suffix_token_varieties[1:-1]]
            prefix_entropies = [self._entropy(x) for x in prefix_token_varieties[1:-1]]

            # normalize
            norm_suffix_entropies = self._normalize(suffix_entropies)
            norm_prefix_entropies = self._normalize(prefix_entropies)

            self.metrics[word]["entropy"] = [norm_suffix_entropies, norm_prefix_entropies]

    def _train(self, **kwargs):
        self.threshold = kwargs.get("threshold") or 0.5

        # Medina-Urrea (2007) suggests that the normalizing constant is calculated per word type,
        # not on the entire corpus
        self._count_squares()
        self._calculate_economy()
        self._calculate_entropy()

        for word, metrics in self.metrics.items():
            squares = metrics["squares"]
            suffix_economy, prefix_economy = metrics["economy"]
            suffix_entropy, prefix_entropy = metrics["entropy"]

            # suffix and prefix affixiality are calculated separately here; a boundary is then inserted if
            # one of them exceeds the threshold. It is not clear from the paper whether this is actually the
            # intended segmentation strategy.
            for i in range(len(squares)):
                affixiality = max((squares[i] + prefix_entropy[i] + prefix_economy[i]) / 3,
                                  (squares[i] + suffix_entropy[i] + suffix_economy[i]) / 3)
                self.metrics[word]["affixiality"].append(affixiality)

    def _postprocess(self):
        for form in self.forms:
            affixialities = self.metrics[form.unsegmented[0]]["affixiality"]
            for i, af in enumerate(affixialities):
                if af > self.threshold:
                    form.split(i+1)
