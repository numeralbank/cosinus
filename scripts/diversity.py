from lingpy import *
from pathlib import Path
from collections import defaultdict
import statistics
from tabulate import tabulate
import csv
from itertools import combinations

def simpson_div(varis):
    """
    Calculate Simpsons's diversity index.
    """
    
    score = 0
    for val in set(varis):
        score += (varis.count(val) / len(varis)) ** 2
    return 1 - score



def surface(form):
    out = []
    for f in form.split():
        if "/" in f:
            segment = f.split("/")[0]
            if segment not in ["-", "Ø"]:
                out += [segment]
        elif f in ["-", "Ø"]:
            pass
        else:
            out += [f]
    return out

def underlying_morpheme(segments):
    if isinstance(segments, str):
        segments = segments.split()
    base = [s for s in [x.split("/")[1] if "/" in x else x for x in segments]
            if s != "-"]
    return base


with open(Path(__file__).parent.parent / "etc" / "languages.csv") as f:
    languages = {row["FileName"]: row["Name"] for row in csv.DictReader(f,
                                                                        delimiter=",")}

paths = Path(__file__).parent.parent.joinpath("raw", "done").glob("*.tsv")

surface_data = {}
underlying_data = {}

for path in paths:

    lang = path.name[:-4]
    print(lang)
    surface_data[lang] = defaultdict(list)
    underlying_data[lang] = []

    try:
        wl = Wordlist(str(path))
        for idx, language, concept, tokens, morphemes, cognates in wl.iter_rows(
                "doculect", "concept", "tokens", "morphemes", "cogids"):
            token_chunks = " ".join(tokens).split(" + ")
            for m, c, t in zip(morphemes, cognates, token_chunks):
                surface_data[lang][m, c] += [surface(t)]
                if (m, c, underlying_morpheme(t)) not in underlying_data[lang]:
                    underlying_data[lang].append((m, c, underlying_morpheme(t)))

        # analyze data
        diversities = {}
        for (m, c), alms in surface_data[lang].items():
            sequences = sorted(set([tuple(t) for t in alms]))
            msa = Multiple(sequences)
            msa.align(method="library")
            divs = []
            for i in range(len(msa.alm_matrix[0])):
                varis = [row[i] for row in msa.alm_matrix]
                divs += [simpson_div(varis)]
            diversities[m, c] = [" / ".join([" ".join(s) for s in sequences]), statistics.mean(divs)]

        # get most diverse patterns
        div_data = sorted([(a[0], a[1], b[0], b[1]) for a, b in diversities.items()],
                          key=lambda x: x[3], reverse=True)
        print(f"# Data for {languages[lang]}")
        print("")
        print(tabulate(div_data[:10], tablefmt="pipe", floatfmt=".4", headers=[
            "gloss", "cogid", "sequence", "score"]))

        # calculate most similar underlying morphemes
        distances = []
        for i, j in combinations(underlying_data[lang], 2):
            gloss_i, id_i, tokens_i = i
            gloss_j, id_j, tokens_j = j
            dist = edit_dist(tokens_i, tokens_j, normalized=True)
            distances.append((i, j, dist))
        top_10 = [[" ".join(x[2]), " ".join(y[2]), x[0], y[0], x[1], y[1], z] for x, y, z in sorted(distances, key=lambda x: x[2])[:10]]
        print("")
        print(tabulate(top_10, tablefmt="pipe", floatfmt=".4", headers=[
            "morpheme 1", "morpheme 2", "gloss 1", "gloss 2", "cogid 1", "cogid 2", "distance"]))
    except Exception as e:
        print(e)
    input()
