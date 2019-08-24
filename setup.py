from setuptools import setup, find_packages

setup(
    name="monorepo-builder",
    version="0.2.3",
    packages=find_packages(),
    install_requires=["Click"],
    entry_points="""
        [console_scripts]
        run-build=monorepo_builder.runner:run_build
    """,
)
