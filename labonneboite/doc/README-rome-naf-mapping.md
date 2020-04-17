# About our custom ROME NAF mapping

We build this custom weighted ROME-NAF mapping for our use as we needed it to match ROME codes requested by the frontend user to the NAF code of companies.

- The raw mapping is available [here](https://raw.githubusercontent.com/StartupsPoleEmploi/labonneboite/master/labonneboite/common/data/rome_naf_mapping.csv).
- Documentation about how it was built is available [here](https://github.com/StartupsPoleEmploi/labonneboite/tree/master/ROME_NAF) (in French only, sorry!).
- The ROME code referential is available [here](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/data/rome_labels.csv).
- The NAF code referential is available [here](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/data/naf_labels.csv).
- The [ROME NAF mapping explorer](https://labonneboite.pole-emploi.fr/data/romes-for-naf) is a publicly available web interface designed to help you navigate this mapping. For each ROME code (resp. NAF code) it will interactively show you its relevant NAF codes (resp. ROME codes) ordered by relevancy weight. Here are for example [relevant ROME codes for NAF 0220Z](https://labonneboite.pole-emploi.fr/data/romes-for-naf?naf=0220Z) and [relevant NAF codes for ROME A1201](https://labonneboite.pole-emploi.fr/data/nafs-for-rome?rome=A1201).

## What to do when a ROME NAF mapping does not make sense

From time to time a user will report a matching which does not make any sense. The simplest solution is to manually delete this specific mapping from [here](https://raw.githubusercontent.com/StartupsPoleEmploi/labonneboite/master/labonneboite/common/data/rome_naf_mapping.csv).

However, make sure that deleting this mapping does not result in an orphan ROME or an orphan NAF, by carefully checking both the NAF and the ROME in the [ROME NAF mapping explorer](https://labonneboite.pole-emploi.fr/data/romes-for-naf).

An orphan ROME would result in all searches for this ROME code to give zero results. This is highly undesirable.

An orphan NAF would result in all companies having this NAF code to never ever be displayed in any search result on LBB. This is highly undesirable as well.


