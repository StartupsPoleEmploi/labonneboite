import pygal
import pandas as pd
from os import *
from os.path import *

path = abspath('charts.py')[:-9]+'images/'

# Correspondence n° of department with n° of regions in pygal.
REG_DEP = {'01': '82',
           '02': '22',
           '03': '83',
           '04': '93',
           '05': '93',
           '06': '93',
           '07': '82',
           '08': '12',
           '09': '73',
           '10': '21',
           '11': '91',
           '12': '73',
           '13': '93',
           '14': '25',
           '15': '83',
           '16': '54',
           '17': '54',
           '18': '24',
           '19': '74',
           '2A': '94',
           '2B': '94',
           '21': '26',
           '22': '53',
           '23': '74',
           '24': '72',
           '25': '43',
           '26': '82',
           '27': '23',
           '28': '24',
           '29': '53',
           '30': '91',
           '31': '73',
           '32': '73',
           '33': '72',
           '34': '91',
           '35': '53',
           '36': '24',
           '37': '24',
           '38': '82',
           '39': '43',
           '40': '72',
           '41': '24',
           '42': '82',
           '43': '83',
           '44': '52',
           '45': '24',
           '46': '73',
           '47': '72',
           '48': '91',
           '49': '52',
           '50': '25',
           '51': '21',
           '52': '21',
           '53': '52',
           '54': '41',
           '55': '41',
           '56': '53',
           '57': '41',
           '58': '26',
           '59': '31',
           '60': '22',
           '61': '25',
           '62': '31',
           '63': '83',
           '64': '72',
           '65': '73',
           '66': '91',
           '67': '42',
           '68': '42',
           '69': '82',
           '70': '43',
           '71': '26',
           '72': '52',
           '73': '82',
           '74': '82',
           '75': '11',
           '76': '23',
           '77': '11',
           '78': '11',
           '79': '54',
           '80': '22',
           '81': '73',
           '82': '73',
           '83': '93',
           '84': '93',
           '85': '52',
           '86': '54',
           '87': '74',
           '88': '41',
           '89': '26',
           '90': '43',
           '91': '11',
           '92': '11',
           '93': '11',
           '94': '11',
           '95': '11',
           '971': '01',
           '972': '02',
           '973': '03',
           '974': '04',
           '975': '05',
           '977': '01',
           '976': '06',
           '978': '01'}

# Gather n° of old regions in new regions.
NEW = [['42', '41', '21'],
       ['72', '74', '54'],
       ['82', '83'],
       ['26', '43'],
       ['53'],
       ['24'],
       ['94'],
       ['11'],
       ['91', '73'],
       ['31', '22'],
       ['23', '25'],
       ['52'],
       ['93'],
       ['01'],
       ['02'],
       ['03'],
       ['04'],
       ['05'],
       ['06']
       ]

# Correpondence of each types request with the subdvision (dep/region) :
Type = {'old_region': (lambda x: REG_DEP[x], pygal.maps.fr.Regions()),
        'new_region': (lambda x: REG_DEP[x], pygal.maps.fr.Regions()),
        'departement': (lambda x: x, pygal.maps.fr.Departments())
        }


def map(ordre, columns_code_postal, df, title, name, subdivision):
    df_copy = pd.DataFrame.copy(df)

    # Give department, and the region if it's request
    def get_subdvision(row):
        if row[columns_code_postal][:2] != '97':
            return Type[subdivision][0](row[columns_code_postal][:2])
        else:
            return Type[subdivision][0](row[columns_code_postal][:3])

    df_copy[columns_code_postal] = df_copy.apply(
        lambda row: get_subdvision(row), axis=1)

    # create dictionnary with the department/region associate to the numbers of DPAE
    postal_codes = df_copy[columns_code_postal]
    occurences = postal_codes.value_counts()
    subdivision_nb_dpae = occurences.to_dict()

    # gather the DPAE on the new regions if it's request
    if subdivision[:3] == 'new':
        total_dpae = 0
        region_dpae_bis = {}
        for grouping_old_region in NEW:
            for old_region in grouping_old_region:
                try:
                    total_dpae += subdivision_nb_dpae[old_region]
                except:
                    None
            for old_region in grouping_old_region:
                region_dpae_bis[old_region] = total_dpae
            total_dpae = 0
        subdivision_nb_dpae = region_dpae_bis

    # create and save the sharts
    fr_chart = Type[subdivision][1]
    fr_chart.title = title
    fr_chart.add('DPAE', subdivision_nb_dpae)
    fr_chart.render_to_png(path+ordre+name+'.png')
    fr_chart.render_to_file(ordre+name+'.svg')


'''
11 	Île-de-France
21 	Champagne-Ardenne
22 	Picardie
23 	Haute-Normandie
24 	Centre
25 	Basse-Normandie
26 	Bourgogne
31 	Nord-Pas-de-Calais
41 	Lorraine
42 	Alsace
43 	Franche-Comté
52 	Pays-de-la-Loire
53 	Bretagne
54 	Poitou-Charentes
72 	Aquitaine
73 	Midi-Pyrénées
74 	Limousin
82 	Rhône-Alpes
83 	Auvergne
91 	Languedoc-Roussillon
93 	Provence-Alpes-Côte d’Azur
94 	Corse
01 	Guadeloupe
02 	Martinique
03 	Guyane
04 	Réunion
05 	Saint Pierre et Miquelon
06 	Mayotte
'''
