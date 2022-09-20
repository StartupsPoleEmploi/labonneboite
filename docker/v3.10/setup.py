import os
from setuptools import setup
import re


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


pip_editable_with_egg_regex = re.compile("-e (.+#egg=(.+))")


def requirement_to_install_require(requirement: str):
    result = pip_editable_with_egg_regex.match(requirement)
    if result:
        return f"{result.group(2)} @ {result.group(1)}"
    return requirement


install_requires = [
    requirement_to_install_require(req) for req in open("requirements.txt")
]

setup(
    name="LaBonneBoite",
    version="0.2",
    author="La Bonne Boite",
    author_email="labonneboite@pole-emploi.fr",
    description=(""),
    packages=[
        "labonneboite",
    ],
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "create_index = labonneboite.scripts.create_index:run",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
)
