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


