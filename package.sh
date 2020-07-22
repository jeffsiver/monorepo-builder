#!/bin/bash

echo "Updating patch version number"
if ! pipenv run bumpversion patch
then
    echo "bumpversion failed, package not updated"
    exit 16
fi

echo "Building distribution file"
if ! pipenv run python setup.py bdist_wheel
then
    echo "Package build failed"
    exit 16
fi

echo "Removing older installers"
pipenv run python setup.py rotate -m *.whl -d dist -k 1
