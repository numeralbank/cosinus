import morfessor
import csv
from linse.typedsequence import Word
from pathlib import Path


FILE = Path(__file__).parent.parent / "raw" / "latin-annotated.tsv"


def get_word(wf):
    if isinstance(wf, list):
        wf = " ".join(wf)
    return Word([x.split() for x in wf.split(" + ")])


def preprocess_data(forms, remove_boundaries=True):
    """
    Convert wordlist to a data representation that is suitable for Morfessor.
    :param forms: The wordlist as list of linse.Word objects
    :param remove_boundaries: Indicates if morpheme boundary annotations should be removed, defaults to true
    :return: Data ready to be fed to Morfessor
    """
    clean_data = []

    for form in forms:
        form = str(form)
        if remove_boundaries:
            form = form.replace(" + ", " ")
        tokens = form.split()
        tokens = [x.split("/")[0] for x in tokens if x.split("/")[0] != "-"]
        clean_data.append((1, tuple(tokens)))

    return clean_data


# load data
with open(FILE) as f:
    words = []
    for row in csv.DictReader(f, delimiter="\t"):
        tokens = row["TOKENS"]
        if tokens:
            words += [get_word(tokens)]

# can't pass linse objects to Morfessor; but tuples work
train_data = preprocess_data(words)

model = morfessor.BaselineModel()
model.load_data(train_data)
model.train_batch()

for s in model.get_segmentations():
    morphemes = [" ".join(x) for x in s[2]]
    print(" + ".join(morphemes))
