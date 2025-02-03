python prepare.py $1
pandoc --css css/pandoc.css --standalone --citeproc --bibliography=sources.bib --variable papersize=a4paper,fontsize=10pt -i tmp.md -o $2 --pdf-engine=xelatex
