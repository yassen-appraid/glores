#!/bin/bash
cd ..

for dir in repo-{1..7}; do (python glores/glores.py update --workspace $(pwd) --repo $(pwd)/"$dir") done