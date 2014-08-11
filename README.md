adsmodel
========

Network model for an advertising exchange system using networkx and Gurobi Optimizer

This is a python implementation of a network model for an advertising exchange system.  The main python source is in src/advertiser.py.  For a usage example see the python blocks in tex/PreliminaryReport.tex, and see PreliminaryReport.pdf for a description of the algorithm.

In order to run the model you will need Python 2 with networkx, Gurobi Optimizer, and the associated python bindings.  To compile PreliminaryReport.tex you should use pdflatex, and make sure to add -shell-escape as a command line options in order to activate the python latex package.
