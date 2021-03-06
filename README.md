# PC est magique

Application Flask tournant sur https://pc-est-magique.fr.


## Quoi de neuf sur PC est magique ?

Rien pour l'instant

Seules les fonctionnalités majeures sont listées ici ; voir
[`CHANGELOG.md`](CHANGELOG.md) pour les détails.

### 2.1

* Authentification (création de compte et connexion) via le SSO de l'ESPCI.
* Accès effectif aux photos.

### 2.0

* Factorisation du site de l'IntraRez (anciennement sur 
  https://intrarez.pc-est-magique.fr, https://github.com/GRI-ESPCI/intrarez) 
  comme module ce site plus global.
* Ajout du module de photos.
* Nouveau système de rôles et permissions.

### 1.6

* Système de ban par les GRI / si non paiement, coupant l'accès Internet.

### 1.5

* Mise en service des paiements :
  * Pages d'information, de choix de l'offre et de paiement ;
  * Paiement par Lydia / CB (automatisé), virement bancaire ou espèces ;
  * Ajout / validation de paiement manuel par les GRI ;
  * Souscription automatique à l'offre de bienvenue à la première connexion.
* Envoi de mails riches, au format HTML pour divers motifs.
* Ajout de la possibilité de modifier diverses informations sur son profil ;
* Enregistrement en base de la langue préférée de chaque utilisateur ;
* Mode maintenance activable par les GRI et page pour exécuter un script.

### 1.4

* Accès extérieur et contexte de connexion.
* Captcha pour le formulaire de contact depuis l'extérieur.

### 1.3

* Mécanisme de changement de chambre.
* Affichages de l'adresse IP attribuée aux appareils dans le profil.
* Gestion des chambres et appareils par les GRI (doas).

### 1.2

* Menu GRI pour la gestion des PCéens et le monitoring réseau.

### 1.1

* Portail captif pour simplifier la connexion au réseau.

### 1.0

* Release initiale, fonctionnalités de base en tant que site IntraRez :
  * Connexion des rezidents, chambres et appareils (détection automatique),
  * Génération des règles DHCP pour chaque chambre et script de mise à jour,
  * Menu GRI avec liste des rezidents.


## Exigences

* Python >= 3.10 ;
* Autres packages Linux : ``postgresql postfix git npm xmlsec1``, plus pour le
  déploiement : ``supervisor nginx`` ;
* Package npm : ``bower sass``
    * Package Bower : ``bootstrap moment webping-js lightgallery``
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

(côté développement, voir plus bas)



## Notes de développement

Je vais ici noter pas à pas ce que je fais, pour simplifier au maximum
l'appréhension du code par d'éventuels GRI futurs.


### Début de l'installation

### 11/09/2021 - Loïc 137

Tout a été créé en suivant ce tutoriel :
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

Requirements : je pars sur Python 3.10, parce que le nouveau statement `match`
me fait beaucoup trop de l'oeil.

À ce jour, Python 3.10 n'est disponible qu'en version *release candidate* 2
(donc quasiment finale), et devrait sortir début octobre (donc avant la
release de l'IntraRez).

Installation propre de plusieurs versions de Python sur un même OS :
https://hackersandslackers.com/multiple-python-versions-ubuntu-20-04

Installation d'un virtual env fresh

Utilisation de SQLAlchemy 1.4 (2.x pas prêt)

#### Gestion des migrations de db

Lors du développement d'une nouvelle version modifiant le modèle de données :
  * En local : ``flask db migrate -m "Migration to <version>"`` ;
  * Vérifier le fichier créé dans ``migrations/versions``.
    **ATTENTION** : notemment, si on crée une nouvelle colonne non-nullable,
    il faut modifier le code généré automatiquement :
    ```py
        op.add_column('table', sa.Column('col', sa.Boolean(), nullable=False))
    ```
    devient
    ```py
        op.add_column('table', sa.Column('col', sa.Boolean(), nullable=True))
        op.execute("UPDATE table SET col = false")      # Ou autre valeur
        op.alter_column('table', 'col', type_=sa.Boolean(), nullable=False)
    ```
  * ``flask db upgrade`` pour appliquer localement ;
  * (autres modifs hors db)
  * Release de la version.


#### Spécificités

Je pars sur une structure en modules (basée sur les *blueprints* Flask),
détaillée au chapitre XV du tuto :
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xv-a-better-application-structure


Application bilingue (utilisant Flask-Babel) : lorsque le code est modifié,
* Exécuter ``flask translate update`` ;
* Modifier/ajouter les clés de traduction dans
  ``app/translations/en/LC_MESSAGES/messages.po``. Les entrées modifiées
  sont indiquées avec ``#, fuzzy`` : **supprimer ce commentaire** après
  avoir vérifié qu'il n'y avait pas d'erreur / modifié la traduction ;
* Exécuter ``flask translate compile``.


### 20/09/21 - Loïc 137

Abandon de Flask-Bootstrap, qui est sur Bootstrap 3 et assez restreignant.

À la place, je crée le template de base à la main (en créant à peu près
les blocs que Flask-Bootstrap créait), de même pour le template des forms.

J'ai repris le code de Flask-Bootstrap pour ce qui est de la gestion des
forms, directement dans [`app/templates/_form.html`](app/templates/_form.html).

Utilisation des icônes SVG [Bootstrap Icons](https://icons.getbootstrap.com/),
directement dans app/static/svg. Voir le code d'affichage des notifications
dans [`app/templates/base.php`](app/templates/base.php) pour savoir comment
utiliser ces icônes (rechercher `svg`).
