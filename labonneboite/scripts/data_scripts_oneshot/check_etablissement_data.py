import pandas as pd
import os

class EtablissementData:

    def __init__(self):
        self.etablissement_folder_path = '/srv/lbb/data/'
        self.most_recent_etablissement_file = self.get_most_recent_etablissement_file()

    def get_most_recent_etablissement_file(self):
        etablissement_paths = os.listdir(self.etablissement_folder_path)
        # IMPORTANT : Need to copy the etablissement file from /mnt/datalakepe/ to /srv/lbb/data
        # It is certainly ok, because of the importer which also needs this file
        etablissement_paths = [i for i in etablissement_paths if i.startswith('lbb_etablissement_full_')]

        etablissement_paths.sort()
        most_recent_etablissement_file = etablissement_paths[-1]

        print(f"the etablissement file which will be used is : {most_recent_etablissement_file}")

        return most_recent_etablissement_file

    def get_compression_to_use_by_pandas_according_to_file(self):
        etablissement_file_extension = self.most_recent_etablissement_file.split('.')[-1]
        if etablissement_file_extension == 'csv':
            compression = 'infer'
        else:
            compression = 'bz2'
        
        return compression
    
    def read_file(self):
        df_etab = pd.read_csv(
            self.etablissement_folder_path + self.most_recent_etablissement_file,
            compression=self.get_compression_to_use_by_pandas_according_to_file(),
            sep='|',
            index_col=False)

        return df_etab

    def filter_on_siret(self,df_etab):
        df_filtre = df_etab[df_etab.dc_siretetablissement == 44443604200261]
        import ipdb; ipdb.set_trace()

    def extract_mail_clean(self, df_etab):
        df_etab= df_etab[['dc_siretetablissement','dc_raisonsocialeentreprise','dc_emailcorrespondant']]
        df_etab = df_etab.dropna(subset=['dc_emailcorrespondant'])
        df_etab = df_etab.drop_duplicates()
        df_etab.to_csv('/srv/lbb/data/mail_clean_entreprises.csv')
        #dc_adressemailetablissement = mail principal ___ dc_emailcorrespondant=RGPD

     


if __name__ == '__main__':
    etab_data = EtablissementData()
    df = etab_data.read_file()
    etab_data.extract_mail_clean(df)
