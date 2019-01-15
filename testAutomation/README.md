# website

[![Build Status](https://travis-ci.com/incuna/gfgp-website.svg?token=B7FBjzP1Jq2YnjxxXA33&branch=master)](https://travis-ci.com/incuna/gfgp-website)

The African Academy of Sciences' Good Financial Grant Practice assessment website.

Project information: https://incuna-pm.atlassian.net/wiki/display/GBL/

## Installation instructions
**This is a Python 3.5, Django 1.11 and Postgres 9.4 project.**

Steps:
- Clone the project
- Make your virtual environment. e.g.
   ```
   mkvirtualenv gfgp --python=`which python3.5`
   ```
- Ensure you have postgres app running
- Run `make install` to install backend and frontend requirements
    + If any command pauses or won't run, run the command individually, e.g. `pip install -r requirements.txt` instead of `make install`
- Create a super user using `python manage.py createsuperuser`

## Running
- Ensure you are in your virtual environment. e.g. `workon gfgp`
- Run the site with `make runserver`
- Run frontend with `grunt`
  * add `--livereload` to use live reload feature
- Run tests with `make test`
- If requirements change you will need to run `make install` again

## Adding an initial survey
* In the admin go to Home > Surveys > Add Survey
* Enter the name of your survey and press "Save and continue editing"
* You will now see an option to import a CSV. Choose your file and upload it.
