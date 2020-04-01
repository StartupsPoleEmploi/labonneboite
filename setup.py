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
            'check_etablissements = labonneboite.importer.jobs.check_etablissements:run',
            'check_dpae = labonneboite.importer.jobs.check_dpae:run',
            'extract_etablissements = labonneboite.importer.jobs.extract_etablissements:run',
            'extract_dpae = labonneboite.importer.jobs.extract_dpae:run_main',
            'compute_scores = labonneboite.importer.jobs.compute_scores:run_main',
            'validate_scores = labonneboite.importer.jobs.validate_scores:run',
            'geocode = labonneboite.importer.jobs.geocode:run_main',
            'populate_flags = labonneboite.importer.jobs.populate_flags:run_main',
            'update_lbb_data = labonneboite.importer.importer:run',
            'daily_json_activity_parser = labonneboite.scripts.impact_retour_emploi.daily_json_activity_parser:run_main',
            'join_activity_logs_dpae = labonneboite.scripts.impact_retour_emploi.join_activity_logs_dpae:run_main',
            'clean_activity_logs_dpae = labonneboite.scripts.impact_retour_emploi.clean_activity_logs_dpae:run_main',
            'make_report = labonneboite.scripts.impact_retour_emploi.make_report:run_main',
            'get_nb_clics_per_siret = labonneboite.scripts.data_scripts.get_nb_clic_per_siret_pse:run_main',
            'get_bonne_boite_company_rome = labonneboite.scripts.data_scripts.get_nb_bonne_boite_per_rome_company.get_bonne_boite_company_rome:run_main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
