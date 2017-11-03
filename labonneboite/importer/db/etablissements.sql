DROP TABLE if exists etablissements;

CREATE TABLE etablissements (
  siret varchar(191),
  raisonsociale varchar(191) DEFAULT NULL,
  enseigne varchar(191) DEFAULT NULL,
  codenaf varchar(191) DEFAULT NULL,
  trancheeffectif varchar(191) DEFAULT NULL,
  numerorue varchar(191) DEFAULT NULL,
  libellerue varchar(191) DEFAULT NULL,
  codepostal varchar(8) DEFAULT NULL,
  tel varchar(191) DEFAULT NULL,
  email varchar(191) DEFAULT NULL,
  website varchar(191) DEFAULT NULL,
  flag_alternance tinyint(1) NOT NULL,
  flag_junior tinyint(1) NOT NULL,
  flag_senior tinyint(1) NOT NULL,
  flag_handicap tinyint(1) NOT NULL,
  has_multi_geolocations tinyint(1) NOT NULL,
  codecommune varchar(191) DEFAULT NULL,
  coordinates_x double DEFAULT NULL,
  coordinates_y double DEFAULT NULL,
  departement varchar(8) DEFAULT NULL,
  score int(11) DEFAULT NULL,
  PRIMARY KEY (siret),
  KEY dept_i (departement)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
