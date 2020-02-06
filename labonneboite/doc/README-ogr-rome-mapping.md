# About the ROME dataset, our OGR-ROME mapping, job autocomplete and thesaurus

## The ROME dataset

Technically LBB searches are designed to give results for a specific given ROME code, which is an official job category code of the French administration. They are 500+ of them and you can see them [here](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/data/rome_labels.csv).

A job autocomplete based solely on the ROME labels would not give users a great experience because many relevant keywords do not appear in any ROME code and would thus give zero results.

## The OGR dataset and our OGR-ROME mapping

As the job autocomplete goal is to make the user select an existing ROME code, we need to enrich the ROME dataset with many more relevant keywords for each ROME code.

We did this historically by using the OGR dataset. This is another dataset from the French administration about job categories, much more refined than the ROME dataset. They are 10K+ OGR codes and you can see them [here](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/data/ogr_labels.csv).

The OGR dataset is also called `Appellations métier` in French.

The mapping between OGR and ROME codes is [here](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/data/ogr_rome_mapping.csv). One ROME code has many OGR codes but one OGR code belongs to a single ROME code.

We pretend to make the user select an OGR code but actually we use its correponding ROME code to process the search.

## The thesaurus

We experienced rare cases where the OGR dataset was not enough and would not match some specific keywords. For example `android` and `ios` (technical terms for IT Developers) would not match anything.

Thus we injected another logic to match these specific keywords, and potentially thousands of others located in a dataset of Pôle emploi but unfortunately the administration refused that we used this dataset (internally named `thesaurus`) on our open source project, hence the fact that this feature only works as a proof of concept for only two keywords :-/

The thesaurus logic can be found [here](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/autocomplete.py#L90).
