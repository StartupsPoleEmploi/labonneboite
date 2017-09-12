import pandas as pd

# Affichage des codes ROME les plus fréquents

ROME_df = pd.read_csv('../referentiels/referentiel_ROME/20150921_arboprincipale28427_ROME.csv', index_col=0, sep='|', dtype=str)
OGR_df = pd.read_csv('../referentiels/referentiel_OGR/20150921_arboprincipale28427_OGR.csv', sep='|', dtype=str).set_index('OGR')
NAF_df = pd.read_csv('../referentiels/referentiel_NAF/naf2008_liste_n5_nouveau_header.csv', sep='|', encoding="utf-8").set_index(['NAF'])

stats_lbb = pd.read_csv('../stats_lbb/stats_lbb.csv')
top_slugs = stats_lbb[:34]

def pprint_ROME(array):
    i = 0
    for l in top_slugs.iterrows():
        slugs, visite, uniq = l[1]
        i += 1

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

            #print('{}, {} : {}\n    {}'.format(NAF, NAF_label, poids_NAF[NAF_index], str(array[NAF_index, ROME_index, :])))
            print('{}, {} : {}'.format(NAF_code, NAF_label, poids_NAF[NAF_index], ))
        #print(' '.join([str(NAF) for NAF in top_NAFs]))
        print()


    
# Sortie CSV pour mise en prod

"""
with open('array_ROME1.pickle', 'rb') as f:
    array_ROME1 = pickle.load(f)
with open('array_ROME2.pickle', 'rb') as f:
    array_ROME2 = pickle.load(f)
    
def anonymise(x):
    if 0 < x and x < 10:
        return '?'
    else:
        return str(x)

def write_line_lbb(array, ROME_code, NAF_code, f):
    ROME_index = ROME_df.index.get_loc(ROME_code)
    NAF_index = NAF_df.index.get_loc(NAF_code)
    
    sum_for_ROME_NAF = array[NAF_index, ROME_index, :].sum()
    
    if sum_for_ROME_NAF > 0:
        str_to_write = '{},{},"{}","{}",{},,,,'.format(
            ROME_code,
            NAF_code,
            NAF_df.loc[NAF_code].label,
            ROME_df.loc[ROME_code].label,
            sum_for_ROME_NAF,
            )

        str_to_write += ','.join([
            str(array[NAF_index, ROME_index, tranche_index])
            for tranche_index, tranche in 
            enumerate(tranches_effectif)
        ])

        str_to_write += '\n'

        f.write(str_to_write)
        
def write_line_opendata(array, ROME_code, NAF_code, f):
    ROME_index = ROME_df.index.get_loc(ROME_code)
    NAF_index = NAF_df.index.get_loc(NAF_code)
    
    sum_for_ROME_NAF = array[NAF_index, ROME_index, :].sum()
    
    if sum_for_ROME_NAF > 0:
        str_to_write = '{},{},"{}","{}",{},'.format(
            ROME_code,
            NAF_code,
            ROME_df.loc[ROME_code].label,
            NAF_df.loc[NAF_code].label,
            str(int(sum_for_ROME_NAF)),
            )

        str_to_write += ','.join([
            str(int(array[NAF_index, ROME_index, tranche_index]))
            for tranche_index, tranche in 
            enumerate(tranches_effectif)
        ])

        str_to_write += '\n'

        f.write(str_to_write)
        
with open('mapping_ROME1_NAF_from_DPAE_lbb.csv', 'w') as f:
    for ROME_code in ROME_df.index:
        for NAF_code in NAF_df.index:
            write_line_lbb(array_ROME1, ROME_code, NAF_code, f) 
            
with open('mapping_ROME2_NAF_from_DPAE_lbb.csv', 'w') as f:
    for ROME_code in ROME_df.index:
        for NAF_code in NAF_df.index:
            write_line_lbb(array_ROME2, ROME_code, NAF_code, f) 
            
with open('mapping_ROME1_NAF_from_DPAE_opendata.csv', 'w') as f:
    header = 'ROME_code,NAF_code,ROME_label,NAF_label,total,'
    header += ','.join([
        'TEFET_' + tranche
        for tranche in 
        tranches_effectif
        ])
    header += '\n'
    f.write(header)
    
    for ROME_code in ROME_df.index:
        for NAF_code in NAF_df.index:
            write_line_opendata(array_ROME1, ROME_code, NAF_code, f)

with open('mapping_ROME2_NAF_from_DPAE_opendata.csv', 'w') as f:
    header = 'ROME_code,NAF_code,ROME_label,NAF_label,total,'
    header += ','.join([
        'TEFET_' + tranche
        for tranche in 
        tranches_effectif
        ])
    header += '\n'
    f.write(header)
    
    for ROME_code in ROME_df.index:
        for NAF_code in NAF_df.index:
            write_line_opendata(array_ROME2, ROME_code, NAF_code, f)
"""