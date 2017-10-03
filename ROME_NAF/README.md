# Rejouer les traitements

Les codes sources de ce répertoires sont écrit en python 3.5.2.

Les traitements de ce répertoires font un large usage de notebooks jupyter écrits en python. Un [notebook jupyter](http://jupyter.org/) est un environnement de développement intégré dans un navigateur web, permettant d'exécuter du code par étapes et d'en partager facilement les résultats.

Pour installer un serveur jupyter : `pip install jupyter`

Le serveur se lance avec la commande `jupyter notebook`. Le serveur est accessible par défaut à l'adresse `localhost:8888` et il est possible de naviger dans l'arborescence pour atteindre un notebook.

Il est souvent préférable de procéder à l'installation au sein d'un environnement virtuel. Voir par exemple [pew](https://github.com/berdario/pew).


# Sources de données

## Croisement entre la base des DPAE et les données de Pôle emploi.

Pour les DPAE hors intérim : fichier `LBB_XDPDPA_DPAE_20160307_20170407_20170407_165803.csv.bz2` de 875Mo.

Pour les DPAE intérim : fichier `LBB_ETT_ETT_20160430_20170530_20170530_162434.csv.gz` de 310Mo.

## Offres d'emploi

Fichier `LBB_EOF_OFFRES_20160307_20170407_20170407_191410.csv.bz2` de 295Mo qui contient des codes OGR.

# Préparation

Les fichiers de données sont nettoyés et seules les informations utilisées ultérieurement sont conservées.

## `clean.sh`

Le script `clean.sh` décompresse, supprime les guillemets, remplace le séparateur de colonne par pipe (`|`) et crée un échantillon constitué d'une ligne sur 1000 à des fins d'exploration.

## Notebooks

Les notebooks `DPAE.ipynb`, `ETT.ipynb`, `offres.ipynb` permettent d'examiner les échantillons des fichiers préparés.

Les notebooks `clean_DPAE.ipynb`, `clean_ETT.ipynb` et `clean_offres.ipynb` ne conservent que les informations utilisées par la suite.  Les fichiers créés `*_clean.csv` contiennent des informations réidentifiantes mais moins sensibles que les fichiers originaux. Une copie de ces fichiers est conservées sur lbbdev:/home/michel/data.

# Agrégation par code ROME, OGR, NAF

Les notebooks `groupby_DPAE_CDI_CDD.ipynb`, `groupby_DPAE_ETT.ipynb` et `groupby_offres.ipynb` réalisent l'agrégation des fichiers `*_clean.csv` selon les codes des nomenclatures. L'agrégation peut se faire par le code ROME principal (systématiquement renseigné) ou par le code ROME secondaire (renseigné dans un peu plus de la moitié des cas). Seuls les contrats de plus de 30 jours sont comptabilisés.

Ces notebooks contiennent également quelques statistiques descriptives, à prendre avec précaution en raison des biais statistiques importants affectant les données

Les fichiers résultant de l'agrégation sont nommés `array_offres.pickle` `array_ROME1_ETT.pickle`, `array_ROME2_ETT.pickle`, `array_ROME1_CDI_CDD.pickle` et `array_ROME2_CDI_CDD.pickle`.

Le notebook `fusion_DPAE.ipynb` somme les agrégations faites sur le ROME principal et sur le ROME secondaire et produit les fichiers `array_ROME1_fusion.pickle` et `array_ROME2_fusion.pickle`.

# Analyse

Les tableaux pickles sont examinés dans les notebooks `analyses_*.ipynb`.

# Publication de données en opendata

Les données utilisées ici, les codes sources ainsi que les données produites relèvent pour leur communication et leur réutilisation du cadre juridique établi par le code des relations entre le public et l'administration. En raison du caractère potentiellement utile pour d'autre acteurs, ces travaux font l'objet d'une publication sur la plateforme data.gouv.fr : https://www.data.gouv.fr/fr/datasets/nombre-dembauches-par-code-ape-et-code-rome/

Le notebook `opendata.ipynb` produit un fichier CSV expurgé des données permettant une réidentification d'une entreprise. Pour cela, le notebook `count_SIRENE.ipynb` récupère dans le fichier SIRENE le nombre d'entreprises répertoriées pour chaque code NAF.

# Editorialisation

Les tableaux produits sont adaptés aux besoins de La Bonne Boîte.

## Pertinence des associations

En particulier, seuls les associations ROME/NAF jugées pertinentes sont prises en compte. Plusieurs critères sont automatiquement déduits par le notebook `editorialisation.ipynb` pour produire des suggestions.

Un tableau XLSX est produit par code ROME ainsi qu'un fichier `suggestions.pickle`.

Le notebook `tableau_LBB.ipynb` produit un fichier CSV `tableau_LBB.csv` utilisation par le backend de La Bonne Boîte.

## Partition des codes OGR d'un code ROME (*"ROMEbis"*)

Un code ROME peut se révéler trop imprécis, voir par exemple `ROME_D1106.ipynb` qui détaille les statistiques d'embauches sur le code ROME D1106 (Vente en alimentation). Ce code ROME regroupe des métiers très différents (Vendeur / Vendeuse en boulangerie-pâtisserie, Vendeur / Vendeuse en poissonnerie...).

Le notebook `decoupage_ROME.ipynb` propose une méthode de regroupement automatique des différents codes OGR d'un code ROME donné faisant sens pour le demandeur d'emploi. Le découpage produit est affiché dans le fichier `decoupage_ROME.txt`. Ce regroupement automatique ne donne pas des résultats satisfaisants, c'est donc une approche manuelle qui est actuellement utilisée. Un petit nombre de codes ROME sont découpés manuellement : les extraits correspondants du fichier `decoupage_ROME.txt` sont copiés puis modifiés pour respecter le format suivant :

```
*** X0123 : un code ROME ***

Le label du groupe OGR 1
01234 titre de l'OGR
01235 titre de l'OGR

Le label du groupe OGR 2
01236 titre de l'OGR
01237 titre de l'OGR

*** Y1234 : un autre code ROME ***

...
```

Ce nouveau fichier est parsé par `parsing_decoupage_ROME.ipynb` et le résultat est sauvegardé dans `decoupage_ROME.pickle`.

Les fichiers requis pour faire évoluer LBB sont créés dans le notebook `output_to_production.ipynb` puis `tableau_LBB.ipynb`.

## Copie

Le script `copy_mapping.sh` copie les fichiers précédemment créés dans le dossier `labonneboite/common/data`.
