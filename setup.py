#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['ipython', 'pint', 'numpy', 'papermill', 'jsonpickle', 
                'mendeleev', 'pillow', 'nteract-scrapbook', 'joblib']

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='simtool',
    version='0.2.3',
    description="Functions for creating and running Simulation Tools",
    long_description=readme + '\n\n' + history,
    author="Martin Hunt",
    author_email='mmh@purdue.edu',
    url='https://github.com/hubzero/simtool',
    packages=[
        'simtool',
    ],
    package_dir={'simtool':
                 'simtool'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='simtool',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
