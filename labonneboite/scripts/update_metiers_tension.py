import pandas as pd


# get csv file from : https://statistiques.pole-emploi.org/bmo/bmo?in=4&lg=0&pp=2019&ss=1#
# To build a new file, we join the old file with the new one and we update the percentage of tension for each rome/fap


def format_tension(row):
    return float(row["tension_pct_new"].replace("%", "").replace(",", ".").strip())


def update_percentages():

    # Format new tension file
    df_new_tension = pd.read_csv("common/data/new_metiers_tension_2020.csv", sep=";")
    df_new_tension.rename(columns={"Métier": "fap", "Difficultés à recruter": "tension_pct_new"}, inplace=True)

    df_new_tension["tension_pct_new"] = df_new_tension.apply(lambda row: format_tension(row), axis=1)

    # Format old tension file
    df_old_tension = pd.read_csv("common/data/metiers_tension.csv", sep=",")
    # In the right order, the fap codes to change : E1Z42, K0Z40, U1Z82, E1Z41, E1Z40, D1Z40, D2Z42
    dict_new_names_fap = {
        "Ouvriers qualifiés des industries agroalimentaires (hors viandes)": "Autres ouvriers qualifiés des industries agro-alimentaires (hors transformation des viandes)",
        "Ouvriers qualifiés divers de type artisanal (reliure, gravure, métallerie d'art…)": "Artisans et ouvriers qualifiés divers de type artisanal",
        "Graphistes, dessinateurs, stylistes, décorateurs, créateurs supports…": "Créateurs de supports de communication visuelle, stylistes, décorateurs",
        "Ouvriers qualifiés des industries chimiques et plastiques": "Autres ouvriers qualifiés des industries chimiques et plastiques",
        "Pilotes d'installations lourdes des industries de transformation": "Pilotes d'installation lourde des industries de transformation",
        "Régleurs qualifiés": "Régleurs",
        "Soudeurs qualifiés": "Soudeurs",
    }

    df_old_tension = df_old_tension.replace({"fap": dict_new_names_fap})  # 701 rows

    # Merge both dataframes on the fap name (would have been easier to do it on the fap code, but not available in new data)
    df_merge = df_old_tension.merge(df_new_tension, how="left")

    """
     Stats checks :

     Still 701 rows in old file, and merge fab, with no null tension pourcentage, merge is done

     Mean of the old percentages :
     df_old_tension.tension_pct.mean()
     49.69557774607703

    ipdb> df_old_tension.tension_pct.describe()
    count    701.000000
    mean      49.695578
    std       14.210388
    min       16.300000
    25%       41.200000
    50%       49.100000
    75%       61.100000
    max       86.300000

     Mean of the new percentages :
     df_merge.tension_pct_new.mean()
     53.52881597717546

    ipdb> df_merge.tension_pct_new.describe()
    count    701.000000
    mean      53.528816
    std       14.678187
    min       11.800000
    25%       43.800000
    50%       52.900000
    75%       66.400000
    max       86.200000

     --> The update does not change the global statistics
    """

    # keep only wanted columns
    columns_of_interest = ["fap_code", "fap", "tension_pct_new", "rome_code", "rome_label"]

    df_merge = df_merge[columns_of_interest]

    df_merge.rename(columns={"tension_pct_new": "tension_pct"}, inplace=True)

    # Save new dataset to csv
    df_merge.to_csv("common/data/metiers_tension.csv", encoding="utf-8", sep=",", index=False)


if __name__ == "__main__":
    update_percentages()
