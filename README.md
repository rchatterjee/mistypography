# MISTYPOGRAPHY
This module implements different typo correction strategies discussed
in https://www.cs.cornell.edu/~rahul/papers/pwtypos.pdf.

## REQUIREMENTS
* Install `pwmodel` from [here](https://github.com/rchatterjee/pwmodels.git)
```bash
$ pip isntall git+https://github.com/rchatterjee/pwmodels.git
```
   This should install all the dependencies, if not, you may have to
   install `python-Levenshtein`.
```bash
$ pip install python-Levenshtein
```

## INSTALL

```bash
$ pip install git+https://rchatterjee@bitbucket.org/rchatterjee/pwmodels.git
$ pip install git+https://rchatterjee@bitbucket.org/rchatterjee/mistypography.git
```

## HOW TO USE?  

To allow online typo correction, a set of corrected version of the
mistyped password is created, and then each of them is tested against
the real password hash. This code only generates the possible set of
corrections (a.k.a. ball).  The simplest way to do this is to use one
of the built-in checkers (`BUILT_IN_CHECKERS`) in
`typofixer/checker.py` file. Descriptions of these checkers is given
in the `checker.py` file. 
 
 You can also instantiate your own `Checker`. To instanticate a
 checker we need two arguments, first, a set of correctors which you
 can see the names given in common.py, and second, a policy number
 which will tune the checker to use one of the given policies (ChkAll,
 ChkBl etc.).

Note, the checker needs the `data` directory to be in the same
folder. You can move the `data` directory and change path
`DATA_DIR_PATH` in `common.py` accordingly.

```bash
$ python
Python 2.7.6 (default, Jun 22 2015, 17:58:13) 
[GCC 4.8.2] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> from typofixer.checker import BUILT_IN_CHECKERS

>>> chk = BUILT_IN_CHECKERS['ChkAllTop3']

>>> chk = BUILT_IN_CHECKERS['ChkAllTop3'] 

>>> chk.check('password')
set(['passwor', 'Password', 'PASSWORD', 'password'])

>>> chk_bl = BUILT_IN_CHECKERS['ChkBlTop3']

>>> chk_bl.check('password')
set(['passwor', 'password'])

>>> >>> chk_all = BUILT_IN_CHECKERS['ChkAllTop5']

>>> chk_all.check('password1')
set(['assword1', 'PASSWORD1', 'Password1', 'password!', 'password', 'password1'])

```



### CONTACT
Rahul Chatterjee (rahul@cs.cornell.edu)
