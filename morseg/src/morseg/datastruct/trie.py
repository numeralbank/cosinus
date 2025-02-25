from morseg.utils.wrappers import WordlistWrapper, WordWrapper
from linse.typedsequence import Morpheme, Word, TypedSequence
from typing import overload


class Trie(object):
    """The trie object"""
    # TODO maybe represent Trie as Compact Trie for improved efficiency.
    EOS_SYMBOL = "#"  # symbol to be used to indicate the end of a sequence

    def __init__(self, words: WordlistWrapper = None, eos_symbol=None, reverse=False):
        """
        The trie has at least the root node.
        The root node does not store any character
        """
        self._initialize_root()
        self.reverse = reverse

        if eos_symbol:
            self.EOS_SYMBOL = eos_symbol

        if words:
            self.insert_all(words)

    def _initialize_root(self):
        self.root = TrieNode("")

    def insert(self, word: WordWrapper):
        """Insert a word into the trie"""
        if not word:
            return

        word = self.preprocess_word(word)

        # loop through each character in the word and add/update the node respectively
        node = self.root

        for char in word:
            node = node.add_child(char)

    def preprocess_word(self, word, remove_boundaries=True):
        if type(word) is not WordWrapper:
            raise TypeError()

        # get a copy of the unsegmented "single morpheme" word
        word = Morpheme(word.unsegmented[0])

        # reverse the word if specified as backward trie
        if self.reverse:
            word.reverse()

        # append eos symbol to end of sequence
        if word[-1] != self.EOS_SYMBOL:
            word.append(self.EOS_SYMBOL)

        return word

    def insert_all(self, words):
        if not words:
            return

        for w in words:
            self.insert(w)

    def collect_nodes_preorder(self, node=None):
        if node is None:
            node = self.root

        node_list = [node]

        sorted_child_keys = list(sorted(node.children.keys()))

        for child_key in sorted_child_keys:
            node_list.extend(self.collect_nodes_preorder(node.children[child_key]))

        return node_list

    def dfs(self, node, prefix, output):
        """Depth-first traversal of the trie

        Args:
            - node: the node to start with
            - prefix: the current prefix, for tracing a
                word while traversing the trie
        """
        if node.char == self.EOS_SYMBOL:
            output.append((prefix, node.counter))

        for child in node.children.values():
            if node == self.root:
                self.dfs(child, [], output)
            else:
                self.dfs(child, prefix + [node.char], output)

    def query(self, prefix, freq=False):
        """Given an input (a prefix), retrieve all words stored in
        the trie with that prefix, sort the words by the number of
        times they have been inserted
        """
        # Use a variable within the class to keep all possible outputs
        # As there can be more than one word with such prefix
        output = []
        node = self._get_node(prefix)

        # return an empty list if the prefix is not found in the trie
        if not node:
            return []

        # Traverse the trie to get all candidates
        self.dfs(node, prefix[:-1], output)

        if freq:
            # Sort the results in reverse order and return
            return sorted(output, key=lambda x: x[1], reverse=True)

        # disregard frequencies
        return [x for x, _ in output]

    def get_successor_values(self, word):
        node = self.root
        sv_per_segment = []  # populate with pairs of segment and SV

        for segment in word:
            node = node.children.get(segment)
            if not node:
                break  # populate remaining SVs with 0
            sv = len(node.children)
            sv_per_segment.append((segment, sv))

        while len(sv_per_segment) < len(word):
            i = len(sv_per_segment)
            segment = word[i]
            sv_per_segment.append((segment, 0))
            i += 1

        return sv_per_segment

    @overload
    def get_token_variety(self, word: WordWrapper): ...

    def get_token_variety(self, word: Morpheme):
        if isinstance(word, WordWrapper):
            word = word.unsegmented[0]

        word = Morpheme(word)  # copy object

        if self.reverse:
            word = word[::-1]

        word += self.EOS_SYMBOL
        node = self.root
        variety_per_segment = []

        for segment in word:
            variety = []
            for child in node.children.values():
                variety.append(child.counter)

            variety_per_segment.append(variety)

            node = node.children.get(segment)
            if not node:
                break

        # pad list with 0 values for unknown suffixes
        while len(variety_per_segment) < len(word):
            variety_per_segment.append([0])

        return variety_per_segment

    def is_branching(self, prefix: Morpheme):
        node = self._get_node(prefix)

        if not node:
            return False

        return len(node.children) > 1

    def get_count(self, prefix: TypedSequence):
        """
        Returns how often a prefix occurs in the underlying wordlist, i.e. how many words start with that prefix.
        """
        node = self._get_node(prefix)

        if not node:
            return 0

        return node.counter

    def _get_node(self, prefix: TypedSequence):
        if type(prefix) is Word:
            prefix = sum(prefix)

        node = self.root

        for s in prefix:
            node = node.children.get(s)
            if not node:
                return None

        return node

    def get_subwords(self, word: Word):
        node = self.root
        path = []
        subwords = []

        for m in word:
            for s in m:
                node = node.children.get(s)
                if not node:
                    break

                path.append(s)
                if self.EOS_SYMBOL in node.children:
                    subwords.append(path.copy())

        return subwords

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        nodes = self.collect_nodes_preorder()
        other_nodes = other.collect_nodes_preorder()

        if len(nodes) != len(other_nodes):
            return False

        for node, other_node in zip(nodes, other_nodes):
            if node != other_node:
                return False

        return True


class TrieNode:
    """A node in the trie structure"""
    EOS_SYMBOL = Trie.EOS_SYMBOL

    def __init__(self, char, eos_symbol=None):
        if eos_symbol:
            self.EOS_SYMBOL = eos_symbol

        # the character stored in this node
        self.char = char

        # a counter indicating by how many entries the node is matched
        self.counter = 0

        # a dictionary of child nodes
        # keys are characters, values are nodes
        self.children = {}

    def add_child(self, char):
        if char in self.children:
            child_node = self.children[char]
        else:
            child_node = type(self)(char)
            self.children[char] = child_node

        self.counter += 1

        if char == self.EOS_SYMBOL:
            child_node.counter += 1  # update counter for leaf nodes, since they are never traversed

        return child_node

    def __eq__(self, other):
        if not isinstance(other, TrieNode):
            return False

        return (self.char == other.char and self.counter == other.counter
                and self.children.keys() == other.children.keys())
