import pandas as pd

if __name__ == '__main__':

    df = pd.read_csv('prediction_per_company_per_rome2019-11-08.csv')
    df_rome_nb_bonne_boite = df.groupby(['rome'])['is a bonne boite ?'].sum()
    df_rome_nb_bonne_boite.to_csv('nb_bonne_boite_per_rome2019-11-089.csv')
