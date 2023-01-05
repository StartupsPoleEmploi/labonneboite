##  (2023-01-05)

* feat: :alien: changelog ([e207459](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/e207459))



## <small>1.62.5-rc.1 (2023-01-03)</small>

* :bug: fix api signature verification ([178bc19](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/178bc19))
* :corn: fix peam login ([3f10bf9](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/3f10bf9))



## <small>1.62.4-rc.2 (2022-12-12)</small>

* testing configuration by oidc endpoint only ([e9816f5](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/e9816f5))



## <small>1.62.4-rc.1 (2022-12-12)</small>

* :fixed: relationship backpopulates user favotire offices ([771a7ed](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/771a7ed))
* :rotating_light: fix configuration import ([8b72a4a](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/8b72a4a))
* :spade: removed useless imports ([abce126](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/abce126))
* :sparkles: added OIDC endpoint for peam connect ([303c863](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/303c863))



## <small>1.62.1-rc.1 (2022-12-05)</small>

* :apple: update to lbb-common ([c92fb26](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/c92fb26))



## 1.62.0-rc.2 (2022-12-02)

* :bug: removed self used oustide of class ([025fbbb](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/025fbbb))
* :cloud_lightning: fix for xss attack (and doc update) ([97c23f2](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/97c23f2))
* :motor_scooter: reducing the amount of bugs in sonar ([cb81324](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/cb81324))
* :recycle: remove deperecated SPREADSHEET_IDS setting ([8ae6412](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/8ae6412))
* :rotating_light:  urgent quick ui fixes ([9b14101](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/9b14101))
* :sparkles: add consent_categories query param to jepostule iframe ([235dd38](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/235dd38))
* :sparkles: remove memo ([289ad9d](https://git.beta.pole-emploi.fr:23/lbb/lbb/commits/289ad9d))



## 1.60 (2022-09-05)
* ♻️ extract common module by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/622
* ✨♻️ handle new database format by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/623
* PELBB-277: update es and mysql db after office admin changes by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/625
* PELBB-454: office admin remove by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/627
* PELBB-455: update elastic search and mysql db after office admin add by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/626
* PELBB-365: met en valeur les metiers connexes by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/628
* migrate ci to Github CI by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/629
* revert nullable hiring by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/631
* PELBB-85: corrige le bouton postuler sur mobile by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/630

## 1.58 (2022-04-13)
* fix: PELBB-429: 🐛 revert the unexpected add of the offers_count api field by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/621


**Full Changelog**: https://github.com/StartupsPoleEmploi/labonneboite/compare/v1.55...v1.58

## 1.55 (2022-03-03)
* refacto: PELBB-410,PELBB-180,PELBB-353: refactor the search engine by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/616
* feat: PELBB-100: ✨ promote offices with emails by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/617
* feat: PELBB-35: ✨ change sort types by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/618
* style: PELBB-404: 💄 improve mobiville banner style by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/619
* feat: PELBB-407: retire la carte "Elargir aux alentours" si 0 résultats et que mobiville est visible by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/620


**Full Changelog**: https://github.com/StartupsPoleEmploi/labonneboite/compare/v1.54...v1.55

## 1.54 (2022-02-17)

* feat: PELBB-87: integre la banniere mobiville by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/614
* fix: PELBB-415: error 500 on invalid occupation by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/615


**Full Changelog**: https://github.com/StartupsPoleEmploi/labonneboite/compare/v1.53...v1.54

## 1.53 (2022-02-02)

* ux: PELBB-31: ajoute un pas-à-pas sur la page d'accueil  by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/608
* feature: PELBB-163: n'afficher le lien Kompass qu'aux usagers CDE by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/609
* fix: PELBB-354: store the search ROME in favorites to display the same score by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/610
* fix: PELBB-357: remove error when editing an office without alternance email by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/611
* fix: PELBB-11: empty api result return a valid url by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/612
* task: PELBB-400: ajoute un lien vers l'annuaire des entreprises by @lmarvaud in https://github.com/StartupsPoleEmploi/labonneboite/pull/613

### New Contributors
* @lmarvaud made their first contribution in https://github.com/StartupsPoleEmploi/labonneboite/pull/602

**Full Changelog**: https://github.com/StartupsPoleEmploi/labonneboite/commits/v1.53