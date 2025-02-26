from pathlib import Path
from tabulate import tabulate
import csv
from morseg.algorithms.tokenizer import *
from morseg.utils.wrappers import *
import numpy as np


raw_path = Path(__file__).parent.parent / "raw" / "done"

results = []
languages = []
models = ["Morfessor (surface)", "Affix (surface)", "LSPE (surface)", "Morfessor (underlying)", "Affix (underlying)", "LSPE (underlying)"]

precisions = []
recalls = []

for file in raw_path.glob("*.tsv"):
    with open(file) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for line in reader:
            languages.append(line["DOCULECT"])
            break

    row = []
    for underlying in [False, True]:
        wl = WordlistWrapper.from_file(file, underlying=underlying)

        # Morfessor
        model = Morfessor()
        model.train(wl)
        f1, prec, recall = model.forms.f1_score()
        row.append(f1)
        if underlying:
            precisions.append(prec)
            recalls.append(recall)

        # Affix
        model = LSPVTokenizer(strategy="subword")
        model.train(wl)
        row.append(model.forms.f1_score()[0])

        # LSPE
        model = LSPVTokenizer(method="entropy", strategy="peak")
        model.train(wl)
        row.append(model.forms.f1_score()[0])

    results.append(row)

print(tabulate(results, headers=models, showindex=languages))

print(f"Avg. Precision: {np.mean(precisions)}")
print(f"Avg. Recall: {np.mean(recalls)}")

with open("morseg_eval.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Language"] + models)
    for i, row in enumerate(results):
        writer.writerow([languages[i]] + row)
    writer.writerow(["average"] + np.mean(results, axis=0).tolist())
