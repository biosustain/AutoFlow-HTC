# -*- coding: utf-8 -*-
import re
from setuptools import setup
import setuptools

with open("README.md", "r") as doc:
    long_description = doc.read()

version = re.search(
    r'^__version__\s+([^,\s]+).+"',
    open("tecan_od_analyzer/tecan_od_analyzer.py").read(),
    re.M,
).group(1)

setup(
    name="tecan_od_analyzer",
    version=version,
    author="Matthias Mattanovich",
    author_email="matmat@biosustain.dtu.dk",
    description=(
        "OD data handling for growth curve estimation and visualization of TECAN OD readings" # noqa E501
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
        "flake8",
        "wheel==0.36.2",
        "numpy==1.19.5",
        "matplotlib",
        "datetime==4.3",
        "argparse==1.4.0",
        "path==15.0.1",
        "xlsxwriter==1.3.7",
        "seaborn==0.11.1",
        "scipy==1.6.0",
        "pycodestyle==2.6.0",
        "sphinx==3.4.3",
        "sphinx_rtd_theme==0.5.1",
        "pytest==6.2.1",
        "xlrd==1.2.0",
        "pandas==1.2.1",
    ],
    dependency_links=["https://github.com/biosustain/croissance.git@v1.2.x"],
    include_package_data=True,
)
