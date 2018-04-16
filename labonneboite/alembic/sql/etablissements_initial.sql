# this script should only run in local development and BEFORE any migration

# FIXME transform this script into a migration, very early in the migration tree,
# or even make it the initial migration

#
# SQL Export
# Created by Querious (1068)
# Created: 14 July 2017 at 16:18:36 GMT+2
# Encoding: Unicode (UTF-8)
#


SET @PREVIOUS_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `etablissements`;

CREATE TABLE `etablissements` (
  `siret` varchar(191) NOT NULL,
  `raisonsociale` varchar(191) DEFAULT NULL,
  `enseigne` varchar(191) DEFAULT NULL,
  `codenaf` varchar(191) DEFAULT NULL,
  `numerorue` varchar(191) DEFAULT NULL,
  `libellerue` varchar(191) DEFAULT NULL,
  `codecommune` varchar(191) DEFAULT NULL,
  `codepostal` varchar(11) DEFAULT NULL,
  `email` varchar(191) DEFAULT NULL,
  `tel` varchar(191) DEFAULT NULL,
  `departement` varchar(11) DEFAULT NULL,
  `trancheeffectif` varchar(191) DEFAULT NULL,
  `score` int(11) DEFAULT NULL,
  `coordinates_x` float DEFAULT NULL,
  `coordinates_y` float DEFAULT NULL,
  `website` varchar(191) DEFAULT NULL,
  `flag_alternance` tinyint(1) NOT NULL,
  `flag_junior` tinyint(1) NOT NULL,
  `flag_senior` tinyint(1) NOT NULL,
  `flag_handicap` tinyint(1) NOT NULL,
  `has_multi_geolocations` tinyint(1) NOT NULL,
  PRIMARY KEY (`siret`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
ALTER TABLE `etablissements` ENABLE KEYS;
UNLOCK TABLES;


SET FOREIGN_KEY_CHECKS = @PREVIOUS_FOREIGN_KEY_CHECKS;


