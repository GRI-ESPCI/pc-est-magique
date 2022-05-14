# PC est magique

Application Flask tournant sur https://pc-est-magique.fr.


## Quoi de neuf sur PC est magique ?

Rien pour l'instant


## Exigences

* Python >= 3.10 ;
* Autres packages Linux : ``postgresql postfix git npm``, plus pour le
  déploiement : ``supervisor nginx`` ;
* Package npm : ``bower sass``
    * Package Bower : ``bootstrap moment lightgallery``
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
     CREATE ROLE pc_est_magique WITH LOGIN PASSWORD '<mdp-db>';
     CREATE DATABASE pc_est_magique OWNER pc_est_magique ENCODING "UTF8";
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

ATTENTION : par défaut, le module ``ngx_http_secure_link_module`` (dont on a
besoin pour les tokens de sécurisation d'accès aux photos) n'est pas inclus
dans Nginx ! Il faut donc désinstaller la version installée via ``apt`` (par
exemple), et le recompiler (voir http://nginx.org/en/docs/configure.html) en
activant le *flag* ``--with-http_secure_link_module``.

À titre d'exemple, voici la configuration utilisée pour build la version
actuelle sur la Griway :

```
./configure \
  --prefix=/usr/local \
  --sbin-path=/sbin/nginx \
  --conf-path=/etc/nginx/nginx.conf \
  --pid-path=/run/nginx.pid \
  --lock-path=/var/lock/nginx.lock \
  --error-log-path=/var/log/nginx/error.log \
  --http-log-path=/var/log/nginx/access.log \
  --user=nginx \
  --group=nginx \
  --with-debug \
  --with-file-aio \
  --with-http_gzip_static_module \
  --with-http_realip_module \
  --with-http_ssl_module \
  --with-http_secure_link_module \
  --with-pcre-jit
```

Et la configuration du service ``systemctl``
(``/lib/systemd/system/nginx.service``) :

```
[Unit]
Description=The NGINX HTTP and reverse proxy server
After=syslog.target network-online.target remote-fs.target nss-lookup.target
Wants=network-online.target

[Service]
Type=forking
PIDFile=/var/run/nginx.pid
ExecStartPre=/sbin/nginx -t
ExecStart=/sbin/nginx
ExecReload=/sbin/nginx -s reload
ExecStop=/bin/kill -s QUIT $MAINPID
PrivateTmp=true

[Install]
WantedBy=multi-user.target
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
