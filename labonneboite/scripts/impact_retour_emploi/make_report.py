import urllib
import shutil
from os import makedirs, remove, listdir
from os.path import abspath, exists
from datetime import date
import pandas as pd
import openpyxl
import openpyxl.styles
from sqlalchemy import create_engine
from labonneboite.scripts.impact_retour_emploi.scripts_charts import charts as charts
from labonneboite.scripts.impact_retour_emploi.scripts_charts import fr_charts as fr
from labonneboite.scripts.impact_retour_emploi.scripts_charts import grand_public as gd
from labonneboite.importer import util as import_util
from labonneboite.importer.jobs.common import logger
from labonneboite.scripts.impact_retour_emploi.settings_path_charts import root_path, clean_path, gd_pub_path, images_path
from settings_path_charts import DEBUG, JOIN_ON_SIREN

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

# FIXME : Refacto all files about the creation of charts and pasting on sheets (<3 Joris)
table_name_act_dpae = 'act_dpae_clean_siren' if JOIN_ON_SIREN is True else 'act_dpae_clean'

def get_infos_from_sql():
    #Get all joined activity logs and dpae CLEAN and NO DUPLICATES
    engine = import_util.create_sqlalchemy_engine()
    query = f'SELECT date_activite, date_embauche, type_contrat, \
                    duree_activite_cdd_mois, duree_activite_cdd_jours,\
                    diff_activite_embauche_jrs, dc_lblprioritede,\
                    tranche_age, dc_privepublic, duree_prise_en_charge,\
                    dn_tailleetablissement, code_postal\
             FROM {table_name_act_dpae}'

    df_act_dpae = pd.read_sql_query(query, engine)

    # Get the evolution of number of IDPEC which log into LBB
    query = '''
    SELECT count(DISTINCT idutilisateur_peconnect) as count_distinct_idpe, MONTH(dateheure), YEAR(dateheure)
    FROM idpe_connect
    GROUP BY MONTH(dateheure), YEAR(dateheure)
    ORDER BY YEAR(dateheure), MONTH(dateheure);
    '''
    idpe_connect = pd.read_sql_query(query, engine)
    month_idpe = idpe_connect['MONTH(dateheure)'].tolist()
    year_idpe = idpe_connect['YEAR(dateheure)'].tolist()

    month_year_idpe = []  # Formatting
    i=0
    while i < len(month_idpe):
        month_year_idpe.append(str(year_idpe[i])+'/'+str(month_idpe[i]))
        i+=1
    idpe_connect['Date'] = month_year_idpe

    # Get the total distinct number which has logged into LBB since start
    query_bis = '''
    SELECT count(DISTINCT idutilisateur_peconnect)
    FROM idpe_connect;
    '''
    total_idpe_connect = pd.read_sql_query(query_bis, engine)

    # Get total of idpe_connect which has logged into Pe connect and made a significative activty about a company
    query_ter = '''
    SELECT count(DISTINCT idutilisateur_peconnect)
    FROM activity_logs;
    '''
    total_idpe_connect_sign = pd.read_sql_query(query_ter, engine)

    print('Getting infos and datas from SQL done !')

    return df_act_dpae, idpe_connect, total_idpe_connect, total_idpe_connect_sign

