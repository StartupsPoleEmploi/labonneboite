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

Computing this data is the responsibility of the [importer](https://github.com/StartupsPoleEmploi/labonneboite-importer).

We have access and use confidential hiring history for all companies in France, provided by various public institutions.

A machine learning model (linear regression) is trained on past hiring data (DPAE for LBB) to predict the total number of hirings (all ROME codes included) for each company for the future/upcoming semester, based on hirings of past semesters and other company features like the company size.

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
