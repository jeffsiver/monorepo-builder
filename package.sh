#!/bin/bash

python3 -m venv .

echo "Updating patch version number"
bumpversion patch

echo "Building distribution file"
rm -rf ./dist
if ! python setup.py bdist_wheel
then
    echo "Package build failed"
    exit 16
fi
