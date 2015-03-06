Fedora Patch Tracker
============

A prototype for the Fedora Patch Tracker Project in GSoC 2015. WIP

### Usage

1. Install the dependencies with `pip install requirements.txt`
2. Install redis and start it
3. Open the shell by running `python shell.py` and create the database by executing `db.create_all()`.
4. Run the development server `python run.py`
5. Run `python worker.py`
