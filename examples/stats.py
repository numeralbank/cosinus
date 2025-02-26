from pycldf import Dataset
from lingpy import Wordlist
from pathlib import Path
from collections import defaultdict
from tabulate import tabulate
import statistics
import csv
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from morseg.algorithms.tokenizer import Morfessor
from morseg.utils.wrappers import WordlistWrapper, WordWrapper
import math


def our_path():
    return Path(__file__).parent


def expressivity(data, language):
    sfs, ufs, cgs = defaultdict(list), defaultdict(list), defaultdict(list)
    problems = []
    morpheme_test = defaultdict(set)
    cognate_test = defaultdict(set)
    for concept, forms in data.items():
        for surface, underlying, cognates, morphemes in forms:
            try:
                assert len(morphemes) == len(surface) == len(underlying) == len(cognates)
                for i in range(len(surface)):
                    sfs[surface[i]] += [1 / len(forms)]
                    ufs[underlying[i]] += [1 / len(forms)]
                    cgs[cognates[i]] += [1 / len(forms)]
                    morpheme_test[underlying[i]].add(cognates[i])
                    cognate_test[cognates[i]].add(underlying[i])

            except AssertionError:
                problems += [[
                    " ".join(morphemes),
                    len(morphemes),
                    " + ".join(underlying),
                    len(underlying),
                    " + ".join(surface),
                    len(surface),
                    " + ".join(cognates),
                    len(cognates)]]
    if problems:
        print("# Problem with {0}".format(language))
        print(tabulate(
            problems,
            headers=["Morphemes", "Count", "Underlying", "Count", "Surface", "Count", "Cognates", "Count"],
            tablefmt="pipe"))
    for m, vals in morpheme_test.items():
        if len(vals) > 1:
            print(f"{language} has {len(vals)} cogids for morpheme {m}.")
    for m, vals in cognate_test.items():
        if len(vals) > 1:
            print(f"{language} has {len(vals)} morphemes for cogid {m}.")

    for m in sfs:
        sfs[m] = sum(sfs[m])
    for m in ufs:
        ufs[m] = sum(ufs[m])
    for m in cgs:
        cgs[m] = sum(cgs[m])

    return sfs, ufs, cgs


def morfessor_f1(data, underlying=False):
    forms = []
    idx = 1 if underlying else 0

    for concept, items in data.items():
        for form in items:
            surface = form[idx]
            split_form = [morpheme.split() for morpheme in surface if morpheme]
            forms.append(split_form)

    wl = WordlistWrapper(forms)
    model = Morfessor()
    model.train(wl)

    return model.forms.f1_score()


def entropy(data):
    total = sum(data.values())
    entropy = 0

    for freq in data.values():
        proba = freq / total
        entropy -= proba * math.log(proba)

    return entropy


ds = Dataset.from_metadata(
        our_path().parent / "cldf" / "cldf-metadata.json")

concepts = ds.objects("ParameterTable")
languages = ds.objects("LanguageTable")

data = defaultdict(lambda : defaultdict(list))

for form in ds.objects("FormTable"):
    language = languages[form.data["Language_ID"]]
    concept = concepts[form.data["Parameter_ID"]]
    segments = form.data["Segments"]
    surface = form.data["Surface_Form"]
    underlying = form.data["Underlying_Form"]
    morphemes = form.data["Morphemes"]
    cognates = form.data["Cognates"]

    data[language.data["ID"]][concept.data["Name"]] += [
            (
                surface,
                underlying,
                cognates,
                morphemes
            )
    ]

    # extract only vigesimal system for scottish and lamjung
    if language.id in ["Scottish_Gaelic", "Lamjung_Yolmo"]:
        note = form.data["Comment"]
        if (not note) or note.startswith("vigesimal"):
            lang_key = language.id + "-20"
            data[lang_key][concept.data["Name"]] += [
                (
                    surface,
                    underlying,
                    cognates,
                    morphemes
                )
            ]


table = []
morpheme_expressivity = []
num_morphemes = []

f1_scores = []
opacities = []

entropies = []
coding_lengths = []

for i, (language, items) in enumerate(sorted(data.items())):
    sfs, ufs, cgs = expressivity(items, language)
    sfs_entropy = entropy(sfs)
    ufs_entropy = entropy(ufs)
    cgs_entropy = entropy(cgs)

    entropies.append(cgs_entropy)

    morpheme_expressivity.append(statistics.mean(cgs.values()))
    num_morphemes.append(len(cgs))

    morfessor_score = morfessor_f1(items)[0]
    f1_scores.append(morfessor_score)
    opacities.append(len(sfs) / len(cgs))

    morfessor_underlying = morfessor_f1(items, underlying=True)[0]

    vigesimal_only = language.endswith("-20")
    if vigesimal_only:
        language = language[:-3]

    # can also be put into a function or into expressivity
    form_count = 0
    morpheme_count = 0
    for forms in items.values():
        for form in forms:
            form_count += 1
            morpheme_count += len(form[1])

    # calculate coding length
    coding_length = morpheme_count / form_count
    coding_lengths.append(coding_length)

    table += [[
        i + 1,
        languages[language].data['Glottocode'],
        languages[language].data['Name'],
        languages[language].data["Family"],
        languages[language].data["Base"],
        form_count,
        statistics.mean(sfs.values()),
        statistics.mean(ufs.values()),
        statistics.mean(cgs.values()),
        len(sfs),
        len(ufs),
        len(cgs),
        len(sfs) / sum(sfs.values()),
        len(ufs) / sum(ufs.values()),
        len(cgs) / sum(cgs.values()),
        sfs_entropy,
        ufs_entropy,
        cgs_entropy,
        coding_length,
        len(sfs) / len(cgs),
        morfessor_score,
        morfessor_underlying,
        "X" if vigesimal_only else ""
        ]]

headers = ["Number", "Glottocode", "Language", "Family", "Base", "Forms",
                     "Surface",
                     "Underlying", "Cognates",
                     "Surf. Morph.",
                     "Und. Morph.",
                     "Cogn.",
                     "TTR (Surface)", "TTR (Underlying)", "TTR (Cognates)",
                     "H (Surface)", "H (Underlying)", "H (Cognates)", "code length",
                     "Morph. Opacity", "Morfessor F1", "Morfessor F1 (underlying)",
                     "only vigesimal"]

print(tabulate(table, headers=headers, tablefmt="pipe", floatfmt=".2f"))

with open(our_path() / "stats.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    for row in table:
        writer.writerow(row)

"""
plt.scatter(morpheme_expressivity, num_morphemes)
stat = pearsonr(morpheme_expressivity, num_morphemes)
plt.show()

plt.cla()
plt.scatter(opacities, f1_scores)
print(pearsonr(f1_scores, opacities))
plt.show()
"""

plt.scatter(entropies, coding_lengths)
plt.show()
