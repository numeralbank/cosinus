from pathlib import Path
from tabulate import tabulate
import csv
from morseg.algorithms.tokenizer import *
from morseg.utils.wrappers import *
import numpy as np


raw_path = Path(__file__).parent.parent / "raw" / "done"

results = []
languages = []
models = ["BPE (surface)", "WordPiece (surface)", "Unigram (surface)", "BPE (underlying)", "WordPiece (underlying)", "Unigram (underlying)"]

for file in raw_path.glob("*.tsv"):
    with open(file) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for line in reader:
            languages.append(line["DOCULECT"])
            print(line["DOCULECT"])
            break

    row = []
    for underlying in [False, True]:
        wl = WordlistWrapper.from_file(file, underlying=underlying)

        # get number of distinct morphemes
        morphemes = set()
        for word in wl.gold_segmented():
            for m in word:
                morphemes.add(m)

        vocab_size = len(morphemes)

        """
        # BPE
        model = PairEncoding()
        model.train(wl, vocab_size=vocab_size)
        row.append(model.forms.f1_score()[0])

        # WordPiece
        model = WordPiece()
        model.train(wl, vocab_size=vocab_size)
        row.append(model.forms.f1_score()[0])
        """
        # TODO find working solution for these algorithms
        row.append(0)
        row.append(0)

        # Unigram
        model = UnigramSentencePiece()
        model.train(wl, vocab_size=vocab_size, count_single_characters=False)
        row.append(model.forms.f1_score()[0])

    results.append(row)

print(tabulate(results, headers=models, showindex=languages))

with open("morseg_eval.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Language"] + models)
    for i, row in enumerate(results):
        writer.writerow([languages[i]] + row)
    writer.writerow(["average"] + np.mean(results, axis=0).tolist())
