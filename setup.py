from setuptools import setup, find_namespace_packages

setup(
    name="monorepo_builder",
    author="Jeff Siver",
    author_email="jsiver@celltrak.com",
    description="An opionated builder for CellTrak monorepo's with Python and node projects.",
    version="0.2.12",
    license="MIT",
    packages=find_namespace_packages(include="monorepo_builder.*"),
    install_requires=["Click", "boto3"],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points="""
        [console_scripts]
        monorepo-build=monorepo_builder.runner:run_build
        copy-installers=monorepo_builder.runner:copy_installers
    """,
)
