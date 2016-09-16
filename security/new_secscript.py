import json, os, sys, gc, random
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
import numpy as np
import time, datetime
from hashlib import md5
from collections import OrderedDict, defaultdict
from heap import priority_dict
import warnings
import csv
import joblib
from multiprocessing import Pool
# import dawg
import marisa_trie
from pwmodel import HistPw
from typofixer.checker import Checker, BUILT_IN_CHECKERS
checker = 'ChkAll_keyedit'
attacker_pwmodel = HistPw(os.path.expanduser('~/passwords/rockyou-withcount.txt.bz2'))
pwlist = attacker_pwmodel.iterpasswords()
typofixer = BUILT_IN_CHECKERS[checker]

import numpy
all_pass = numpy.array([
    pw.encode('ascii', 'ignore')
    for pw in attacker_pwmodel._T.keys()
    if (len(pw)>=6 and len(pw)<=16)
])
K = 10000

datadir = './typodata'
def _get_typos(i):
    marisa_trie.Trie({
        str(tpw)
        for pw in all_pass[i:i+K]
        for tpw in typofixer.check(pw)
    }).save('{datadir}/{:6d}.trie'.format(datadir, i))

def create_basic():
    joblib.Parallel(n_jobs=8, verbose=8)(
        joblib.delayed(_get_typos)(i)
        for i in range(0, len(all_pass), K)
    )

def reconcile():
    T = [
        marisa_trie.Trie().load('{}/{:6d}.trie'.format(datadir, i)
                                for i in range(0, len(all_pass), K))
    ]

if __name__ == '__main__':
    create_basic()
