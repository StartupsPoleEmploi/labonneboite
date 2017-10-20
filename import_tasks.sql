#
# SQL Export
# Created by Querious (1068)
# Created: 20 October 2017 at 14:19:35 GMT+2
# Encoding: Unicode (UTF-8)
#


SET @PREVIOUS_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;


DROP TABLE IF EXISTS `import_tasks`;


CREATE TABLE `import_tasks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `state` int(11) DEFAULT '0',
  `import_type` int(11) DEFAULT '0',
  `created_date` datetime DEFAULT NULL,
#  DEFAULT CURRENT_TIMESTAMP supported on percona (lbbdev) but not on MariaDB
#  `created_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `filename` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=111 DEFAULT CHARSET=utf8;




SET FOREIGN_KEY_CHECKS = @PREVIOUS_FOREIGN_KEY_CHECKS;


SET @PREVIOUS_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;


LOCK TABLES `import_tasks` WRITE;
ALTER TABLE `import_tasks` DISABLE KEYS;
INSERT INTO `import_tasks` (`id`, `state`, `import_type`, `created_date`, `filename`) VALUES 
	(1,2,2,'2015-10-30 13:53:47','dpae_MA11239_2015.tbl.gz'),
	(8,3,2,'2015-11-12 14:03:33','etablissements_20150311.txt'),
	(9,2,2,'2016-01-25 10:04:55','dpae_MA11343_2015.tbl.gz'),
	(10,1,2,'2016-01-25 13:36:55','dpae_MA11595_XDPDPA_DPAE_2015.tbl.gz'),
	(11,2,2,'2016-01-25 15:49:44','dpae_MA11595_XDPDPA_DPAE_NEW_TEST_2015.tbl.gz'),
	(12,2,2,'2016-01-26 21:35:00','dpae_MA11595_XDPDPA_DPAE_importer_bug_fixed_2015.tbl.gz'),
	(13,2,2,'2016-01-27 17:06:56','dpae_MA11595_XDPDPA_DPAE_importer_bug_0x_departement_fixed_2015.tbl.gz'),
	(15,3,2,'2016-02-29 15:59:20','etablissements_20150311_dom_corse.txt'),
	(16,3,2,'2016-03-08 16:20:40','etablissements_20150311_dom_corse_verbose.txt'),
	(17,3,2,'2016-03-09 09:42:01','etablissements_20150311_dom_corse_verbose_v2.txt'),
	(18,3,2,'2016-03-09 10:29:35','etablissements_20150311_dom_corse_verbose_v3.txt'),
	(19,3,2,'2016-03-09 14:25:03','etablissements_20150311_dom_corse_verbose_v4.txt'),
	(20,3,2,'2016-03-09 15:35:10','etablissements_20150311_dom_corse_verbose_v5.txt'),
	(21,3,2,'2016-03-10 09:34:27','etablissements_20150311_dom_corse_verbose_v6.txt'),
	(22,3,2,'2016-03-17 15:48:42','etablissements_20150311_dom_corse_verbose_v7.txt'),
	(23,3,2,'2016-03-22 09:46:24','etablissements_20150311_dom_corse_verbose_v8.txt'),
	(24,3,2,'2016-03-23 10:02:41','etablissements_MA11785.txt'),
	(25,3,2,'2016-03-23 11:04:18','etablissements_MA11785_v2.txt'),
	(28,2,2,'2016-03-29 10:18:21','dpae_MA11761_XDPDPA_DPAE_2015.tbl.gz'),
	(29,3,2,'2016-03-31 13:42:01','etablissements_MA11785_v3.txt'),
	(30,3,2,'2016-03-31 13:59:18','etablissements_MA11785_v4.txt'),
	(31,3,2,'2016-03-31 14:39:59','etablissements_MA11785_v5.txt'),
	(32,3,2,'2016-03-31 16:03:30','etablissements_MA11785_v6.txt'),
	(33,3,2,'2016-03-31 16:22:32','etablissements_MA11785_v7.txt'),
	(34,3,2,'2016-03-31 16:43:57','etablissements_MA11785_v8.txt'),
	(35,3,2,'2016-04-01 12:18:18','etablissements_MA11785_v9.txt'),
	(36,3,2,'2016-04-01 12:52:27','etablissements_MA11785_v10.txt'),
	(37,3,2,'2016-04-06 14:28:04','etablissements_M11823.tbl'),
	(38,2,2,'2016-05-11 14:58:00','etablissements_MA11785_v11.txt'),
	(39,3,2,'2016-05-12 09:14:02','etablissements_MA11785_v12.txt'),
	(40,3,2,'2016-05-12 09:48:06','etablissements_MA11785_v13.txt'),
	(41,1,2,'2016-05-12 10:32:16','etablissements_MA11785_v14.txt'),
	(42,3,2,'2016-05-12 13:32:58','etablissements_MA11785_v15.txt'),
	(43,1,2,'2016-05-12 14:12:11','etablissements_MA11785_v16.txt'),
	(44,3,2,'2016-05-17 14:32:39','etablissements_MA11785_v17.txt'),
	(45,3,2,'2016-05-17 14:33:27','etablissements_MA11785_v18.txt'),
	(46,2,2,'2016-05-17 14:59:47','etablissements_MA11785_v19.txt'),
	(47,3,2,'2016-05-26 14:24:36','dpae_MA11984_XDPDPA_DPAE_201503-201605.tbl.gz'),
	(48,3,2,'2016-05-27 08:23:12','dpae_MA11984_XDPDPA_DPAE_201503-201605_v2.tbl.gz'),
	(49,2,2,'2016-05-30 08:32:18','dpae_MA11984_XDPDPA_DPAE_201503-201605_not_corrupted.tbl.gz'),
	(65,1,2,'2016-07-28 12:56:28','etablissements_MA11785_tests.tbl.gz'),
	(66,1,1,'2016-07-28 15:24:04','dpae_file_MA11984_XDPDPA_DPAE_201503-201605.tbl.gz'),
	(67,1,2,'2016-08-03 13:18:19','etablissements_MA11785_tests_v2.tbl.gz'),
	(68,1,1,'2016-08-31 15:32:07','dpae_XDPDPA_DPAE_2016_08_17.tar.gz'),
	(69,1,1,'2016-08-31 15:52:32','dpae_XDPDPA_DPAE_20160817.tar.gz'),
	(71,1,2,'2016-09-15 13:25:42','etablissements_172459.tbl.gz'),
	(72,1,2,'2016-09-19 09:06:44','etablissements_172459_v2.tbl.gz'),
	(73,1,2,'2016-09-19 09:48:47','etablissements_172459_v3.tbl.gz'),
	(74,1,2,'2016-09-19 12:16:06','etablissements_172459_v3.tbl'),
	(75,1,2,'2016-09-21 10:16:09','etablissements_111239.tbl.gz'),
	(77,1,1,'2016-10-25 08:33:45','dpae_XDPDPA_DPAE_20161010.csv.gz'),
	(79,1,1,'2016-11-17 10:01:48','dpae_XDPDPA_DPAE_20161110.csv.gz'),
	(86,1,2,'2016-11-25 13:23:37','etablissements_173907.tbl.gz'),
	(90,1,1,'2016-12-26 13:32:01','LBB_XDPDPA_DPAE_20151110_20161210_20161210_094110.csv.bz2'),
	(91,1,2,'2016-12-26 13:32:06','LBB_EGCEMP_ENTREPRISE_20151119_20161219_20161219_153447.csv.bz2'),
	(96,1,1,'2017-02-07 17:49:27','LBB_XDPDPA_DPAE_20151210_20170110_20170110_102638.csv.bz2'),
	(97,1,2,'2017-02-19 13:51:09','LBB_EGCEMP_ENTREPRISE_20151210_20170110_20170110_101155.csv.bz2'),
	(99,1,1,'2017-03-05 08:57:08','LBB_XDPDPA_DPAE_20120222_20170222.csv.gz'),
	(100,1,2,'2017-03-06 18:07:15','LBB_EGCEMP_ENTREPRISE_20160122_20170222_20170222_094933.csv.bz2'),
	(101,1,2,'2017-05-10 16:02:44','LBB_EGCEMP_ENTREPRISE_20160307_20170407_20170407_182228.csv.bz2'),
	(103,1,1,'2017-05-11 16:27:02','LBB_XDPDPA_DPAE_20160302_20170331_20170331_172811.csv.bz2'),
	(106,1,2,'2017-06-23 09:01:58','LBB_EGCEMP_ENTREPRISE_20160209_20170309_20170309_175317.csv.bz2'),
	(110,1,1,'2017-06-30 19:04:55','LBB_XDPDPA_DPAE_20160430_20170530_20170530_161206.csv.bz2');
ALTER TABLE `import_tasks` ENABLE KEYS;
UNLOCK TABLES;




SET FOREIGN_KEY_CHECKS = @PREVIOUS_FOREIGN_KEY_CHECKS;


