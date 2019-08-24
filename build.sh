#!/bin/bash

function reset_virtual_environment() {
    echo "Removing current virtual environment"
    rm -rf .Python
    rm -rf include
    rm -rf bin
    rm -rf lib
}

function setup_virtual_environment() {
    if [[ ! -d bin ]]; then
        echo "Creating virtual environment"
        python3 -m venv .
    fi

    source bin/activate
    echo "Installing requirements"
    pip install -r requirements.txt
}

if [[ $1 = "reset" ]]; then
    reset_virtual_environment
fi

setup_virtual_environment

rm -rf reports
mkdir reports

echo "Reformatting"
black .

echo "Running pytest"
if ! pytest
then
    echo "One or more unit tests failed"
    exit 16
fi

echo "Running bandit"
if ! bandit -f screen customer_id_management
then
    echo "bandit found issues"
    exit 16
fi

echo "Collecting test coverage"
pytest --cov-report term --cov=monorepo_builder monorepo_builder/tests

echo "Build completed successfully"
