from setuptools import setup, find_namespace_packages

setup(
    name="celltrak_monorepo_builder",
    author="Jeff Siver",
    author_email="jsiver@celltrak.com",
    description="An opionated builder for monorepo's with Python and node projects.",
    version="0.2.6",
    license="MIT",
    packages=find_namespace_packages(include="monorepo_builder.*"),
    install_requires=["Click"],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points="""
        [console_scripts]
        monorepo-build=monorepo_builder.runner:run_build
    """,
)
