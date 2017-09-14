import pandas as pd

# Affichage des codes ROME les plus fréquents

ROME_df = pd.read_csv('../referentiels/referentiel_ROME/20150921_arboprincipale28427_ROME.csv', index_col=0, sep='|', dtype=str)
OGR_df = pd.read_csv('../referentiels/referentiel_OGR/20150921_arboprincipale28427_OGR.csv', sep='|', dtype=str).set_index('OGR')
NAF_df = pd.read_csv('../referentiels/referentiel_NAF/naf2008_liste_n5_nouveau_header.csv', sep='|', encoding="utf-8").set_index(['NAF'])

stats_lbb = pd.read_csv('../stats_lbb/stats_lbb.csv')
top_slugs = stats_lbb[:34]

def pprint_ROME(array):
    for i, line in enumerate(top_slugs.iterrows()):
        slugs, visite, uniq = line[1]

        assert len(ROME_df[ROME_df.slugs == slugs]) == 1

        ROME_code = ROME_df[ROME_df.slugs == slugs].index[0]
        ROME_label = ROME_df.loc[ROME_code].label
        ROME_index = ROME_df.index.get_loc(ROME_code)

        poids_NAF = array[:, ROME_index, :].sum(1)
        top_NAF_indexes = (-poids_NAF).argsort()[:20]

        print('{}. {} ({})'.format(i, ROME_label, ROME_code))
        for NAF_index in top_NAF_indexes:
            NAF_code = NAF_df.iloc[NAF_index].name
            NAF_label = NAF_df.loc[NAF_code].label

            print('{}, {} : {}'.format(NAF_code, NAF_label, poids_NAF[NAF_index], ))
        print()
