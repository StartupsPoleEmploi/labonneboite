#
# SQL Export
# Created by Querious (201009)
# Created: 27 October 2017 at 18:15:05 GMT+2
# Encoding: Unicode (UTF-8)
#


SET @PREVIOUS_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;


DROP TABLE IF EXISTS `dpae_statistics`;


CREATE TABLE `dpae_statistics` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `last_import` datetime DEFAULT NULL,
  `most_recent_data_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;




SET FOREIGN_KEY_CHECKS = @PREVIOUS_FOREIGN_KEY_CHECKS;


