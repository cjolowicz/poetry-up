poetry-up
=========

.. toctree::
   :hidden:
   :maxdepth: 1

   reference
   CONTRIBUTING
   Code of Conduct <CODE_OF_CONDUCT>
   license
   Changelog <https://github.com/cjolowicz/poetry-up/releases>

Command-line tool for upgrading Python dependencies using Poetry.

By default, this tool determines outdated dependencies
using ``poetry show --outdated``,
and performs the following actions for every reported package:

    1. Switch to a new branch ``poetry-up/<package>-<version>``.
    2. Update the dependency with ``poetry update``.
       For incompatible updates, also update ``pyproject.toml``.
    3. Commit the changes to pyproject.toml and poetry.lock.
    4. Push to origin (optional).
    5. Open a pull request or merge request (optional).

If no packages are specified on the command-line,
all outdated dependencies are upgraded.


Installation
------------

To install poetry-up,
run this command in your terminal:

.. code-block:: console

   $ pip install poetry-up


Usage
-----

poetry-up's usage looks like:

.. code-block:: console

   $ poetry-up [<options>] [<packages>]

.. option:: --install

   Install dependency into virtual environment.
   This is the default behavior.

.. option:: --no-install

   Do not install dependency into virtual environment.

.. option:: --commit

   Commit the changes to Git.
   This is the default behavior.

.. option:: --no-commit

   Do not commit the changes to Git.

.. option:: --push

   Push the changes to the remote repository.

.. option:: --no-push

   Do not push the changes to the remote repository.
   This is the default behavior.

.. option:: --merge-request

   Open a merge request.

.. option:: --no-merge-request

   Do not open a merge request.
   This is the default behavior.

.. option:: --pull-request

   Open a pull request.

.. option:: --no-pull-request

   Do not open a pull request.
   This is the default behavior.

.. option:: --upstream <branch>, -u <branch>

   Specify the upstream branch.
   By default, branches are created off the master branch.

.. option:: --remote <remote>, -r <remote>

   Specify the remote to push to.
   By default, branches are pushed to origin.

.. option:: -C <directory>, --cwd <directory>

   Change to this directory before performing any actions.

.. option:: -n, --dry-run

   Just show what would be done.

.. option:: --version

   Display the version and exit.

.. option:: --help

   Display a short usage message and exit.
