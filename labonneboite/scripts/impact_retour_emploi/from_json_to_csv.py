import json
import urllib.parse
import os
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('mysql://labonneboite:%s@127.0.0.1:3306/labonneboite' %urllib.parse.quote_plus('LaB@nneB@ite'))
engine.connect()

data=[]

json_path='/mnt/datalakepe/vers_datalake/activity/'
#json_path='/home/ads/Documents/labonneboite/labonneboite/importer/jobs/scripts_tre/'
liste_files=os.listdir(json_path)
liste_files.sort()
json_files=liste_files[-1]

with open(json_path+json_files,'r') as json_files:
    for line in json_files:
        data.append(line)
activity_dico={}
i=1
for line in data:
    activity_dico[str(i)]=json.loads(line)
    i+=1

table_activity=pd.DataFrame.from_dict(activity_dico).transpose()

def idpe_only(row):
    if row['idutilisateur-peconnect']==None:
        return 0
    else : return 1

table_activity['provisoire']=table_activity.apply(lambda row:idpe_only(row),axis=1)
table_activity=table_activity[table_activity.provisoire != 0]
table_activity_2_bis= table_activity.drop_duplicates(subset=['idutilisateur-peconnect'], keep='first')

table_activity_2_bis=table_activity_2_bis[['dateheure','idutilisateur-peconnect']]
table_activity_2_bis.to_sql(con=engine, name='idpe_connect', if_exists='append',index=False)

cliks_of_interest=['details','afficher-details','telecharger-pdf','ajout-favori']

def tri_nom(row):
    if row['nom'] in cliks_of_interest:
        return True
    else : 
        return False

table_activity['to_tej'] = table_activity.apply(lambda row: tri_nom(row), axis=1)
table_activity_2 = table_activity[table_activity.to_tej == True]

def siret(row):
    return row['proprietes']['siret']

table_activity_2['siret'] = table_activity_2.apply(lambda row: siret(row), axis=1)
cols_of_interest=["dateheure","nom","idutilisateur-peconnect","siret"]
table_activity_3=table_activity_2[cols_of_interest]
table_activity_3.to_sql(con=engine, name='activity_logs', if_exists='append',index=False)
