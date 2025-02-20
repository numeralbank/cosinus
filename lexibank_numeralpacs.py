from pathlib import Path
from collections import defaultdict

import attr
import pylexibank
from clldutils.misc import slug


@attr.s
class CustomLanguage(pylexibank.Language):
    Sources = attr.ib(default=None)
    FileName = attr.ib(default=None)


@attr.s
class CustomLexeme(pylexibank.Lexeme):
    Morphemes = attr.ib(default=None)


class Dataset(pylexibank.Dataset):
    dir = Path(__file__).parent
    id = "numeralpacs"
    writer_options = dict(keep_languages=False, keep_parameters=False)
    lexeme_class = CustomLexeme
    language_class = CustomLanguage

    form_spec = pylexibank.FormSpec(
        brackets={"(": ")"}, separators=",", missing_data=("",), strip_inside_brackets=True
    )

    def cmd_makecldf(self, args):
        sources = {}

        args.writer.add_sources()
        args.writer.add_languages()
        args.writer.add_sources()

        concepts = args.writer.add_concepts(
            id_factory=lambda c: c.id.split("-")[-1] + "_" + slug(c.gloss), lookup_factory="Name"
        )

        for language in self.languages:
            sources[language["ID"]] = language["Sources"].split(";")

        for file in sorted(self.raw_dir.glob("done/*.tsv")):
            table = self.raw_dir.read_csv(file, delimiter="\t", dicts=True)

            if args.dev:
                # only log problems in dev mode; don't raise exceptions
                validate_language(table, sources[table[0]["DOCULECT"]], log=args.log)
            else:
                try:
                    validate_language(table, sources[table[0]["DOCULECT"]])
                except ValueError as e:
                    args.log.error(str(e)+ " Skipping language...")

            for data in pylexibank.progressbar(table):
                try:
                    args.writer.add_form_with_segments(
                        Language_ID=data["DOCULECT"],
                        Parameter_ID=concepts[data["CONCEPT"].lower()],
                        Value=data["FORM"],
                        Form=data["FORM"],
                        Segments=data["TOKENS"].split(),
                        Morphemes=data["MORPHEMES"],
                        Source=sources[data["DOCULECT"]],
                    )
                except ValueError:
                    args.log.error(
                        f"Problem/missing data in:\n  LANGUAGE: {data['DOCULECT']}\n  CONCEPT: {data['CONCEPT']}\n  FORM: {data['FORM']}"
                    )
                except KeyError as e:
                    args.log.error(
                        f"Problem w/ concept or doculect mapping:\n  LANGUAGE: {data['DOCULECT']}\n  CONCEPT: {data['CONCEPT']}\n  FORM: {data['FORM']}"
                    )


def validate_language(data, sources_for_lang, log=None):
    # record sources
    all_sources = []
    language = data[0]["DOCULECT"]

    # map morpheme ID's to underlying forms and glosses
    id_to_underlying_morpheme = defaultdict(set)
    id_to_gloss = defaultdict(set)

    for row in data:
        # normalize morphemes and extract underlying forms
        tokens = row["TOKENS"]

        morphemes = tokens.split("+")
        morphemes = [x.strip().split() for x in morphemes]
        for i, morpheme in enumerate(morphemes):
            for j, token in enumerate(morpheme):
                if "/" in token:
                    morphemes[i][j] = token.split("/")[1]

        # remove empty string (from inline alignments)
        for m in morphemes:
            while "-" in m:
                m.remove("-")

        # extract cognate IDs and morpheme glosses
        cogids = list(map(int, row["COGIDS"].split()))
        glosses = row["MORPHEMES"].split()

        if not (len(morphemes) == len(glosses) == len(cogids)):
            msg = f"Mismatching number of morphemes for form {row['FORM']} in language {language}."
            if log:
                log.warn(msg)
            else:
                raise ValueError(msg)

        for id, morpheme in zip(cogids, morphemes):
            id_to_underlying_morpheme[id].add(tuple(morpheme))

        for id, gloss in zip(cogids, glosses):
            id_to_gloss[id].add(gloss)

        # extract sources
        sources = row.get("SOURCE", "")
        if ";" in sources:
            sources = sources.split(";")
        else:
            sources = sources.split()

        all_sources.extend(sources)

    # validate glosses
    for id, gloss_set in id_to_gloss.items():
        if id != 0 and len(gloss_set) > 1:
            msg = f"COGID {id} in language {language} points to multiple glosses: {', '.join(gloss_set)}."
            if log:
                log.warn(msg)
            else:
                raise ValueError(msg)

    # validate underlying forms
    for id, morpheme_set in id_to_underlying_morpheme.items():
        if id != 0 and len(morpheme_set) > 1:
            morphemes = [" ".join(m) for m in morpheme_set]
            morphemes = "\n\t".join(morphemes)
            msg = (f"COGID {id} in language {language} points to multiple underlying morphemes: \n\t{morphemes}")
            if log:
                log.warn(msg)
            else:
                raise ValueError(msg)

    # validate sources
    if not all_sources:
        msg = f"No sources in language {language}."
        if log:
            log.warn(msg)
        else:
            raise ValueError(msg)

    for source in all_sources:
        if source.endswith("]") and "[" in source:
            source = source.split("[")[0]
        if source not in sources_for_lang:
            msg = f"Source {source} not defined for language {language}."
            if log:
                log.warn(msg)
            else:
                raise ValueError(msg)

    return True
