# About the algorithms behind LBB and LBA

## Glossary

- A company hiring potential (either all ROME codes included or for a specific ROME code) is a quantity which can be expressed in 3 different forms:
  - a number of hirings (positive integer) - confidential
  - a score (between 0 and 100) - public
  - a number of stars (from 0 to 5) - public
- A ROME code is an official job category, they are approx 500 of them, see [this](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/data/rome_labels.csv). There is no official mapping between a given company and ROME codes.
- A NAF code is an official company activity category, they are approx 700 of them, see [this](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/data/naf_labels.csv). Each company is officially registered with a single NAF code.
- A department is an official geographic subdivision of France. They are approx 100 of them.


## Predicted number of hirings of each company for the upcoming semester, all ROME codes included

Computing this data is the responsibility of the [importer](https://github.com/StartupsPoleEmploi/labonneboite#importer).

We have access and use confidential hiring history for all companies in France, provided by various public institutions.

A machine learning model (linear regression) is trained on past hiring data (DPAE for LBB and APR/CP for LBA, see Hiring model docstring [here](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/importer/models/computing.py#L12) for details) to predict the total number of hirings (all ROME codes included) for each company for the future/upcoming semester, based on hirings of past semesters and other company features like the company size.

Technically there is one model per department thus the department can somehow be considered a feature.

## Predicted number of hirings of each company for the upcoming semester, for each ROME code

For a given company, we convert its (all ROME codes included) predicted number of hirings for the upcoming semester into its predicted number of hirings for each independant ROME code, using the following method.

Let's say we predicted 1000 hirings for company A which has NAF code 0220Z.

We know from our [custom made ROME NAF mapping](https://raw.githubusercontent.com/StartupsPoleEmploi/labonneboite/master/labonneboite/common/data/rome_naf_mapping.csv) that, on average, hirings for NAF code 0220Z have [the following distribution between 5 different ROME codes](https://labonneboite.pole-emploi.fr/data/romes-for-naf?naf=0220Z).

Thus we conclude that company A will hire 425 contracts for ROME code A1201, 195 contracts for ROME code A1101 etc etc 

Feel free to explore [this public undocumented interface](https://labonneboite.pole-emploi.fr/data/romes-for-naf) to browse ROME NAF mapping.

## Conversion of a number of hirings from and to a 0-100 score

Predicted number of hirings are never stored as-is in our database since we consider this data to be confidential / industrial secret.

Instead, we obfuscate this data by converting it into a 0-100 score. The number of hirings is never stored in database, only the equivalent score is. This way even if our production database gets hacked, it cannot be reverse-engineered to get the confidential predicted hirings.

The conversion function used to implement this obfuscation is public on github, however its coefficients used in production are not. Only fake values for the coefficients are available on github.

You can read the underlying code [here](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/scoring.py#L57) (method `_get_score_from_hirings`).

## Conversion of a 0-100 score to a 0-5 stars rating

A simple linear transformation is used for this conversion, see [this code](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/scoring.py#L165) (method `get_stars_from_score`).

Historically stars were between 1.0 and 5.0, matching scores between 20 and 100, however as lower stars may give a bad unjustified feeling about the company, we decided to artificially raise the
stars to be guaranteed to be between 2.5 and 5.0.

## Importer jobs

The importer needs two files to compute hirings for companies :
- Offices file which contains informations about all french offices
- Hirings file which contains informations about all hirings made by french companies

The importer is made up of several jobs :

- [Job 1](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/importer/jobs/check_etablissements.py) and [Job 2](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/importer/jobs/extract_etablissements.py) : These jobs have to check that the offices file is available, and will parse the file to insert into database. 
  **Note** : After each execution of the importer, the offices table is totally rebuilt from scratch.

- [Job 3](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/importer/jobs/check_dpae.py) and [Job 4](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/importer/jobs/extract_dpae.py) : These jobs have to check that the hirings file is available, and will parse the file to insert into database. 
  **Note** : After each execution of the importer, the hirings table is **NOT** totally rebuilt from scratch. We have to keep hirings year after year for the algorithm to work.

- [Job 5](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/importer/jobs/compute_scores.py) is the job which will compute scores for each company. The behaviour of this job and how it computes scores is explained in the sections above.

- [Job 6](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/importer/jobs/validate_scores.py) task is the job which will check different ratios about the prediction of number of hirings that has just been made. It will check that we have enough data for each "departement" (geographic section in France).

- [Job 7](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/importer/jobs/geocode.py) is the job which will get coordinates (latitude and longitude) for each office's location, based on the adress. The [Geolocation Gouv API](https://geo.api.gouv.fr/adresse) is used. There is a cache system that enables to not compute every coordinates for all companies during each importer's cycle. **Note** : This job uses multithreading !

- [Job 8](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/importer/jobs/populate_flags.py) is the job which will assign to each companies some flags. There are different types of flags which let us know if companies hire some old/young people or disabled people...