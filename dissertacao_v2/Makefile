ROOT := $(abspath ..)
PY ?= $(ROOT)/.venv/bin/python

.PHONY: pdf figuras clean
figuras:
	cd $(ROOT) && $(PY) dissertacao_v2/scripts/figuras.py

pdf:
	cd latex && TEXINPUTS=$(ROOT)/templates/ita//:$(CURDIR)/latex//: latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=../build dissertacao.tex
	mkdir -p ../output/pdf/v2.0.0-rc.1 && cp build/dissertacao.pdf ../output/pdf/v2.0.0-rc.1/dissertacao.pdf

clean:
	rm -rf build
