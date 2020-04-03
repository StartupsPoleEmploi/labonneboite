import os
import pandas as pd

# NOT DONE TO RUN IN LOCAL DEV
# A util script to run outside the current lbb dev to check validity of files values sent by datalake
# To copy and paste on the importer server (Bonaparte) where data are located


class DatalakeFile:

    def __init__(self, file_type='etab'):
        self.file_type = file_type
        self.datalake_files_folder_path = '/srv/lbb/data'
        self.most_recent_file = self.get_most_recent_file()

    def get_most_recent_file(self):
        file_paths = os.listdir(self.datalake_files_folder_path)
        token_file = 'lbb_etablissement_full_' if self.file_type == 'etab' else 'lbb_xdpdpae_delta'

        file_paths = [i for i in file_paths if i.startswith(token_file)]

        file_paths.sort()
        most_recent_file = file_paths[-1]

        print(f"the {self.file_type} file which will be used is : {most_recent_file}")

        return most_recent_file

    def get_compression_to_use_by_pandas_according_to_file(self):
        file_extension = self.most_recent_file.split('.')[-1]
        compression = 'infer' if file_extension == 'csv' else 'bz2'

        return compression

    def read_file(self):
        df = pd.read_csv(
            f"{self.datalake_files_folder_path}/{self.most_recent_file}",
            compression=self.get_compression_to_use_by_pandas_according_to_file(),
            sep='|',
            index_col=False)

        return df

# METHODS ETABLISSEMENTS
# ----------------------

# For etablissement file : Print the lines that are related to a siret
# Example : Check some fields that seem to contain wrong values for a specific siret
# Used it when we wantee to check the effectif field for this specific siret
def filter_on_siret_etab(self, df, siret):
    df_filtre = df[df.dc_siretetablissement == siret]
    print(df_filtre)

# Here, we needed to extract all mail cleans that datalake sent us via the etablissement file
def extract_mail_clean_etab(self, df):
    df = df[['dc_siretetablissement', 'dc_raisonsocialeentreprise', 'dc_emailcorrespondant']]
    df = df.dropna(subset=['dc_emailcorrespondant'])
    df = df.drop_duplicates()
    df.to_csv('/srv/lbb/data/mail_clean_entreprises.csv')

# Main function for établissement
def run_function_etab():
    etab_data = DatalakeFile('etab')
    df = etab_data.read_file()
    # extract_mail_clean(df)
    #filter_on_siret_etab(df, 44443604200261)

# METHODS DPAE
# ----------------------

def filter_on_siret_dpae(self, df, siret):
    df_filtre = df[df.kc_siret == siret]
    print(df_filtre)

# Main function for dpae
def run_function_dpae():
    etab_data = DatalakeFile('dpae')
    df = etab_data.read_file()
    #filter_on_siret_dpae(df, 44443604200261)


if __name__ == '__main__':
    # run_function_dpae()
    run_function_etab()
