import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="LaBonneBoite",
    version="0.1",
    author="La Bonne Boite",
    author_email="labonneboite@pole-emploi.fr",
    description=(""),
    packages=['labonneboite',],
    include_package_data=True,
    long_description=read('README.md'),
    install_requires=[req for req in open('requirements.txt')],
    entry_points={
        'console_scripts': [
            'create_index = labonneboite.scripts.create_index:run',
            'update_lbb_data = labonneboite.importer.importer:run'
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
