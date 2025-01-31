from pathlib import Path

import attr
import pylexibank
from clldutils.misc import slug


@attr.s
class CustomLanguage(pylexibank.Language):
    Sources = attr.ib(default=None)
    FileName = attr.ib(default=None)


class Dataset(pylexibank.Dataset):
    dir = Path(__file__).parent
    id = "numeralpacs"
    writer_options = dict(keep_languages=False, keep_parameters=False)
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
            for data in pylexibank.progressbar(
                self.raw_dir.read_csv(file, delimiter="\t", dicts=True)
            ):
                try:
                    args.writer.add_form_with_segments(
                        Language_ID=data["DOCULECT"],
                        Parameter_ID=concepts[data["CONCEPT"]],
                        Value=data["FORM"],
                        Form=data["FORM"],
                        Segments=[{"_": "+"}.get(x, x) for x in data["TOKENS"].replace(" ", "")],
                        Source=sources[data["DOCULECT"]],
                    )
                except ValueError:
                    args.log.error(
                        f"Problem/missing data in:\n  LANGUAGE: {data['DOCULECT']}\n  CONCEPT: {data['CONCEPT']}\n  FORM: {data['FORM']}"
                    )
