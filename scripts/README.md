# Scripts PC est magique

Les fichiers `.py` dans ce dossier sont des scripts exécutables dans le
contexte applicatif de PC est magique.

Pour exécuter le script `<name>.py` :

```py
cd /home/pc-est-magique/pc-est-magique
source env/bin/activate
flask script <name>
```

Les scripts doivent comporter une fonction `main()`, qui sera appelée
(sans arguments) par `flask script`.
