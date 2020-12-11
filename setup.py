# -*- coding: utf-8 -*-
import os
import re
from setuptools import setup
import setuptools

with open("README.md", "r") as doc:
    long_description = doc.read()

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open("tecan_od_analyzer/tecan_od_analyzer.py").read(),
    re.M,
).group(1)

setup(
    name="tecan_od_analyzer",
    version=version,
    author="Felix Pacheco Pastor",
    author_email="fepac@biosustain.com",
    description=(
        "OD data handling for growth curve estimation and visualization of TECAN OD readings"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Biosustain/AutoFlow-HTC",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "tecan_od_analyzer = tecan_od_analyzer.__main__:main"
        ]
    },
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "xcode",
        "wheel",
        "numpy",
        "matplotlib",
        "datetime",
        "argparse",
        "path",
        "xlsxwriter",
        "seaborn",
        "scipy",
        "pycodestyle",
        "sphinx",
        "sphinx_rtd_theme",
        "xlrd",
        "pandas",
    ],
    dependency_links=["https://github.com/meono/croissance@v1.2.x"],
    include_package_data=True,
)
