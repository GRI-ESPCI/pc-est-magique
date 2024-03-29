
SHELL := /bin/bash

help:
	@echo "PC est magique Makefile - v0.1.0"
	@echo "The following directives are available:"
	@echo "		install 	Install PC est magique (development mode)"
	@echo "					Run all steps described in README §Installation"
	@echo "		deploy 		Make PC est magique ready for production"
	@echo "					Run all steps described in README §Passage en prod"
	@echo "		update 		Install PC est magique (development mode)"
	@echo "					Run all steps described in README Mise à jour"
	@echo "		help 		Show this message and exit"

install:
	@echo "Installing PC est magique (development mode)..."
	# Check packages
	EXECUTABLES = python3 psql postfix git npm xmlsec1
	K := $(foreach exec,$(EXECUTABLES),\
	    $(if $(shell which $(exec)),some string,$(error "No $(exec) in PATH")))
	# Install dependecies
	python3 -m venv env
	env/bin/pip install -r requirements.txt
	env/bin/pip install psycopg2 cryptography
	npm install
	# Configure .env
	cp .conf_models/.model.env .env
	SECRET_KEY=$(shell python3 -c "import uuid; print(uuid.uuid4().hex)")
	sed -e "s/some-random-key/$(SECRET_KEY)" .env
	edit .env
	# Create database
	SQL_PASS=$(shell bash -c 'read -s -p "SQL user password: " pwd; echo $$pwd')
	SQL_PASS_SEDESC=$(printf '%s\n' "$SQL_PASS" | sed -e 's/[]\/$*.^[]/\\&/g');
	sed -e "s/<mdp-db>/$(SQL_PASS_SEDESC)" .env
	@echo "We need privileges to create PostgreSQL base and user:"
	sudo su postgres -c "psql \
		-c \"CREATE ROLE pc-est-magique WITH LOGIN PASSWORD '$(SQL_PASS)'\" \
		-c \"CREATE DATABASE pc-est-magique OWNER pc-est-magique ENCODING 'UTF8'\""
	# Other steps
	echo "export FLASK_APP=pc-est-magique.py" >> ~/.profile
	bower install
	env/bin/flask translate compile
	env/bin/flask sass compile
	@echo "All set, try source 'env/bin/activate' then 'flask run'!"

deploy:
	@echo "Installing production mode..."
	# Check packages
	EXECUTABLES = supervisor nginx
	K := $(foreach exec,$(EXECUTABLES),\
	    $(if $(shell which $(exec)),some string,$(error "No $(exec) in PATH")))
	# Update environment
	cp .conf_models/prod.flaskenv .flaskenv
	env/bin/pip install gunicorn
	# Configure Supervisor
	cp .conf_models/supervisor.conf /etc/supervisor/conf.d/pc-est-magique.conf
	supervisorctl reload
	# Configure Nginx
	cp .conf_models/nginx.conf /etc/nginx/sites-enabled/pc-est-magique
	service nginx reload

update:
	@echo "Updating PC est magique..."
	# Get last version
	git pull
	# Update dependencies
	env/bin/pip install -r requirements.txt
	npm install
	./node_modules/bower/bin/bower install
	./node_modules/bower/bin/bower update
	# Upgrade application
	@echo "Stopping application before critical updates..."
	sudo supervisorctl stop pc-est-magique
	env/bin/flask db upgrade
	env/bin/flask translate compile
	env/bin/flask sass compile
	@echo "Compressing static files..."
	find app/static -name "*.gz" -type f -delete
	gzip -krf app/static
	@echo "Running update scripts..."
	env/bin/flask script update_offers
	env/bin/flask script update_roles
	@echo "Starting application..."
	sudo supervisorctl start pc-est-magique
	@echo "Update live!"
