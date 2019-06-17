On nanoHUB, we have over 500 simulation tools developed with our Rappture toolkit.  This toolkit was developed with ease-of-use and reproducibility as its goals.  Over the years we have added some new features like results caching.  And in the last year we have even had students using the results cache to train machine learning models to better understand certain simulations. 


Now we are taking a fresh look at what a modern simulation pipeline should do.  How can we make it easier to use?  Easier to reproduce?  How can students and researchers chain simulations together into workflows?  How should results be saved to allow data analytics and machine learning?  How can we enable tools to run on local resources, HPC clusters, and cloud resources?


There is no shortage of software that is designed to accomplish these things.  However we were unable to find any single package that met our needs.  Many packages were designed by data scientists for data scientists.  Our customers are mostly non-CS students and researchers.  Ease-of-use is the most important requirement.  For example, requiring developers to package their tool in a special Docker container, or use a language they are unfamiliar with will discourage too many potential contributors.


The solution we are building makes use of many open source components, including Jupyter, Papermill, YAML, MLflow, Docker, and Singularity.  A modular design will support different execution models.  Tools may
