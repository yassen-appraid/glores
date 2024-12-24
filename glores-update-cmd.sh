#!/bin/bash
cd ..

for dir in repo-{1..5}; do (test -d "$(pwd)/$dir" && (test -d "$(pwd)/$dir/.github" || mkdir "$(pwd)/$dir/.github") && python glores/glores.py update --workspace $(pwd) --repo $(pwd)/"$dir") done