def make_charts(df_act_dpae, idpe_connect, total_idpe_connect, total_idpe_connect_sign):

    # Creation of all directory needed : We will put everything in /srv/lbb/data on the server
    shutil.rmtree(root_path,ignore_errors=True)
    folders_to_create = [root_path, images_path, gd_pub_path, clean_path]
    for folder in folders_to_create:
        makedirs(folder)

    # Write Datas and Charts in Excel :
    # -------------------------------------
    # Initialisation of the excel sheets
    sheet_names = [None, "BoxPlot + Graph",
                "Détail Embauches", "Pie Charts", "Map", "Cohortes"]
    sheet_sizes = [None, 5, 2, 2, 3]  # Number of files per sheet (start at 0)
    num_sheet = 1

    # First sheet : paste raw datas of the dataframe
    # -------------------------------------
    wb = openpyxl.Workbook()
    wb.save(root_path+'Temporaire.xlsx')
    df_tmp = pd.ExcelWriter(root_path+'Temporaire.xlsx', engine='xlsxwriter')
    df_act_dpae.to_excel(df_tmp, 'DPAE', index=False)
    df_tmp.save()
    book = openpyxl.load_workbook(root_path+'Temporaire.xlsx', data_only=True)

    # Enlarge the columns of the excel document first sheet
    for i in range(len(df_act_dpae.columns.tolist())):
        book.active.column_dimensions[ALPHABET[i]].width = 20

    # next sheets : paste different graphics/maps/Pie/charts etc...
    # ------------------------
    book.create_sheet(sheet_names[num_sheet])
    ws = book.worksheets[num_sheet]
    dict_charts = {('01', "diff_activite_embauche_jrs", "Nombre de Jours entre l'activite sur lbb et la DPAE", "act_emb", 1): charts.BoxPlot,
                ('02', 'duree_activite_cdd_jours', "Durée du CDD obtenu", "cdd_duree", 0): charts.BoxPlot,
                ('03', 'count_distinct_idpe', "Nbre d'IDPE connect par mois", "idpe_connect", 'Date'): charts.graph_sql,
                ('04', 'date_activite', "Nombre d'activités entrainant une DPAE par mois", "act_mo", "month"): charts.Graph,
                ('05', 'date_embauche', "Nombre d'embauches par mois", "emb_mo_gd_public_graph", 'month'): charts.Graph,
                ('07', 'date_embauche', " : Nombre d'embauches par semaine", "emb_sem", 'week'): charts.Graph,
                ('08', "type_contrat", "Type de contrat obtenu", "type_cont_gd_public_pie", None): charts.Pie,
                ('10', "tranche_age", "Pourcentage des differentes tranches d'ages dans les DPAE", "age_gd_public_pie", None): charts.Pie,
                ('11', "dc_privepublic", "Pourcentage d'embauche dans le privé et dans le public", "prive_pub_gd_public_pie", None): charts.Pie,
                ('12', "code_postal", "Part des DPAE par anciennes régions", "old_region_gd_public_svg", "old_region"): fr.map_fr,
                ('13', "code_postal", "Part des DPAE par nouvelles régions", "new_region_gd_public_svg", "new_region"): fr.map_fr,
                ('14', "code_postal", "Part des DPAE par département", "dep_gd_public_svg", "departement"): fr.map_fr,
                ('15', 'date_embauche', ("Total from activity", "Nbre_Total_DPAE", "Mois d'activité",
                    "Mois d'embauche", "Origine de l'Activité,  en fonction du mois d'Embauche"), 'cohorte_1_gd_public', 'date_activite'): charts.Stacked_Bar,
                ('16', 'date_activite', ('Nbre_Total_DPAE', "Total from activity", "Mois d'embauche",
                    "Mois d'activité", "Nombres et Mois d'Embauche,  en fonction du mois d'Activité"), 'cohorte_2_gd_public', 'date_embauche'): charts.Stacked_Bar}


    # Add some important numbers on the first sheet
    #------------------------------------------
    # Add number of DPAE with LBB activity
    nbre_DPAE = df_act_dpae['date_activite'].describe().tolist()[0]
    ws.merge_cells('A4:F4')
    ws.merge_cells('A5:F5')
    cell_A4 = ws['A4']
    cell_A4.value = 'Nbre de DPAE ayant pour origine une activité sur LBB'
    cell_A4.font = openpyxl.styles.Font(size=10, bold=True, underline='double')
    cell_A4.alignment = openpyxl.styles.Alignment(horizontal="center")
    cell_A5 = ws['A5']
    cell_A5.value = nbre_DPAE
    cell_A5.font = openpyxl.styles.Font(size=10, italic=True)
    cell_A5.alignment = openpyxl.styles.Alignment(horizontal="center")
    DPAE_for_gd_pub = [cell_A4.value, nbre_DPAE]  # for grand_public

    # Add number of IDPE unique
    nbre_DPAE = total_idpe_connect.loc[0][0]
    ws.merge_cells('A7:F7')
    ws.merge_cells('A8:F8')
    cell_A7 = ws['A7']
    cell_A7.value = "Nbre d'IDPE connect unique sur LBB depuis 09/18"
    cell_A7.font = openpyxl.styles.Font(size=10, bold=True, underline='double')
    cell_A7.alignment = openpyxl.styles.Alignment(horizontal="center")
    cell_A8 = ws['A8']
    cell_A8.value = nbre_DPAE
    cell_A8.font = openpyxl.styles.Font(size=10, italic=True)
    cell_A8.alignment = openpyxl.styles.Alignment(horizontal="center")
    IDPE_for_gd_pub = [cell_A7.value, nbre_DPAE]  # for grand_public

    # Add number of IDPE unique with significative activity
    nbre_IDPE_sign = total_idpe_connect_sign.loc[0][0]
    ws.merge_cells('A10:F10')
    ws.merge_cells('A11:F11')
    ws.merge_cells('A12:F12')
    cell_A10 = ws['A10']
    cell_A10.value = "Nbre d'IDPE connect unique sur LBB, ayant cliqué sur:"
    cell_A10.font = openpyxl.styles.Font(size=10, bold=True, underline='double')
    cell_A10.alignment = openpyxl.styles.Alignment(horizontal="center")
    cell_A11 = ws['A11']
    cell_A11.value = "'Favoris','Telecharger PDF','Details d'une entreprise' "
    cell_A11.font = openpyxl.styles.Font(size=10, bold=True, underline='double')
    cell_A11.alignment = openpyxl.styles.Alignment(horizontal="center")
    cell_A12 = ws['A12']
    cell_A12.value = nbre_IDPE_sign
    cell_A12.font = openpyxl.styles.Font(size=10, italic=True)
    cell_A12.alignment = openpyxl.styles.Alignment(horizontal="center")
    IDPE_sign_for_gd_pub = [cell_A10.value,
                            nbre_IDPE_sign, cell_A11.value]  # for grand_public


    num_im = 1
    package_svg = []
    all_stats = []

    # Creation and saving of charts, using charts.py
    #-----------------------------
    for args in dict_charts:  
        if 'sql' in dict_charts[args].__name__:  # choose data
            data = idpe_connect
        else:
            data = df_act_dpae

        # Creation of charts/maps in directory "images/"
        image = dict_charts[args](
            args[0], args[1], data, args[2], args[3], args[4])  # a chart function is related to each set of args

        # FIXME : ??? What ???
        # if sem in args, function return the number of graph by "week". It means that creating a new sheet is necessary
        # if sem not in args AND image is not None, it means that the function return a list of stats (for gd_pub sheet)
        if "sem" in args[3]:
            sheet_sizes.insert(2, image-1)
        elif image is not None:
            all_stats.append(image)

    # Pasting of pictures
    def location(num_image, file_name, link=False):  
        if link is True:
            ws.merge_cells("A21:F21")
            ws.merge_cells("G21:L21")
            ws.merge_cells("M21:R21")

            num_image += 3
        list_abscisses = ["A", "G", "M"]
        if "cohorte" in file_name:
            list_abscisses = ["A", "G"]
        y = (((num_image//len(list_abscisses)))*20)+1
        x = list_abscisses[num_image % len(list_abscisses)]
        return x+str(y)

    # Iterate through the created images
    # Pasting of charts from the directory
    for filename in sorted(listdir(images_path)):

        img = openpyxl.drawing.image.Image(images_path+filename)

        if "gd_public" in filename:
            shutil.copyfile(images_path+filename, gd_pub_path+filename)

        if "table" in filename:  # it's the table of cohorte --> it's a different size
            img.anchor = 'H1'
            img.height = 750
            img.width = 900
        else:
            # using the function location in order to place the charts
            img.anchor = location(num_im, filename)
            img.height = 400
            img.width = 500

        ws.add_image(img)  # Pasting

        # if it's map --> pasting web link below charts
        if exists(root_path+filename[:-3]+'svg'):
            cells_link = ws[location(num_im, filename, True)]
            cells_link.hyperlink = filename[:-3]+'svg'
            cells_link.font = openpyxl.styles.Font(
                size=5.5, italic=True, underline='single')
            cells_link.alignment = openpyxl.styles.Alignment(horizontal="center")
            package_svg.append((root_path, filename[:-3]+'svg'))

        num_im += 1

        # if it's the last charts of the sheet --> change sheet
        if num_im == (sheet_sizes[num_sheet]+1):
            try:
                num_sheet += 1
                book.create_sheet(sheet_names[num_sheet])
                ws = book.worksheets[num_sheet]
                num_im = 0
            except:
                pass

    book.save(root_path+'Impact_lbb_DPAE.xlsx')

    # gd_pub sheet
    gd.build_grand_public_sheet(DPAE_for_gd_pub,
                                IDPE_for_gd_pub,
                                IDPE_sign_for_gd_pub,
                                all_stats,
                                book)

    # Remove all files/directory useless and create "Clean" package
    shutil.rmtree(images_path)
    shutil.rmtree(gd_pub_path)
    remove(root_path+"Temporaire.xlsx")
    shutil.copyfile(root_path+'Impact_lbb_DPAE.xlsx', clean_path+'Impact_lbb_DPAE.xlsx')
    for path, svg in package_svg:
        shutil.copyfile(path+svg, clean_path+svg)
    remove(root_path + "filename.html")
    for last_files in listdir(root_path):
        try:
            extension = last_files[last_files.index('.'):]
            if extension == '.svg' or extension == '.xlsx':
                remove(root_path+last_files)
        except:
            pass  # It's a directory


def run_main():
    df_act_dpae, idpe_connect, total_idpe_connect, total_idpe_connect_sign = get_infos_from_sql()
    make_charts(df_act_dpae, idpe_connect, total_idpe_connect, total_idpe_connect_sign)

if __name__ == '__main__':
    run_main()