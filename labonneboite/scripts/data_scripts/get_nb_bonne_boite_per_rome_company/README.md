# First dataset : nb_hirings_per_company-DATE.csv

For the PSE study, some datas were needed : 
- Number of hirings per company per rome
- threshold for which the number of hirings enables the company to be a "bonne boîte"

This dataset contains multiple columns: 
- **siret** : the siret of the company
- **raisonsociale** : the name of the company
- **enseigne** : the name of the company
- **email** : the email of the company
- **tel** : the tel of the company
- **website** : the website of the company
- **codenaf** : the naf code of the company (activity sector)
- **rome** : the rome code for this specific row (which has been found, from the naf code)
- **codepostal** : the zipcode
- **codecommune** : the citycode
    - The zipcode and city code are different : http://www.owlapps.net/articles/code-insee-code-commune-et-code-postal 
- **trancheeffectif** : Each value matches to a number of people in the company. We can find the labels matching to these codes on this CSV file : https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/data/helpers/effectif_labels.csv 
- **nb_recrutements_predits** : Number of people the algorithm believes the company will hire for this specific ROME for this specific company
- **score** : It's just a different/obfuscated version of the field above, the threshold to define if it's a "bonne boîte" or not is based on this field
- **seuil** : If the previous field 'score' is above or equal to this 'seuil' value, then the company is seen as a "bonne boîte".
- **is a bonne boite ?** : The column contains 1 if it's a "bonne boîte", 0 if it's not.

# Second dataset : nb_bonne_boite_per_rome-DATE.csv

Dataset based on the other one
We check the number of bonne boite per rome to make sure that LBB has enough companies for each Rome.

- **rome** : the rome code
- **nb_bonnes_boites** : the number of companies considered as "bonnes boites" for this rome code
