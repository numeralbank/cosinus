# Analysis

This directory contains all relevant code for running the analyses from the paper (§ 4). To install the required packages, run:

```bash
$ pip install -r requirements.txt
```

The analyses can then be reproduced by simply running the corresponding Python files (`stats.py` for § 4.1; `morseg_eval.py` for § 4.2, `subword_eval.py` for § 4.3).

## Visualization

The map (`map.pdf`) was produced running the following commands:

```bash
pip install cldfviz[cartopy]  # install cldfviz
git clone https://github.com/glottolog/glottolog-cldf.git --depth 1 --branch v5.1  # clone Glottolog 5.1
# make sure you are inside this directory (examples) when running this command (or alternatively adjust the relative paths accordingly)
cldfbench cldfviz.map ../cldf --language-properties Base --format pdf --markersize 25 --output map.pdf --glottolog-cldf glottolog-cldf --no-legend
```
