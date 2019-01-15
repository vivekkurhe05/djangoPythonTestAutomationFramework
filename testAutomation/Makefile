verbosity=2
language='en-gb'
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
LANGUAGES =
addrport=localhost:8000

help:
	@echo "Usage:"
	@echo " make help                   -- display this help"
	@echo " make install                -- install backend"
	@echo " make runserver              -- run site"

install-pip:
	pip install -r requirements.txt

install-db:
	if [ `psql -t -c "SELECT COUNT(1) FROM pg_catalog.pg_database WHERE datname = 'gfgp'"` -eq 0 ]; then \
		psql  -c "CREATE DATABASE gfgp"; \
	fi

install-django:
	@python manage.py migrate
	$(MAKE) loaddata

install-frontend:
	npm install

install: install-pip
install: install-db
install: install-django
install: install-frontend

loaddata:
	python manage.py loaddata page.json

runserver:
	@DEBUG=1 \
		EMAIL_BACKEND=$(EMAIL_BACKEND) \
		python manage.py runserver_plus $(addrport)

test-backend:
	@EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend \
		STATICFILES_STORAGE=django.contrib.staticfiles.storage.StaticFilesStorage \
		DISABLE_RECAPTCHA=1 SESSION_COOKIE_SECURE= CSRF_COOKIE_SECURE= \
		coverage run manage.py test --keepdb --exclude-tag=email --verbosity=$(verbosity)
	@coverage report -m
	@flake8 .

test-fast:
	@EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend \
		STATICFILES_STORAGE=django.contrib.staticfiles.storage.StaticFilesStorage \
		python manage.py test --keepdb --exclude-tag=live --exclude-tag=email --verbosity=$(verbosity)

test-live:
	@EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend \
		STATICFILES_STORAGE=django.contrib.staticfiles.storage.StaticFilesStorage \
		DISABLE_RECAPTCHA=1 SESSION_COOKIE_SECURE= CSRF_COOKIE_SECURE= \
		python manage.py test --keepdb --tag=live111 --verbosity=$(verbosity)\

test-emails:
	@python manage.py test --keepdb --tag=email --verbosity=$(verbosity)

test-frontend:
	@grunt test

test: test-backend
test: test-frontend

translations: site_packages = $(shell python -c "import distutils; print(distutils.sysconfig.get_python_lib())")
translations:
	@mkdir -p locale
	@ln -s $(site_packages)/user_management .
	@python manage.py makemessages --locale=$(language) -s --no-wrap --ignore='*node_modules*' --ignore="user_management/api*"
	@rm user_management
	@python manage.py compilemessages --locale=$(language)

translations-all:
	for language in $(LANGUAGES) ; do \
		echo $$language ; \
		$
		(MAKE) translations language=$$language ; \
	done
