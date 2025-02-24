from pycldf import Dataset
from lingpy import Wordlist
from pathlib import Path
from collections import defaultdict
from tabulate import tabulate
import statistics


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
    
    

    return (
            sfs,
            ufs,
            cgs)


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
                morphemes)]

table = []

for i, (language, items) in enumerate(sorted(data.items(), key=lambda x:
                                             languages[x[0]].data["Name"])):
    sfs, ufs, cgs = expressivity(items, language)
    
    # can also be put into a function or into expressivity
    form_count = 0
    for forms in items.values():
        for form in forms:
            form_count += 1

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
        "!" if len(ufs) != len(cgs) else ""
        ]]
print(
        tabulate(
            table, 
            headers=["Number", "Glottocode", "Language", "Family", "Base", "Forms",
                     "Surface",
                     "Underlying", "Cognates", 
                     "Surf. Morph.",
                     "Und. Morph.",
                     "Cogn.",

                     "Problems"],
            tablefmt="pipe",
            floatfmt=".2f"
               )
      )




