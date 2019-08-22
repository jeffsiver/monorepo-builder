from setuptools import setup, find_packages

setup(
    name="monorepo-builder",
    version="0.1",
    packages=find_packages(),
    install_requires=["Click"],
    entry_points="""
        [console_scripts]
        run=monorepo_builder.runner:run_build
    """,
)
