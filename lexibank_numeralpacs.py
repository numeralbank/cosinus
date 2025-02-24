from pathlib import Path
from collections import defaultdict

import attr
import pylexibank
from clldutils.misc import slug


def surface(segments):
    if isinstance(segments, str):
        segments = segments.split()
    base = [s for s in [x.split("/")[0] for x in segments] if s != "-"]
    return [x.strip() for x in " ".join(base).split("+")]
    


def underlying(segments):
    if isinstance(segments, str):
        segments = segments.split()
    base = [s for s in [x.split("/")[1] if "/" in x else x for x in segments]
            if s != "-"]
    return [x.strip() for x in " ".join(base).split("+")]



@attr.s
class CustomLanguage(pylexibank.Language):
    Sources = attr.ib(default=None)
    FileName = attr.ib(default=None)
    Base = attr.ib(default=None, metadata={"format": "integer"})

@attr.s
class CustomConcept(pylexibank.Concept):
    Number = attr.ib(default=None, metadata={"format": "integer"})


@attr.s
class CustomLexeme(pylexibank.Lexeme):
    Morphemes = attr.ib(default=None, metadata={"format": "string",
                                                "separator": " "})
    Cognates = attr.ib(default=None, metadata={"format": "integer",
                                               "separator": " "})
    Surface_Form = attr.ib(default=None, metadata={"format": "string",
                                                       "separator": " + "})
    Underlying_Form = attr.ib(default=None, metadata={"format": "string",
                                                       "separator": " + "})
    Tokens = attr.ib(default=None, metadata={"format": "string"})


class Dataset(pylexibank.Dataset):
    dir = Path(__file__).parent
    id = "numeralpacs"
    writer_options = dict(keep_languages=False, keep_parameters=False)
    lexeme_class = CustomLexeme
    language_class = CustomLanguage
    concept_class = CustomConcept

    form_spec = pylexibank.FormSpec(
        brackets={"(": ")"}, separators=",", missing_data=("",), strip_inside_brackets=True
    )

    def cmd_makecldf(self, args):
        sources = {}

        args.writer.add_sources()
        args.writer.add_languages()
        args.writer.add_sources()
        
        concepts = {}
        for concept in self.concepts:
            lookup = concept["ID"] + "-" + slug(concept["GLOSS"])
            args.writer.add_concept(
                    ID=lookup,
                    Name=concept["GLOSS"],
                    Number=concept["NUMBER"],
                    Concepticon_ID=concept["CONCEPTICON_ID"],
                    Concepticon_Gloss=concept["CONCEPTICON_GLOSS"]
                    )
            concepts[concept["GLOSS"]] = lookup
            

        for language in self.languages:
            sources[language["ID"]] = language["Sources"].split(";")

        for file in sorted(self.raw_dir.glob("done/*.tsv")):
            table = self.raw_dir.read_csv(file, delimiter="\t", dicts=True)

            language = table[0]["DOCULECT"]
            errors, warnings = validate_language(table, sources[language])
            for warning in warnings:
                args.log.warning(warning)
            if errors:
                if args.dev:
                    for error in errors:
                        args.log.error(error)
                else:
                    error_header = f"An error occurred while processing language {language}. Skipping language..."
                    error_msg = "\n\t\t".join([error_header] + errors)
                    args.log.error(error_msg)
                    raise ValueError

            for data in pylexibank.progressbar(table):
                try:
                    args.writer.add_form_with_segments(
                        Language_ID=data["DOCULECT"],
                        Parameter_ID=concepts[data["CONCEPT"].lower()],
                        Value=data["FORM"],
                        Form=data["FORM"],
                        Segments=" + ".join(surface(data["TOKENS"].split())).split(" "),
                        Morphemes=data["MORPHEMES"].split(" "),
                        Cognates=data["COGIDS"].split(" "),
                        Source=sources[data["DOCULECT"]],
                        Surface_Form=surface(data["TOKENS"].split()),
                        Underlying_Form=underlying(data["TOKENS"].split()),
                        Tokens=data["TOKENS"],
                    )
                except ValueError:
                    args.log.error(
                        f"Problem/missing data in:\n  LANGUAGE: {data['DOCULECT']}\n  CONCEPT: {data['CONCEPT']}\n  FORM: {data['FORM']}"
                    )
                except KeyError as e:
                    args.log.error(
                        f"Problem w/ concept or doculect mapping:\n  LANGUAGE: {data['DOCULECT']}\n  CONCEPT: {data['CONCEPT']}\n  FORM: {data['FORM']}"
                    )


def validate_language(data, sources_for_lang):
    warnings = []
    errors = []

    # record sources
    all_sources = []
    language = data[0]["DOCULECT"]

    # map morpheme ID's to underlying forms and glosses
    id_to_underlying_morpheme = defaultdict(set)
    morpheme_to_id = defaultdict(set)
    id_to_gloss = defaultdict(set)
    gloss_to_id = defaultdict(set)

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
            errors.append(msg)

        for id, morpheme in zip(cogids, morphemes):
            id_to_underlying_morpheme[id].add(tuple(morpheme))
            morpheme_to_id[tuple(morpheme)].add(id)

        for id, gloss in zip(cogids, glosses):
            id_to_gloss[id].add(gloss)
            gloss_to_id[gloss].add(id)

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
            errors.append(msg)

    for gloss, id_set in gloss_to_id.items():
        if gloss != "?" and len(id_set) > 1:
            msg = f"Gloss {gloss} in language {language} maps to multiple IDs: {id_set}."
            warnings.append(msg)

    # validate underlying forms
    for id, morpheme_set in id_to_underlying_morpheme.items():
        if id != 0 and len(morpheme_set) > 1:
            morphemes = [" ".join(m) for m in morpheme_set]
            morphemes = "\n\t".join(morphemes)
            msg = (f"COGID {id} in language {language} points to multiple underlying morphemes: \n\t{morphemes}")
            errors.append(msg)

    for morpheme, id_set in morpheme_to_id.items():
        if len(id_set) > 1:
            msg = f"Morpheme '{' '.join(morpheme)}' in language {language} maps to multiple IDs: {id_set}."
            warnings.append(msg)

    # validate sources
    if not all_sources:
        msg = f"No individual sources in language {language}."
        warnings.append(msg)

    if not sources_for_lang:
        msg = f"No sources in language {language}."
        warnings.append(msg)

    for source in all_sources:
        if source.endswith("]") and "[" in source:
            source = source.split("[")[0]
        if source not in sources_for_lang:
            msg = f"Source {source} not defined for language {language}."
            errors.append(msg)

    return errors, warnings
