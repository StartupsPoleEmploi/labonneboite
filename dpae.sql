#
# SQL Export
# Created by Querious (201009)
# Created: 27 October 2017 at 18:21:11 GMT+2
# Encoding: Unicode (UTF-8)
#


SET @PREVIOUS_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;


DROP TABLE IF EXISTS `dpae`;


CREATE TABLE `dpae` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `siret` varchar(255) NOT NULL DEFAULT '',
  `hiring_date` datetime DEFAULT NULL,
  `zipcode` int(11) DEFAULT NULL,
  `contract_type` int(11) DEFAULT NULL,
  `departement` varchar(8) DEFAULT NULL,
  `contract_duration` int(11) DEFAULT NULL,
  `iiann` varchar(255) DEFAULT NULL,
  `tranche_age` varchar(255) DEFAULT NULL,
  `handicap_label` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `departement_i` (`departement`),
  KEY `siret` (`siret`),
  KEY `contract_type` (`contract_type`),
  KEY `zipcode` (`zipcode`),
  KEY `contract_duration` (`contract_duration`),
  KEY `hiring_date` (`hiring_date`),
  KEY `tranche_age` (`tranche_age`)
) ENGINE=InnoDB AUTO_INCREMENT=287266203 DEFAULT CHARSET=utf8;




SET FOREIGN_KEY_CHECKS = @PREVIOUS_FOREIGN_KEY_CHECKS;


