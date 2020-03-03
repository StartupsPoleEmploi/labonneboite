## Impact sur le retour à l'emploi

Ce projet va aider à représenter l'impact sur le retour à l'emploi de LBB.
Il va consister en plusieurs scripts : 

- 1 script quotidien : 
    - le daily parser : daily_json_activity_parser.py.

    C'est un script qui va être exécuté quotidiennement, et va récupérer des infos à partir des logs de production de la bonne boite.
    Il va aider à stocker les activités sur le site de LBB, les différents utilisateurs se connectant au site, les recherches effectuées etc...

- 3 scripts mensuels : 
    - la join activity logs and dpae : join_activity_logs_dpae.py
    
    C'est un script exécuté mensuellement qui va récupérer toutes les données précédentes, et va faire une jointure avec les DPAE.
    Dans le principe, on va estimer qu'un utilisateur de LBB réalisant une activité sur le site de LBB par rapport à un entreprise, et qui par la suite va retrouver un travail avec cette même entreprise, a été aidé par LBB pour retrouver du travail. Ce script nous donne un csv.
    - clean activity logs dpae
    
    La suite logique du précédent. Il va récupérer le csv et va effectuer un certain nombre de transformations/épurations dans les données pour avoir uniquement ce qui va nous intéresser dans les données, avant de les insérer dans la base de données.
    - make_report
    
    Ce script va récupérer les données précédentes, pour les envoyer sur un Google Sheets qui ira alimenter un Google Data Studio, afin d'élaborer un rapport sur l'impact sur le retour à l'emploi. 