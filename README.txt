* Dependency

This is a purely python based project with no dependency other than
standard python 2.7 impelementation.



* How to use?  

Basically one would like to create the ball of correction given a
entered password. The simplest way to do this is instantiate a Checker
class with required arguments. The checker class already has a set of
checker implemented, e.g., ChkAll, ChkBl, ChkAOp (description of these
checker is given in the checker.py file).  To instanticate Checker we
need two arguments, first, a set of correctors which you can see the
names given in common.py, and second, a policy number which will tune
the checker to use one of the given policies (ChkAll, ChkBl etc.).

Note, the checker needs the data directory to be in the same
folder. You can move the 'data' directory but then you have set the path
in common.py for DATA_DIR_PATH.


[rahul @ code/dropbox] [master]$ python
Python 2.7.6 (default, Jun 22 2015, 17:58:13) 
[GCC 4.8.2] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> from common import top3correctors

>>> from checker import Checker
data/rockyou1M.json.gz

>>> chk = Checker(top3correctors, 5)

>>> chk.get_ball('password1')
set(['password1'])

>>> chk.get_ball('password123')
set(['PASSWORD123', 'Password123', 'password123'])

