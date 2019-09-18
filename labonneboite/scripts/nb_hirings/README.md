# Number of hirings per company per rome

For the PSE school study, some datas were needed : 
- Number of hirings per company per rome
- threshold for which the number of hirings enables the company to be "bonne boîte"

First version of this dataset contains multiple columns: 
- **siret** : the siret of the company
- **codenaf** : the naf code of the company (activity sector)
- **rome** : the rome code for this specific row (which has been found, from the naf code)
- **codepostal** : the zipcode
- **codecommune** : the citycode
    - The zipcode and city code are different : http://www.owlapps.net/articles/code-insee-code-commune-et-code-postal 
- **trancheeffectif** : Each value matches to a number of people in the company. We can find the labels matching to these codes on this CSV file : https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/data/helpers/effectif_labels.csv 
- **nb_recrutements_predits** : Number of people the algorithm believes the company will hire for this specific ROME for this specific company
- **score** : It's just a different/obfuscated version of the field above, the threshold to define if it's a "bonne boîte" or no, is based on this field
- **seuil** : If the previous field 'score' is above or equal to this 'seuil' value, then the company is seen as a "bonne boîte".
- **is a bonne boite ?** : The column contains 1 if it's a "bonne boîte", 0 if it's not. Right now, the threshold is just an arbitrary number we chose after different experiences. But, as i explained it to Sofia, it will soon evolve : We will use a 'metiers en tension' file, which will give for each ROME a percentage of 'tension'. The threshold will be evolving according to this percentage, and won't be the same for all the ROME. So the definition of this field "is it a bonne boite or no" will evolve really quickly --> When it will be set up, we will give you another dataset which will say according to the new standards if it's a "bonne boîte" or no. 