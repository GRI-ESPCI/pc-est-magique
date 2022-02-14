# PC est magique

Application Flask tournant sur https://pc-est-magique.fr.


## Quoi de neuf sur PC est magique ?

Rien pour l'instant


## Exigences

* Python >= 3.10 ;
* Autres packages Linux : ``postgresql postfix git npm``, plus pour le
  déploiement : ``supervisor nginx`` ;
* Package npm : ``bower sass``
    * Package Bower : ``bootstrap moment``
* Packages Python : Voir [`requirements.txt`](requirements.txt), plus pour le
  déploiement : ``gunicorn pymysql cryptography`` ;
* Pour le déploiement : un utilisateur Linux ``pc-est-magique`` dédié.


## Installation

Je reprends pour l'essentiel le déploiement conseillé dans le tutoriel :
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvii-deployment-on-linux

* Installer les dépendances :

  ```
  sudo apt install postgresql postgresql-client postfix git npm [supervisor nginx]
  ```

* Installer l'application :

  ```
  cd /home/pc-est-magique
  git clone https://github.com/GRI-ESPCI/pc-est-magique
  cd pc-est-magique
  npm install
  python3 -m venv env
  source env/bin/activate
  pip install -r requirements.txt
  pip install gunicorn pymysql cryptography
  cp .conf_models/model.env .env
  ```

* Créer et initialiser la base de données :

   * PostgreSQL (recommandé) :
     ```
     sudo su postgres -c psql
     ```
     ```sql
     CREATE ROLE pc-est-magique WITH LOGIN PASSWORD '<mdp-db>';
     CREATE DATABASE pc-est-magique OWNER pc-est-magique ENCODING "UTF8";
     EXIT;
     ```

     ```
     pip install psycopg2 # ==2.9.2
     ```

   * MySQL :
      ```
      sudo mysql -u root
      ```
      ```sql
      CREATE DATABASE pc_est_magique CHARACTER SET utf8 COLLATE utf8_bin;
      CREATE USER 'pc_est_magique'@'localhost' IDENTIFIED BY '<mdp-db>';
      GRANT ALL PRIVILEGES ON pc_est_magique.* TO 'pc_est_magique'@'localhost';
      FLUSH PRIVILEGES;
      QUIT;
      ```

  Puis
  ```
  flask db upgrade
  ```

* Modifier le fichier ``.env`` créé depuis le modèle.
  Pour générer une ``SECRET_KEY`` aléatoire :

  ```
  python3 -c "import uuid; print(uuid.uuid4().hex)"
  ```

* Enregistrer l'application dans les variables d'environment :

  ```
  echo "export FLASK_APP=pc-est-magique.py" >> ~/.profile
  ```

* Compiler les traductions (fichiers binaires) :

  ```
  flask translate compile
  ```

* Installer les dépendances Bower (Bootstrap) :

  ```
  bower install
  ```

* Compiler les fichiers SASS :

  ```
  flask sass compile
  ```

L'application peut alors normalement être lancée avec ``flask run``.

On a alors une version de développement installée : ``flask run`` n'est pas
approprié à de la production (peu optimisé), et il faut configurer l'accès
depuis l'extérieur (même si c'est un extérieur interne, dans notre cas).


### Passage en production

La première chose à faire est d'utiliser le `.flaskenv` approprié :
```
cp .conf_models/prod.flaskenv .flaskenv
```

On utilise Gunicorn en interne : le serveur Python n'est pas accessible de
l'extérieur, c'est Nginx qui lui servira les requêtes non-statiques.

Gunicorn est lancé et contrôlé par Supervisor, qui fait à peu près le travail
d'un service mais en plus pratique :

```
sudo cp .conf_models/supervisor.conf /etc/supervisor/conf.d/pc-est-magique.conf
sudo supervisorctl reload
```

Le nombre de *workers* de Gunicorn (le ``-w 4`` dans le fichier de conf)
peut être adapté selon la machine.

Configuration de Nginx :

```
sudo cp .conf_models/nginx.conf /etc/nginx/sites-enabled/pc-est-magique
sudo service nginx reload
```


### Mise à jour

Pour mettre à jour l'application, dans le dossier ``pc-est-magique`` :

```bash
git pull
source env/bin/activate
pip install -r requirements.txt
npm install
bower install
sudo supervisorctl stop pc-est-magique
flask db upgrade
flask translate compile
flask sass compile
sudo supervisorctl start pc-est-magique
```
