# -*- coding: utf-8 -*-
import os 
import re
from setuptools import setup
import setuptools

with open("README.md", "r") as doc:
    long_description = doc.read()

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('OD_handler/OD_handler.py').read(),
    re.M
    ).group(1)

setup(
    name = "OD_handler",
    version = version,
    author = "Felix Pacheco Pastor",
    author_email = "fepac@biosustain.com",
    description = ("OD data handling for growth curve estimation and visualization of TECAN OD readings"),
    long_description = long_description, 
    long_description_content_type="text/markdown",
    url = "https://github.com/felixpacheco/AutoFlow-HTC/tree/felix_HTC",
    packages=setuptools.find_packages(),
    entry_points = {
        "console_scripts": ["OD_handler = OD_handler.__main__:main"]
        },
    license = "MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
    ],
    install_requires=[],
    include_package_data = True,

)