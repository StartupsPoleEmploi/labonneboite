import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "LaBonneBoite",
    version = "0.1",
    author = "Tommy Jarnac",
    author_email = "tommy.jarnac@gmail.com",
    description = (""),
    packages=['labonneboite',],
    include_package_data=True,
    long_description=read('README.md'),
    install_requires=[],
    entry_points = {
        'console_scripts': [
            'create_index = labonneboite.scripts.create_index:run',
            'update_lbb_data = labonneboite.importer.importer:run'
        ],
    }
)
