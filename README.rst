===============================
SimTool
===============================


.. image:: https://img.shields.io/pypi/v/simtool.svg
        :target: https://pypi.python.org/pypi/simtool

.. image:: https://img.shields.io/travis/hubzero/simtool.svg
        :target: https://travis-ci.org/hubzero/simtool

.. image:: https://readthedocs.org/projects/simtool/badge/?version=latest
        :target: https://simtool.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

Functions for creating and running Simulation Tools on the HUBzero_ platform lead by nanoHUB_

* Free software: MIT license
* Documentation: https://simtool.readthedocs.io.


Features
--------

* Easily declare and validate inputs and outputs of a simulation using Python and Jupyter notebooks. The entire simulation code can run inside a notebook or the notebook can be a wrapper that invokes complex external codes.
 
* Uses papermill_ to run parameterized notebooks, saving a new copy for each run.

* Results saved in a datastore (filesystem or web service based).  The datastore can be used for machine learning and statistical analysis.  Additionally, it functions as a cache.

* Can be containerized for remote execution.



Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _HUBzero: https://help.hubzero.org
.. _nanoHUB: https://nanohub.org
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _papermill: https://github.com/nteract/papermill
