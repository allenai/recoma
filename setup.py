"""
Initialized from:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

from pathlib import Path
from typing import List

from setuptools import setup, find_namespace_packages


def read_reqs_file(path: str) -> List[str]:
    reqs: List[str] = []
    with open(path, "r") as reqs_file:
        for line in reqs_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            reqs.append(line)
    return reqs


# Get the long description from the README file
long_description = Path("README.md").read_text(encoding="utf-8")
setup(
    name="recoma",
    version="0.0.1",
    description="A Python package to reason by communicating with agents",
    long_description=long_description,
    long_description_content_type="text/markdown",  # Optional (see note above)
    url="https://github.com/allenai/recoma",
    author="Tushar Khot",
    author_email="tushark@allenai.org",
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="reasoning, communication, language models, tools, LLM",  # Optional
    packages=find_namespace_packages(include=['recoma', 'recoma.*']),
    python_requires=">=3.9",
    install_requires=read_reqs_file("requirements.txt"),
    entry_points={  # Optional
        "console_scripts": [
            "recoma.run_inference=recoma.run_inference:main",
        ],
    }
)
