# -*- coding: utf-8 -*-

import os
import urllib
import pandas as pd
from sqlalchemy import create_engine

# TODO : To add datas about job sector, use code NAF --> Luc Caffier

start = 0
column_names = ['kc_siret', 'dc_naf_id', 'dc_adresse', 'dc_codepostal', '_',
                'dn_tailleetablissement', 'dc_communenaissancepays', 'kd_dateembauche',
                'dc_typecontrat_id', 'dd_datefincdd', 'dc_romev3_1_id', 'dc_romev3_2_id',
                'kd_datecreation', 'dc_privepublic', 'dc_commune_id', 'dc_natureemploi_id',
                'dc_qualitesalarie_id', 'dn_dureetravailhebdo', 'dn_dureetravailmensuelle',
                'dn_dureetravailannuelle', 'nbrjourtravaille', 'iiann', 'dc_lblprioritede',
                'kn_trancheage', 'duree_pec', 'dc_ididentiteexterne', 'premiere_embauche']


# function used to create a new column from dateheure column in dpae
def get_date(row):
    return row['kd_dateembauche'][:10]


# Get the datas from lab_tre_activity in the mysql of lbbdev
engine = create_engine('mysql://labonneboite:%s@127.0.0.1:3306/labonneboite' %
                       urllib.parse.quote_plus('LaB@nneB@ite'))
engine.connect()
query = "select * from activity_logs"
df_activity = pd.read_sql_query(query, engine)
'''
df_activity = pd.read_csv('/home/jenkins/tre2/activity_logs.csv')
df_activity_2 = df_activity.astype(str)
'''
df_activity_2 = df_activity[df_activity.dateheure > "2018-08-31"]


print('query SQL OK')

liste_files_dpae = os.listdir('/srv/lbb/data')
liste_files_good = []
for bz2 in liste_files_dpae:
    if 'XDPDPAE' in bz2:
        liste_files_good.append(bz2)
liste_files_good.sort()
bz = liste_files_good[-1]
# We use the datas in csv using smaller chunks
chunksize = 10 ** 6
i = 1
for df_dpae in pd.read_csv('/srv/lbb/data/'+bz,
                           header=None,
                           compression='bz2',
                           names=column_names,
                           sep='|',
                           index_col=False,
                           chunksize=chunksize):

    # remove rows where the data is > to the 11 10 2018 (dont have activity dates after this)
    df_dpae['kd_dateembauche_bis'] = df_dpae.apply(
        lambda row: get_date(row), axis=1)
    # TODO:
    df_dpae_2 = df_dpae[df_dpae.kd_dateembauche_bis > "2018-08-31"]

    # convert df dpae columns to 'object'
    df_dpae_3 = df_dpae_2.astype(str)

    # TODO : Test entre left & inner
    new_df = pd.merge(df_dpae_3,
                      df_activity_2,
                      how='left',  # 'left'
                      left_on=['dc_ididentiteexterne', 'kc_siret'],
                      right_on=['idutilisateur_peconnect', 'siret'])

    new_df_2 = new_df[pd.notnull(new_df['idutilisateur_peconnect'])]

    # filter on the fact that dateheure activity must be inferior to kd_dateembauche
    new_df_3 = new_df_2[new_df_2.kd_dateembauche_bis > new_df_2.dateheure]
    new_df_4 = new_df_3.drop(['kd_dateembauche_bis'], axis=1)

    # TODO : Compare documents in both folders,
    # y'a /srv/lbb/data/LBB_XDPDPAE_2019-04-14_2018-03-01.bz2ptet eu un chmilblik
    path = '/home/jenkins/tre2/'
    path_to_csv = path+'act_dpae.csv'
    exists = os.path.isfile(path_to_csv)
    if exists:
        with open(path_to_csv, 'a') as f:
            new_df_4.to_csv(f, header=False, sep='|')
    else:
        new_df_4.to_csv(path_to_csv, encoding='utf-8', sep='|')

    print('nb rows : ', i * chunksize)
    i += 1

def run_main():
    return 0
