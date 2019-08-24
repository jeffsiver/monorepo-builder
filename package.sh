#!/bin/bash

python3 -m venv .

echo "Updating patch version number"
if ! bumpversion patch
then
    echo "bumpversion failed, package not updated"
    exit 16
fi

echo "Building distribution file"
rm -rf ./dist
if ! python setup.py bdist_wheel
then
    echo "Package build failed"
    exit 16
fi
