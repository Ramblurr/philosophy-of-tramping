EPUB=Philosophy_Of_Tramping-Ian_Cutler.epub
OUT=out
PY=py
all: fetch

fetch: venv
	. ${PY}/bin/activate; python fetch.py tramping.txt

epub: ${OUT}/toc.html
	ebook-convert ${OUT}/toc.html ${EPUB} -v --title="A Philosophy of Tramping" --authors="Ian Cutler" --cover=cover.jpg --chapter-mark=pagebreak --toc-filter='.*[jpeg|JPG|png]\$$' --chapter='//h:h1[re:test(@class, "chapter", "i")]' --smarten-punctuation --extra-css="*,body,p,span { font-family: serif }" --sr1-search="font-family: Arial, Helvetica, sans-serif;" --sr1-replace="" --sr2-search='font-family: Times, "Times New Roman", serif;' --sr2-replace="" --filter-css="font-family" --font-size-mapping="12,12,14,16,18,20,22,24"

clean:
	rm -f ${OUT}/*xhtml
	rm -f ${OUT}/images/*

dist-clean: clean
	rm -f ${EPUB}

venv: ${PY}/bin/activate

py/bin/activate: requirements.pip
	test -d ${PY} || virtualenv --system-site-packages ${PY}
	. ${PY}/bin/activate; pip -Ur requirements.pip
	touch ${PY}/bin/activate
