# Remove the header
tail -n +2 tableau_LBB_ROMEbis.csv > ../labonneboite/common/data/rome_naf_filter.csv

cp ogr_rome_codes.csv ../labonneboite/common/data/ogr_rome_codes.csv

cp romebis_labels.csv ../labonneboite/common/data/rome_descriptions.csv
