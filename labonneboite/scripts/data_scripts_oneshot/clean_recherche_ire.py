import urllib
import shutil
import calendar
import pandas as pd
import os.path
import numpy
from os import makedirs, remove, listdir
from datetime import date
import string

from labonneboite.importer import util as import_util
from labonneboite.importer.jobs.common import logger
from labonneboite.importer import settings as importer_settings
from labonneboite.scripts.impact_retour_emploi.google_sheets_report import GoogleSheetReport, generate_google_sheet_service
    
def clean_emploi(row):
    def hasNumbers(inputString):
        return any(char.isdigit() for char in inputString)

    emploi = row['emploi']
    try:
        #example : "soins-d-hygiene-de-confort-du-patient99999' union select unhex(hex(version
        if ' ' in emploi:
            emploi = emploi.split(' ')[0]
        #example : securite-et-surveillance-privees/static/images/logo-lbb.svg
        if '/' in emploi:
            emploi = emploi.split('/')[0]
        #example : tel:0590482468
        if emploi.startswith('tel:'):
            emploi = ''
        #example :vente-en-habillement-et-accessoires-de-la-personne?to=82&from=81&sa=U&ved=2ahUKEwiLqI6mi43mAhVD6aQKHVxyAP4QFjAOegQIRxAB&usg=AOvVaw1hYvyYvxE3CPZnYly-CKci"
        if '?' in emploi:
            emploi = emploi.split('?')[0]
        # example : vente-en-habillement-et-accessoires-de-la-personne%Fto=&from=&d=
        if '%' in emploi:
            emploi = emploi.split('%')[0]
        # example : 'conduite-de-transport-en-commun-sur-route&sa=U&ved=ahUKEwjhlZvHv_kAhUKqlkKHRJyCNQFjAWegQIDBAB&usg=AOvVawWAKqGLFCkVOTiWqLfJXF"'            
        if '&' in emploi:
            emploi = emploi.split('&')[0]
        # example : soins-d-hygiene-de-confort-du-patient99999
        if hasNumbers(emploi):
            emploi = ''.join([i for i in emploi if not i.isdigit()])
        # example : soins-d-hygiene-de-confort-du-patient\'"
        if '\'' in emploi:
            emploi = emploi.split('\'')[0]
        #example : www.orecrute.fr
        if emploi.startswith('www'):
            emploi = ''
        #example : '...'
        if emploi.endswith('..'):
            emploi = ''
        #example : '�'
        if len(emploi) == 1:
            emploi = ''
        #example '||UTL_INADDR.get_host_address(', 
        if emploi.startswith('||'):
            emploi = ''
        #example {{__field_friYEMKBPT}}']
        if emploi.startswith('{'):
            emploi = ''
        #exampleS : 
        # '"><javascript:alert(String.fromCharCode(,,));">', '"><script',
        # '(SELECT', '-"', '-)', '-);select', '..', ';copy', '@@AMfqT',
        #'@@Ddywc', '@@EnFdC', '@@JOQK', '@@LAdgd', '@@MlSoU', '@@QKchw',
        #'@@Rido', '@@WiWWC', '@@XFdfe', '@@ZIdkt', '@@bLTT', '@@gZP',
        #'@@lMTz', '@@nc', '@@ozw', '@@uusYI', '@@zRlWc', '@@ziuX',
        if ('<' or '>') in emploi:
            emploi = ''
        if emploi.startswith('>'):
            emploi = ''
        if ';' in emploi:
            emploi = ''
        if emploi.startswith('('):
            emploi = ''
        if emploi.startswith('('):
            emploi = ''
        if emploi.startswith('@'):
            emploi = ''
        if '\"' in emploi:
            emploi.replace('\"','')
        if '.' in emploi:
            emploi.replace('.','')
        if 'test' in emploi:
            emploi = ''

    except TypeError: #If emploi is NoneType
        emploi = ''

    return emploi

def clean_logs_recherche_emploi():
    # GET the evolution of the number of dpae with LBB activity
    engine = import_util.create_sqlalchemy_engine()
    query = 'SELECT * FROM logs_activity_recherche ORDER BY RAND()'
    df_recherche = pd.read_sql_query(query, engine)
    df_recherche['emploi'] = df_recherche.apply(lambda row: clean_emploi(row), axis=1)
    
    unique_values = df_recherche['emploi'].unique()
    unique_values.sort()

    import ipdb; ipdb.set_trace()

        
    df_recherche.to_sql(
        con=engine,
        name='logs_activity_recherche_fix',
        if_exists='append', 
        index=False, 
        chunksize=10000
    )

    engine.close()


if __name__ == '__main__':
    clean_logs_recherche_emploi()