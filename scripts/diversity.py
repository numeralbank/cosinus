from lingpy import *
from pathlib import Path
from collections import defaultdict
import statistics
from tabulate import tabulate
import csv

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


with open(Path(__file__).parent.parent / "etc" / "languages.csv") as f:
    languages = {row["FileName"]: row["Name"] for row in csv.DictReader(f,
                                                                        delimiter=",")}

paths = Path(__file__).parent.parent.joinpath("raw", "done").glob("*.tsv")

data = {}
for path in paths:

    print(path.name[:-4])
    data[path.name[:-4]] = defaultdict(list)
    wl = Wordlist(str(path))
    for idx, language, concept, tokens, morphemes, cognates in wl.iter_rows(
            "doculect", "concept", "tokens", "morphemes", "cogids"):
        token_chunks = " ".join(tokens).split(" + ")
        for m, c, t in zip(morphemes, cognates, token_chunks):
            data[path.name[:-4]][m, c] += [surface(t)]
    
    # analyze data
    diversities = {}
    for (m, c), alms in data[path.name[:-4]].items():
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
    print(f"# Data for {languages[path.name[:-4]]}")
    print("")
    print(tabulate(div_data[:10], tablefmt="pipe", floatfmt=".4", headers=[
        "gloss", "cogid", "sequence", "score"]))
    input()

