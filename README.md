Fedora Patch Tracker
============

A prototype for the Fedora Patch Tracker Project in GSoC 2015. WIP

### Usage

1. Install the dependencies with `pip install requirements.txt`
2. Install redis and start it
3. Open the shell by running `python shell.py` and create the database by executing `db.create_all()`.
4. Run the development server `python run.py`
5. Run `python worker.py`
6. Access the project by visiting `http://localhost:5000` on your browser

### Limitations

The current design goes through all the branches of the package's git
repository and stores the patches in the database. This poses a few problems:

1. All patches are decoded using UTF-8 charset and characters are replaced in
   case there's a decode error
2. Packages with a large number of patches (e.g. kernel) end up taking a lot of
   space in the database and the retrieval GET request for them is large. This
may be solved by storing the reference of the patches in the database instead
and retrieving them individually on demand instead of having a single GET
request to fetch them all.

