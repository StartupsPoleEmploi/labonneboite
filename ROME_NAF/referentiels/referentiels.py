# Pour utiliser les nomenclatures ROME, OGR ou NAF, importer ce fichier.
# Les objects chargés sont des dataframes pandas. Voir referentiels.ipynb pour des exemples d'utilisation.

import pandas as pd


ROME_df = pd.read_csv("referentiel_ROME/20150921_arboprincipale28427_ROME.csv", index_col=0, sep="|", dtype=str)

OGR_df = pd.read_csv("referentiel_OGR/20150921_arboprincipale28427_OGR.csv", sep="|", dtype=str).set_index("OGR")

NAF_df = pd.read_csv("referentiel_NAF/naf2008_liste_n5_nouveau_header.csv", sep="|", encoding="utf-8").set_index(
    ["NAF"]
)
