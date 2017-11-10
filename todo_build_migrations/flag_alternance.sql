#
# SQL Export
# Created by Querious (201012)
# Created: 10 November 2017 at 11:56:05 GMT+1
# Encoding: Unicode (UTF-8)
#


SET @PREVIOUS_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;


DROP TABLE IF EXISTS `flag_alternance`;


CREATE TABLE `flag_alternance` (
  `siret` varchar(191) NOT NULL DEFAULT '',
  PRIMARY KEY (`siret`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



SET FOREIGN_KEY_CHECKS = @PREVIOUS_FOREIGN_KEY_CHECKS;


