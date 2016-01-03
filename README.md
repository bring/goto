Goto
====

Simple URL shortener in Python/Flask.

Running locally
===============

Use [virtualenv][1]:

    # install virtualenv if not installed already:
    [ $(which virtualenv) ] && echo "already installed" || pip install virtualenv

    # create new virtual environment if it doesn't exist
    [ -d venv ] && echo "venv already exists" || virtualenv --system-site-packages venv

    # activate it
    . venv/bin/activate

Install requirements (if first or requirements changed):

    pip install -r requirements.txt

Run it:

    python run.py

References
==========

[1]: http://flask.pocoo.org/docs/0.10/installation/#virtualenv
