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

problems = ["Cavinena", "Aymara", "Wayuu"]

ideal_vocab_size_found = []

for file in raw_path.glob("*.tsv"):
    with open(file) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for line in reader:
            languages.append(line["DOCULECT"])
            print("\n\n" + line["DOCULECT"])
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

        # BPE
        model = PairEncoding()
        model.train(wl, threshold=3, vocab_size=vocab_size, iterations=200, callbacks=["alphabet_size"])
        row.append(model.forms.f1_score()[0])
        if vocab_size in model.training_history["alphabet_size"]:
            ideal_vocab_size_found.append(languages[-1] + "-BPE-" + "underlying" if underlying else
                                          languages[-1] + "-BPE-" + "surface")

        # WordPiece
        model = WordPiece()
        model.train(wl, threshold=0.05, vocab_size=vocab_size, iterations=200, callbacks=["alphabet_size"])
        row.append(model.forms.f1_score()[0])
        if vocab_size in model.training_history["alphabet_size"]:
            ideal_vocab_size_found.append(languages[-1] + "-WP-" + "underlying" if underlying else
                                          languages[-1] + "-WP-" +"surface")


        # if languages[-1] in problems:
        #    row.append(0)
        #    continue

        # Unigram
        model = UnigramSentencePiece()
        model.train(wl, vocab_size=vocab_size, count_single_characters=False, callbacks=["alphabet_size"])
        row.append(model.forms.f1_score()[0])
        print(model.forms.f1_score()[0])
        if vocab_size in model.training_history["alphabet_size"]:
            ideal_vocab_size_found.append(languages[-1] + "-UG-" + "underlying" if underlying else
                                          languages[-1] + "-UG-" + "surface")


    results.append(row)

print(tabulate(results, headers=models, showindex=languages))
print(ideal_vocab_size_found)

with open("subword_eval.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Language"] + models)
    for i, row in enumerate(results):
        writer.writerow([languages[i]] + row)
    writer.writerow(["average"] + np.mean(results, axis=0).tolist())
