#!/bin/bash
# 구성도 만들기: bash build.sh [fig_이름 ...]  → ../../figs/<이름>_{ko,en}.pdf · .png (300 dpi)
cd "$(dirname "$0")" || exit 1
OUT=../../figs; mkdir -p $OUT _build
FIGS=("$@"); [ ${#FIGS[@]} -eq 0 ] && FIGS=($(ls fig_*.tex | sed 's/\.tex$//'))
rc=0
for f in "${FIGS[@]}"; do
  f=${f%.tex}
  for L in ko en; do
    [ $L = ko ] && echo '\kotrue' > lang.tex || echo '\kofalse' > lang.tex
    if xelatex -interaction=nonstopmode -halt-on-error -output-directory=_build -jobname=${f}_$L $f.tex > _build/${f}_$L.out 2>&1; then
      cp _build/${f}_$L.pdf $OUT/
      pdftoppm -r 300 -png -singlefile $OUT/${f}_$L.pdf $OUT/${f}_$L
      w=$(grep -c 'Overfull\|Missing character' _build/${f}_$L.log)
      echo "ok  ${f}_$L  (경고 $w)"
    else
      echo "!!  ${f}_$L 실패:"; grep -A3 '^!' _build/${f}_$L.log | head -8; rc=1
    fi
  done
done
exit $rc
