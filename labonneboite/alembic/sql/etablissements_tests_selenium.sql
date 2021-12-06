# this script should only run in selenium tests and AFTER all migrations have completed

# this only injects data in existing table etablissements

#
# SQL Export
# Created: 10 July 2019 at 17:22:19 CEST
# Encoding: Unicode (UTF-8)
#


SET @PREVIOUS_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;

LOCK TABLES `etablissements` WRITE;
TRUNCATE `etablissements`;
ALTER TABLE `etablissements` DISABLE KEYS;
INSERT INTO `etablissements` (`siret`, `raisonsociale`, `enseigne`, `codenaf`, `numerorue`, `libellerue`, `codecommune`, `codepostal`, `email`, `tel`, `departement`, `trancheeffectif`, `score`, `coordinates_x`, `coordinates_y`, `website`, `flag_alternance`, `flag_junior`, `flag_senior`, `flag_handicap`, `has_multi_geolocations`, `email_alternance`, `score_alternance`) VALUES


    # Less than 15 minutes by public transports AND 15 minutes by car minimum
    ('99882350427599','LES INVALIDES','','6420Z','','PLACE GABRIEL HOCQUARD','57463','57000','','','57','02',98,6.1728773,49.1247178,'http://www.dummywebsite.com',1,0,0,0,0,'',62),
    ('99882350427600','PALAIS DE JUSTICE','','6420Z','1','AVENUE FOCH','57463','57000','','','57','02',98,6.1713958,49.1113618,'http://www.dummywebsite.com',1,0,0,0,0,'',62),

    # Between 15 and 30 minutes by public transports AND 15 minutes by car minimum
    ('99882350427601','PANTHEON','','6420Z','10','AVENUE DE THIONVILLE','57140','57000','','','57','02',98,6.1580305,49.1439775,'http://www.dummywebsite.com',1,0,0,0,0,'',62),
    ('99882350427602','LES TUILERIES','','6420Z','100','AVENUE ANDRE MALRAUX','57463','57000','','','57','02',98,6.1803206,49.1013597,'http://www.dummywebsite.com',1,0,0,0,0,'',62),

    # Between 30 and 45 minutes by public transports AND 15 minutes by car minimum
    ('99882350427603','ORSAY','','6420Z','','RUE PAUL LANGEVIN','57616','57070','','','57','02',98,6.17397,49.142943,'http://www.dummywebsite.com',1,0,0,0,0,'',62), # Saint-Julien-lès-Metz
    ('99882350427604','ORANGERIE','','6420Z','17','RUE CLAUDE CHAPPE','57616','57070','','','57','02',98,6.2227803,49.1010496,'http://www.dummywebsite.com',1,0,0,0,0,'',62),


    -- # Less than 15 minutes by car
    ('99882350427597','ELYSEE','','6420Z','','VOIE ROMAINE','57433','57280','','','57','02',98,6.1475083,49.1981046,'http://www.dummywebsite.com',1,0,0,0,0,'',62),
    ('99882350427598','PALAIS ROYAL','','6420Z','1','RUE DE LA BELLE FONTAINE','57447','57155','','','57','02',98,6.1427355,49.0684317,'http://www.dummywebsite.com',1,0,0,0,0,'',62),
    ('99882350427607','LE LOUVRE','','6420Z','','SAINT REMY SERVICES','57546','57140','','','57','02',98,6.1758836,49.1760443,'http://www.dummywebsite.com',1,0,0,0,0,'',62),

    # Between 15 and 30 minutes by car
    ('99882350427594','LU','','6420Z','17','AVENUE DES TILLEULS','57221','57190','','','57','02',98,6.1295326,49.3258483,'http://www.dummywebsite.com',1,0,0,0,0,'',62), # Florange
    ('99882350427595','LIEU UNIQUE','','6420Z','52','ROUTE DE TREHEMONT','57491','57250','','','57','02',98,6.0485979,49.2552576,'http://www.dummywebsite.com',1,0,0,0,0,'',62), # Moyeuvre-Grande
    ('99882350427596','LIEU PAS UNIQUE','','6420Z','24','RUE RAYMOND MONDON','57591','57120','','','57','02',98,6.0918738,49.2531081,'http://www.dummywebsite.com',1,0,0,0,0,'',62), # Rombas

    # Between 30 and 45 minutes by car
    ('99882350427591','MA PETITE ENTREPRISE','','6420Z','5','RUE MAURICE BARRES','57463','54000','','','54','02',98,6.1827674,48.6927065,'http://www.dummywebsite.com',1,0,0,0,0,'',62), # Nancy
    ('99882350427592','MA GRANDE ENTREPRISE','','6420Z','12','RUE DES CARMES','57463','54000','','','54','02',98,6.1779875,48.6918406,'http://www.dummywebsite.com',1,0,0,0,0,'',62), # Nancy
    ('99882350427910','MA MOYENNE ENTREPRISE','','6420Z','','RUE LUCIEN CUENOT','54357','54320','','','54','02',98,6.1332809,48.70688,'http://www.dummywebsite.com',1,0,0,0,0,'',62), #  Maxéville

    # For test_reset_naf
    ('30111709900020','LAVAUX JACQUES','CABINET LAVAUX JACQUES','6622Z','77','RUE MAZELLE','57463','57000','','','57','',91,6.18374,49.1155,'http://www.dummywebsite.com',0,0,1,0,0,'',41),

    # For test_make_a_new_search
    ('99882350427630','LA BOUCHERIE DU PALAIS','','4722Z','1','AVENUE FOCH','57463','57000','','','57','02',98,6.1713958,49.1113618,'http://www.dummywebsite.com',1,0,0,0,0,'',62); # boucher

ALTER TABLE `etablissements` ENABLE KEYS;
UNLOCK TABLES;




SET FOREIGN_KEY_CHECKS = @PREVIOUS_FOREIGN_KEY_CHECKS;
