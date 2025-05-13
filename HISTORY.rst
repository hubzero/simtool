=======
History
=======

0.1.0 (2019-08-09)
------------------

* First release on PyPI.

0.2.0 (2020-03-04)
------------------

* Second release on PyPI.

0.2.1 (2020-03-08)
------------------

* Third release on PyPI.

0.2.2 (2020-03-08)
------------------

* PyPI release with updated documentation.

0.2.3 (2020-09-21)
------------------

* Improved search function to locate simTool notebook

0.3.1 (2021-06-14)
------------------

* Improved input data validation
* Added web service based cacheing support

0.3.2 (2021-09-22)
------------------

* Fixed for use outside of HUBzero environment

0.3.3 (2021-10-04)
------------------

* Improved automatic documentation generation
* Fixed Image value setting

0.3.4 (2022-05-10)
------------------

* Verify location of installed or published sim2L notebook
* Differentiate between missing path and wrong path type (file/directory)
* Stricter enforcement of param attributes
* Retain directory structure when saving results.
* Close open files to avoid file descriptor leakage
* Added magic functions needed to run notebooks in parallel (MPI)

0.3.5 (2022-05-16)
------------------

* Trap missing simToolSaveErrorOccurred and simToolAllOutputsSaved in result notebook
* Return list of input files whether inputs is specified as dictionary or YAML
* Add run preparation method used for web service application. Previously used external shell script

0.3.6 (2022-08-11)
------------------

* Extend utility functions for getting information about input files to use either parameter or simple dictionary description.
* Prepare for newer papermill versions

0.4.1 (2022-12-13)
------------------

* Added new parameter classes Tag and File.
* Use checksum and file size to compute sim2L run squidId.
* Improve papermill efficiency by reducing implicit I/O done during execution.
* Added support for sim2L metrics collection - record hit and miss by squidid.
* Added getParamsFromDictionary() and content() methods to standardize processing on INPUTS in sim2L notebooks.

0.4.2 (2025-01-13)
------------------

* Added updateParamsFromDictionary() methods to update params with input dictionary.
* Fixed issue with updating param units attribute.
* Updated dependency requirement versions.

0.4.3 (2025-05-13)
------------------

* Spell check.
* Allow for output in subdirectories.
* Complete changeover from getParamsFromDictionary to updateParamsFromDictionary.
* Add squidId to Run class.

