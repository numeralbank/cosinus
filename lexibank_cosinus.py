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
    Base = attr.ib(default=None, metadata={"format": "string"})

@attr.s
class CustomConcept(pylexibank.Concept):
    Number = attr.ib(default=None, metadata={"format": "string"})
    NumberValue = attr.ib(default=None, metadata={"datatype": "integer"})


@attr.s
class CustomLexeme(pylexibank.Lexeme):
    Morphemes = attr.ib(default=None, metadata={"datatype": "string",
                                                "separator": " "})
    Cognates = attr.ib(default=None, metadata={"datatype": "integer",
                                               "separator": " "})
    Surface_Form = attr.ib(default=None, metadata={"datatype": "string",
                                                       "separator": " + "})
    Underlying_Form = attr.ib(default=None, metadata={"datatype": "string",
                                                       "separator": " + "})
    Tokens = attr.ib(default=None, metadata={"datatype": "string", "separator": " "})


class Dataset(pylexibank.Dataset):
    dir = Path(__file__).parent
    id = "cosinus"
    writer_options = dict(keep_languages=False, keep_parameters=False)
    lexeme_class = CustomLexeme
    language_class = CustomLanguage
    concept_class = CustomConcept

    form_spec = pylexibank.FormSpec(
        brackets={"(": ")"}, separators=",", missing_data=("",), strip_inside_brackets=True
    )

    def cmd_makecldf(self, args):
        sources = {}
        language_by_file = {}

        args.writer.add_sources()
        args.writer.add_languages()

        for concept in self.concepts:
            args.writer.add_concept(
                ID=slug(concept["GLOSS"]),
                Name=concept["GLOSS"],
                Number=concept["NUMBER"],
                NumberValue=concept["NUMBER"],
                Concepticon_ID=concept["CONCEPTICON_ID"],
                Concepticon_Gloss=concept["CONCEPTICON_GLOSS"]
            )

        for language in self.languages:
            sources[language["ID"]] = language["Sources"].split(";")
            language_by_file[language["FileName"]] = language["ID"]

        

        for file in sorted(self.raw_dir.glob("done/*.tsv")):
            args.log.info("Processing {0}".format(file.name))
            table = self.raw_dir.read_csv(file, delimiter="\t", dicts=True)

            language = language_by_file[file.name[:-4]] 
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
                    #raise ValueError

            for data in pylexibank.progressbar(table):
                # we normalize tokens quickly to account for clts
                # ᴇ ˗> e̞
                tokens = []
                for t in data["TOKENS"].split():
                    if "ᴇ" in t:
                        t = t.replace("ᴇ", "e̞")
                    tokens += [t]

                try:
                    args.writer.add_form_with_segments(
                        Language_ID=language,
                        Parameter_ID=slug(data["CONCEPT"]),
                        Value=data["FORM"].strip(),
                        Form=data["FORM"].strip(),
                        Segments=" + ".join(surface(tokens)).split(" "),
                        Morphemes=data["MORPHEMES"].strip().split(" "),
                        Cognates=data["COGIDS"].strip().split(" "),
                        Source=sources[language],
                        Surface_Form=surface(tokens),
                        Underlying_Form=underlying(data["TOKENS"].split()),
                        Tokens=data["TOKENS"].split(),
                        Comment=data.get("NOTE", "")
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
    underlying_to_surface_variants = defaultdict(set)
    id_to_gloss = defaultdict(set)
    gloss_to_id = defaultdict(set)

    for row in data:
        # extract underlying forms and surface forms
        tokens = row["TOKENS"]
        morphemes = underlying(tokens)
        surface_morphemes = surface(tokens)

        # extract cognate IDs and morpheme glosses
        cogids = list(map(int, row["COGIDS"].split()))
        glosses = row["MORPHEMES"].split()

        if not (len(morphemes) == len(glosses) == len(cogids)):
            msg = f"Mismatching number of morphemes for form «{row['FORM']}»"
            msg += f" or glosses «{row["MORPHEMES"]}»"
            msg += f" or cognates «{" ".join([str(c) for c in cogids])}»"
            msg += f" in language {language} (concept {row["CONCEPT"]})."
            errors.append(msg)

        for underlying_morpheme, surface_morpheme in zip(morphemes, surface_morphemes):
            underlying_to_surface_variants[tuple(underlying_morpheme)].add(tuple(surface_morpheme))

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

    # validate underlying vs surface forms
    for underlying_morpheme, surface_variants in underlying_to_surface_variants.items():
        if underlying_morpheme not in surface_variants:
            msg = (f"[{" ".join(underlying_morpheme)}] was given as underlying morpheme, but does not appear as surface form."
                   f" (COGID: {morpheme_to_id[underlying_morpheme]})")
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
