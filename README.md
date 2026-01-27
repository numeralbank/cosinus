# CLDF Dataset presenting Rubehn et al.'s "Compositional Structures in Numeral Systems Across Languages" from 2025

[![CLDF validation](https://github.com/numeralbank/cosinus//workflows/CLDF-validation/badge.svg)](https://github.com/numeralbank/cosinus//actions?query=workflow%3ACLDF-validation)

## How to cite

If you use these data please cite
- the original source
  > Rubehn, A., C. Rzymski, L. Ciucci, K. Bocklage, A. Kučerová, D. Snee, A. Stephen, K. P. van Dam, and J.-M. List (2025): Annotating and Inferring Compositional Structures in Numeral Systems Across Languages. In: Proceedings of the 7th Workshop on Research in Computational Linguistic Typology and Multilingual NLP (SIGTYP 2025). 29-42. https://doi.org/10.18653/v1/2025.sigtyp-1.4
- the derived dataset using the DOI of the [particular released version](../../releases/) you were using

## Description


CLDF dataset providing annotated numeral systems.

This dataset is licensed under a CC-BY-4.0 license

## Notes

# A Note on Browsing the Data with PyCLDF

If you have installed `pycldf` via `pip` in Python (using a fresh virtual environment), you can easily browse the data in the following way. The following code accesses all forms in the data. The individual data types are automatically imposed by `pycldf`. 

```python
from pycldf import Dataset

ds = Dataset.from_metadata("cldf/cldf-metadata.json")

forms = ds.objects("FormTable")
```

Non-canonical data (which the dataset contains) can be accessed via the `data` attribute of each `Form`-object in the list of forms.

```python
In : forms[2500].data
Out: 
OrderedDict([('ID', 'Lamani-thirtyfive-1'),
             ('Local_ID', None),
             ('Language_ID', 'Lamani'),
             ('Parameter_ID', 'thirtyfive'),
             ('Value', 'tis an paanc'),
             ('Form', 'tis an paanc'),
             ('Segments',
              ['t', 'i', 's', '+', 'a', 'n', '+', 'p', 'aː', 'n', 'ʧ']),
             ('Comment', None),
             ('Source', ['TrailLamani1970']),
             ('Cognacy', None),
             ('Loan', None),
             ('Graphemes', None),
             ('Profile', None),
             ('Morphemes', ['thirty', 'and', 'five']),
             ('Cognates', [26, 1, 6]),
             ('Surface_Form', ['t i s', 'a n', 'p aː n ʧ']),
             ('Underlying_Form', ['t i s', 'a n', 'p aː n ʧ']),
             ('Tokens',
              ['t', 'i', 's', '+', 'a', 'n', '+', 'p', 'aː', 'n', 'ʧ'])])
```

Each form links two the language table via the `Language_ID` and to the concept table (`ParameterTable` in CLDF terminology) via the `Parameter_ID`. To combine the information, by pulling more detailed information on the language and the concept, can can load the languages and the concepts from the CLDF datasets as follows.

```python
languages = ds.objects("LanguageTable")
concepts = ds.objects("ParameterTable")
```

The three objects `forms`, `languages`, and `concepts` are no typical Python lists, but a combination of a list and a dictionary. One can access them by using the identifier of an entry as key and by passing an integer as index.

This allows us now to access more specific information on the concept and the lanuage from the form that we accessed above.

```python
this_form = forms[2500].data
this_concept = concepts[this_form["Parameter_ID"]].data
this_language = languages[this_form["Language_ID"]].data
```

This yields the following data for the language:

```python
In : this_language
Out: 
OrderedDict([('ID', 'Lamani'),
             ('Name', 'Lamani'),
             ('Glottocode', 'lamb1269'),
             ('Glottolog_Name', 'Lambadi'),
             ('ISO639P3code', 'lmn'),
             ('Macroarea', 'Eurasia'),
             ('Latitude', Decimal('16.5734')),
             ('Longitude', Decimal('76.9717')),
             ('Family', 'Indo-European'),
             ('Sources', 'TrailLamani1970'),
             ('FileName', 'lamb1269'),
             ('Base', '10')])
```

For the concept, we receive the following data.

```python
In [47]: this_concept
Out[47]: 
OrderedDict([('ID', 'thirtyfive'),
             ('Name', 'thirty five'),
             ('Concepticon_ID', '3484'),
             ('Concepticon_Gloss', 'THIRTY FIVE'),
             ('Number', '35'),
             ('NumberValue', 35)])
```

We can illustrate how the information can be combined by now pulling essential information from the three tables and putting them in a single table. To make sure entries that are represented in their internal Python datatypes are rendered correctly as strings in the table, we must convert them accordingly (this relatest to `Surface_Form`, `Underlying_From`, `Cognates`, and `Morphemes`).

```python
table = []
for form in map(lambda x: x.data, forms):
    language, concept = languages[form["Language_ID"]].data, concepts[form["Parameter_ID"]].data
    if concept["NumberValue"] == 5:
        table += [[language["Name"], language["Glottocode"], concept["Number"],
                  " + ".join(form["Surface_Form"]), 
                  " + ".join(form["Underlying_Form"]), 
                  " ".join(map(lambda x: str(x), form["Cognates"])),
                  " ".join(form["Morphemes"])]]
```

With the help of the `tabulate` package, we can print out this information to table.

```python
from tabulate import tabulate

print(tabulate(table, headers=["Language", "Glott.", "Nr.", "Surface", 
                               "Underlying", "Morphemes", "Cognates"],
               tablefmt="pipe"))
```

The output is given in the table below.

| Language           | Glott.   |   Nr. | Surface             | Underlying          | Morphemes   | Cognates                      |
|:-------------------|:---------|------:|:--------------------|:--------------------|:------------|:------------------------------|
| Acehnese           | achi1257 |     5 | l i m ʌ ŋ           | l i m ʌ ŋ           | 2           | five                          |
| Amharic            | amha1245 |     5 | a m m ɨ s t         | a m m ɨ s t         | 5           | five                          |
| Assamese           | assa1263 |     5 | p ã s               | p ɔ n               | 5           | five                          |
| Barwar Neo-Aramaic | assy1241 |     5 | x a m ʃ a           | x a m ʃ a           | 6           | five                          |
| Aymara             | ayma1253 |     5 | pʰ i s q a          | pʰ i s q a          | 4           | five                          |
| Cavineña           | cavi1250 |     5 | p i ɕ i k a         | p i ɕ i k a         | 10          | five                          |
| Chiquitano/Bésɨro  | chiq1248 |     5 | m a                 | m a                 | 4           | five                          |
| Classical Syriac   | clas1252 |     5 | ħ a m ʃ + aː        | ħ a m e ʃ + aː      | 5 11        | five suff_gender1             |
| Classical Syriac   | clas1252 |     5 | ħ a m e ʃ           | ħ a m e ʃ           | 5           | five                          |
| Czech              | czec1258 |     5 | p j ɛ t             | p j ɛ t             | 5           | five                          |
| Dhivehi            | dhiv1236 |     5 | f a s               | f a s               | 8           | five                          |
| Yiddish            | east2295 |     5 | f ɪ n f             | f ɪ n f             | 5           | five                          |
| French             | stan1290 |     5 | s ɛ̃ k               | s ɛ̃ k               | 5           | five                          |
| Ge'ez              | geez1241 |     5 | x æ m ɨ s + t + u   | x æ m s + t + u     | 5 12 11     | five suff_gender suff_nom_sg1 |
| Ge'ez              | geez1241 |     5 | x æ m s             | x æ m s             | 5           | five                          |
| German             | stan1295 |     5 | f ʏ n f             | f ʏ n f             | 4           | five                          |
| Modern Hebrew      | hebr1245 |     5 | χ a m i ʃ + a       | χ a m e ʃ + a       | 5 13        | five suff_gender2             |
| Modern Hebrew      | hebr1245 |     5 | χ a m e ʃ           | χ a m e ʃ           | 5           | five                          |
| Hindi              | hind1269 |     5 | p ãː tʃ             | p a n tʃ            | 5           | five                          |
| Huallaga Quechua   | hual1241 |     5 | p i tʃ q a          | p i tʃ q a          | 6           | five                          |
| Hungarian          | hung1274 |     5 | ø t                 | ø t                 | 5           | five                          |
| Iraqw              | iraq1241 |     5 | k o o ʔ á n         | k o o ʔ á n         | 3           | five                          |
| Irish              | iris1253 |     5 | k uː ɟ              | k uː ɟ              | 5           | five                          |
| Italian            | ital1282 |     5 | t͡ʃ i n k we         | t͡ʃ i n k we         | 5           | five                          |
| Kalasha            | kala1372 |     5 | p o n ʤ             | p o n ʤ             | 3           | five                          |
| Uipo (Maringic)    | khoi1251 |     5 | pʰ ə + ŋ ɑ̃          | pʰ ə + ŋ ɑ̃          | 51 5        | PFX2 five                     |
| Kumzari            | uigh1240 |     5 | p a n ʤ             | p a n ʤ             | 5           | five                          |
| Lamani             | lamb1269 |     5 | p aː n ʧ            | p aː n ʧ            | 6           | five                          |
| Lamjung Yolmo      | lamj1247 |     5 | ŋ a                 | ŋ a                 | 1           | five                          |
| Latin              | lati1261 |     5 | kʷ iː ŋ kʷ ɛ        | kʷ iː ŋ kʷ ɛ        | 3           | five                          |
| Lishana Deni       | lish1247 |     5 | χ a m ʃ a           | χ a m ʃ a           | 5           | five                          |
| Makyam (Khalai)    | maky1236 |     5 | pʰ ə ³¹ + ŋ a ³³    | pʰ ə ³¹ + ŋ a ³³    | 50 5        | PFX1 five                     |
| Maltese            | malt1254 |     5 | h ɐ m s ɐ           | h ɐ m s ɐ           | 5           | five                          |
| Mandarin           | mand1415 |     5 | u ²¹³               | u ²¹³               | 5           | five                          |
| Burmese            | mand1476 |     5 | ŋ á                 | ŋ á                 | 5           | five                          |
| Mapudungun         | mapu1245 |     5 | k e ʧ u             | k e ʧ u             | 6           | five                          |
| Georgian           | nucl1302 |     5 | χ u tʰ + i          | χ u tʰ + i          | 4 7         | five nominative               |
| Paraguayan Guarani | para1311 |     5 | p o                 | p o                 | 3           | five                          |
| Pashto             | pash1269 |     5 | p i n z ə           | p i n z ə           | 4           | five                          |
| Russian            | russ1263 |     5 | pʲ a tʲ             | pʲ a tʲ             | 7           | five                          |
| Sanskrit           | sans1269 |     5 | p a ɲ tʃ a n        | p a ɲ tʃ a          | 5           | five                          |
| Scottish Gaelic    | scot1245 |     5 | k oː gʲ             | k oː gʲ             | 5           | five                          |
| Sebat Bet Gurage   | seba1251 |     5 | a m m ɨ s t         | a m m ɨ s t         | 5           | five                          |
| Siraiki            | sera1259 |     5 | p ã ʤ               | p ã ʤ               | 10          | five4                         |
| Shanghainese       | shan1293 |     5 | ɦ ŋ̍ ²³              | ɦ ŋ̍ ²³              | 5           | five                          |
| Spanish            | stan1288 |     5 | θ i ŋ k o           | θ i ŋ k o           | 5           | five                          |
| Standard Arabic    | stan1318 |     5 | x a m s + a t + u n | x a m s + a t + u n | 6 13 12     | five suff_gender1 nom_sg      |
| Standard Arabic    | stan1318 |     5 | x a m s + u n       | x a m s + u n       | 6 12        | five nom_sg                   |
| Telugu             | telu1262 |     5 | ʌ j i d u           | ʌ j i d u           | 5           | five                          |
| Tigre              | tigr1270 |     5 | ħ a m ɨ s           | ħ a m ɨ s           | 6           | five                          |
| Tommo So           | tomm1242 |     5 | ǹ n ɔ́               | ǹ n ɔ́               | 3           | five                          |
| Uyghur             | uigh1240 |     5 | b ɛ ʃ               | b ɛ ʃ               | 4           | five                          |
| Wayuu              | wayu1243 |     5 | h a ʔ r a i         | h a ʔ r a ɺ i       | 9           | five                          |
| Balochi            | west2368 |     5 | p ə n ʧ             | p ə n ʧ             | 6           | five                          |
| Wolam              | wola1254 |     5 | p ə ŋ u             | p ə ŋ u             | 5           | five                          |

It is clear, that the table in this form can also be exported to a CSV file that would have a flat structure (as opposed to the multi-table representation in CLDF). The same can also be achieved by converting the data to SQLite and then extracting the data from the SQLite database in one single table in CSV format. The following SQLite code can for example be simply written to a file `flat.sql` and later called with SQLite. 

```sql
.mode csv
.headers on
select 
    l.cldf_name, 
    l.cldf_glottocode, 
    l.cldf_latitude, 
    l.cldf_longitude, 
    c.numbervalue, 
    c.concepticon_gloss, 
    f.surface_form, 
    f.underlying_form 
from 
  languagetable as l, 
  parametertable as c, 
  formtable as f 
where 
    f.cldf_languagereference = l.cldf_id and 
    f.cldf_parameterreference = c.cldf_id
;
```

To convert the database to SQLite format, the `pycldf` package offers a commandline command.

```shell
$ cldf createdb cldf/cldf-metadata.json cosinus.sqlite
```

Then, having created the file `flat.sql` with the code above, one can use the command from the commandline as follows to extract the combined information from the tables and write them to a single CSV file.

```shell
$ sqlite3 cosinus.sqlite < flat.sql > cosinus.csv
```



## Statistics


[![CLDF validation](https://github.com/numeralbank/cosinus//workflows/CLDF-validation/badge.svg)](https://github.com/numeralbank/cosinus//actions?query=workflow%3ACLDF-validation)
![Glottolog: 100%](https://img.shields.io/badge/Glottolog-100%25-brightgreen.svg "Glottolog: 100%")
![Concepticon: 100%](https://img.shields.io/badge/Concepticon-100%25-brightgreen.svg "Concepticon: 100%")
![Source: 100%](https://img.shields.io/badge/Source-100%25-brightgreen.svg "Source: 100%")
![BIPA: 99%](https://img.shields.io/badge/BIPA-99%25-green.svg "BIPA: 99%")
![CLTS SoundClass: 99%](https://img.shields.io/badge/CLTS%20SoundClass-99%25-green.svg "CLTS SoundClass: 99%")

- **Varieties:** 50 (linked to 50 different Glottocodes)
- **Concepts:** 99 (linked to 99 different Concepticon concept sets)
- **Lexemes:** 5,553
- **Sources:** 79
- **Synonymy:** 1.12
- **Invalid lexemes:** 0
- **Tokens:** 73,881
- **Segments:** 234 (3 BIPA errors, 3 CLTS sound class errors, 227 CLTS modified)
- **Inventory size (avg):** 23.44

# Contributors

Name                  | GitHub user | Description                      | Role
---                   |-------------| ---                              | ---
Arne Rubehn           | @arubehn    | data annotation, CLDF conversion | Author
Christoph Rzymski     | @chrzyki    | CLDF conversion                  | Author
Luca Ciucci           |             | data annotation                  | Author
Katja Bocklage        |             | data annotation                  | Author
Alžběta Kučerová      |             | data annotation                  | Author
David Snee            |             | data annotation                  | Author
Kellen Parker van Dam |             | data annotation                  | Author
Chundra Cathcart      | @chundrac   | data annotation                  | Author
Carlo Meloni          | @Cymelo92   | data annotation                  | Author
Johann-Mattis List    | @lingulist  | CLDF conversion, data annotation | Author





## CLDF Datasets

The following CLDF datasets are available in [cldf](cldf):

- CLDF [Wordlist](https://github.com/cldf/cldf/tree/master/modules/Wordlist) at [cldf/cldf-metadata.json](cldf/cldf-metadata.json)