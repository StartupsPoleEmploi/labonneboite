# this script should only be used in development environnement, not in lbbdev nor in test

# FIXME later when we regularly receive new alternance data,
# implement proper "check_alternance" and "extract_alternance" jenkins jobs

# duplicate CDD hirings as APR hirings
insert into hirings(siret, hiring_date, departement, contract_type)
select siret, hiring_date, departement, 11 from hirings where contract_type=1;

# duplicate CDI hirings as CP hirings
insert into hirings(siret, hiring_date, departement, contract_type)
select siret, hiring_date, departement, 12 from hirings where contract_type=2;