# Create the test DB and populate it with tables which doesn't exists in our models module.

# SQL Export
# Created by Querious (1068)
# Encoding: Unicode (UTF-8)

DROP DATABASE IF EXISTS `lbb_test2`;
CREATE DATABASE `lbb_test2` DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;
USE `lbb_test2`;

SET @PREVIOUS_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `import_tasks`;
DROP TABLE IF EXISTS `geolocations`;
DROP TABLE IF EXISTS `etablissements_prod`;
DROP TABLE IF EXISTS `dpae_statistics`;
DROP TABLE IF EXISTS `dpae`;


CREATE TABLE `dpae` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `siret` varchar(191) DEFAULT NULL,
  `hiring_date` datetime DEFAULT NULL,
  `zipcode` varchar(8) DEFAULT NULL,
  `contract_type` int(11) DEFAULT NULL,
  `departement` varchar(8) DEFAULT NULL,
  `contract_duration` int(11) DEFAULT NULL,
  `iiann` varchar(191) DEFAULT NULL,
  `tranche_age` varchar(191) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE `dpae_statistics` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `last_import` datetime DEFAULT NULL,
  `most_recent_data_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE `etablissements_prod` (
  `siret` varchar(191) NOT NULL,
  `raisonsociale` varchar(191) DEFAULT NULL,
  `enseigne` varchar(191) DEFAULT NULL,
  `codenaf` varchar(8) DEFAULT NULL,
  `numerorue` varchar(191) DEFAULT NULL,
  `libellerue` varchar(191) DEFAULT NULL,
  `codecommune` varchar(191) DEFAULT NULL,
  `codepostal` varchar(8) DEFAULT NULL,
  `email` varchar(191) DEFAULT NULL,
  `tel` varchar(191) DEFAULT NULL,
  `departement` varchar(8) DEFAULT NULL,
  `trancheeffectif` varchar(2) DEFAULT NULL,
  `score` int(11) DEFAULT NULL,
  `website1` varchar(191) DEFAULT NULL,
  `website2` varchar(191) DEFAULT NULL,
  PRIMARY KEY (`siret`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE `geolocations` (
  `full_address` varchar(191) NOT NULL,
  `coordinates_x` float DEFAULT NULL,
  `coordinates_y` float DEFAULT NULL,
  PRIMARY KEY (`full_address`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE `import_tasks` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `filename` varchar(191) DEFAULT NULL,
  `state` int(11) DEFAULT NULL,
  `import_type` int(11) DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


LOCK TABLES `dpae` WRITE;
ALTER TABLE `dpae` DISABLE KEYS;
ALTER TABLE `dpae` ENABLE KEYS;
UNLOCK TABLES;


LOCK TABLES `dpae_statistics` WRITE;
ALTER TABLE `dpae_statistics` DISABLE KEYS;
ALTER TABLE `dpae_statistics` ENABLE KEYS;
UNLOCK TABLES;


LOCK TABLES `etablissements_prod` WRITE;
ALTER TABLE `etablissements_prod` DISABLE KEYS;
ALTER TABLE `etablissements_prod` ENABLE KEYS;
UNLOCK TABLES;


LOCK TABLES `geolocations` WRITE;
ALTER TABLE `geolocations` DISABLE KEYS;
ALTER TABLE `geolocations` ENABLE KEYS;
UNLOCK TABLES;


LOCK TABLES `import_tasks` WRITE;
ALTER TABLE `import_tasks` DISABLE KEYS;
ALTER TABLE `import_tasks` ENABLE KEYS;
UNLOCK TABLES;


SET FOREIGN_KEY_CHECKS = @PREVIOUS_FOREIGN_KEY_CHECKS;
