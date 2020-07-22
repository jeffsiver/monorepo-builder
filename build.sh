#!/bin/bash

pipenv update
pipenv clean

rm -rf reports
mkdir reports

echo "Reformatting"
pipenv run black .

echo "Running pytest"
if ! pipenv run pytest
then
    echo "One or more unit tests failed"
    exit 16
fi

echo "Build completed successfully"
