#!/usr/bin/env python3
"""
Setup script for PrecipGenPAR - Parameter generator for PrecipGen
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="precipgen-par",
    version="1.3.0",
    author="PrecipGen Contributors",
    author_email="your-email@example.com",
    description="Parameter generator for PrecipGen - A stochastic precipitation simulator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jlillywh/precipgen_par",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: Hydrology",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "precipgen-cli=precipgen.cli.cli:main",
            "precipgen-menu=scripts.easy_start:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
