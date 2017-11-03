#
# SQL Export
# Created by Querious (1068)
# Created: 20 October 2017 at 17:52:24 GMT+2
# Encoding: Unicode (UTF-8)
#


SET @PREVIOUS_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;


DROP TABLE IF EXISTS `etablissements_importer`;


CREATE TABLE `etablissements_importer` (
  `siret` varchar(255) DEFAULT NULL,
  `raisonsociale` varchar(255) DEFAULT NULL,
  `enseigne` varchar(255) DEFAULT NULL,
  `codenaf` varchar(255) DEFAULT NULL,
  `trancheeffectif` varchar(255) DEFAULT NULL,
  `numerorue` varchar(255) DEFAULT NULL,
  `libellerue` varchar(255) DEFAULT NULL,
  `codepostal` varchar(255) DEFAULT NULL,
  `tel` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `company_datecreation` varchar(255) DEFAULT NULL,
  `codecommune` varchar(255) DEFAULT NULL,
  `departement` varchar(8) DEFAULT NULL,
  `website1` varchar(255) DEFAULT NULL,
  `website2` varchar(255) DEFAULT NULL,
  KEY `dept_i` (`departement`),
  KEY `trancheeffectif` (`trancheeffectif`),
  KEY `codepostal` (`codepostal`),
  KEY `codecommune` (`codecommune`),
  KEY `siret` (`siret`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;




SET FOREIGN_KEY_CHECKS = @PREVIOUS_FOREIGN_KEY_CHECKS;


