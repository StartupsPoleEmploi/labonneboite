DROP TABLE if exists etablissements_exportable;

CREATE TABLE `etablissements_exportable` (
  `siret` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `raisonsociale` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `enseigne` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `codenaf` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `trancheeffectif` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `numerorue` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `libellerue` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `codepostal` varchar(11) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tel` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `website` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `flag_alternance` tinyint(1) NOT NULL,
  `flag_junior` tinyint(1) NOT NULL,
  `flag_senior` tinyint(1) NOT NULL,
  `flag_handicap` tinyint(1) NOT NULL,
  `has_multi_geolocations` tinyint(1) NOT NULL,
  `codecommune` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `coordinates_x` float DEFAULT NULL,
  `coordinates_y` float DEFAULT NULL,
  `departement` varchar(11) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `score` int(11) DEFAULT NULL,
  PRIMARY KEY (`siret`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci