# A Note on Browsing the Data with PyCLDF

If you have installed `pycldf` via `pip` in Python (using a fresh virtual environment), you can easily browse the data in the following way. The following code accesses all forms in the data. The individual data types are automatically imposed by `pycldf`. 

```python
from pycldf import Dataset

ds = Dataset.from_metadata("cldf/cldf-metadata.json")

forms = ds.objects("FormTable")
```

Non-canonical data (which the dataset contains) can be accessed via the `data` attribute of each `Form`-object in the list of forms.

```python
In : forms[0].data
Out: 
OrderedDict([('ID', 'Acehnese-one-1'),
             ('Local_ID', None),
             ('Language_ID', 'Acehnese'),
             ('Parameter_ID', 'one'),
             ('Value', 'sa'),
             ('Form', 'sa'),
             ('Segments', ['s', 'a']),
             ('Comment', None),
             ('Source', ['wiktionary']),
             ('Cognacy', None),
             ('Loan', None),
             ('Graphemes', None),
             ('Profile', None),
             ('Morphemes', ['one']),
             ('Cognates', ['5']),
             ('Surface_Form', ['s a']),
             ('Underlying_Form', ['s a']),
             ('Tokens', ['s', 'a'])])
```

Each form links two the language table via the `Language_ID` and to the concept table (`ParameterTable` in CLDF terminology) via the `Parameter_ID`. To combine the information, by pulling more detailed information on the language and the concept, can can load the languages and the concepts from the CLDF datasets as follows.

```python
languages = ds.objects("LanguageTable")
concepts = ds.objects("ParameterTable")
```

The three objects `forms`, `languages`, and `concepts` are no typical Python lists, but a combination of a list and a dictionary. One can access them by using the identifier of an entry as key and by passing an integer as index.

This allows us now to 

