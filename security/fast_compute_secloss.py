# Compute the security loss of edit 1 correction for q guesses.
# 1. for each password compute all the passwords B^2 that are within
#    edit-distance 2 from the original passwrod w
# 2. Then for each point in the neighborhood around w, find the subset 
#    of the points in B^2 which are within edit distance 1. 
# 3. Then as usual.

import string
from pwmodel import fast_fuzzysearch, HistPw
from heap import priority_dict
import os, sys
import time

allowed_chars = string.printable[:-5]
PWLIMIT = int(2e6)

def apply_edits(w):
    """
    Apply all edits to w and returned the list of possible strings.
    """
    yield w.lower()
    yield w.swapcase()
    for i in xrange(len(w)+1):
        for c in allowed_chars:
            yield w[:i]+c+w[i:]  # insert
            yield w[:i]+c+w[i+1:]  # replace
        yield w[:i]+w[i+1:]  # delete


def greedy_maxcoverage_heap(attacker_pwmodel, q, **kwargs):
    subset_heap = priority_dict()
    covered = set()
    guessed_set = set() # guessed_set \subseteq covered, and equal to guesses 
    guesses = []
    for rpw in attacker_pwmodel.iterpasswords():
        if len(rpw)<6: continue
        nhplus = set(attacker_pwmodel.similarpws(rpw, ed=2)) - covered
        for tpw in apply_edits(rpw):
            if  (tpw not in subset_heap) and (tpw not in guessed_set):
                subset_heap[tpw] = -sum(pwmodel.prob(tpw) for tw in nhplus.query(rpw))

import dataset
def create_pw_db_(attacker_pwmodel, force=False):
    leakname = attacker_pwmodel._leak
    db = dataset.connect('sqlite:///{}.db'.format(leakname))
    if 'passwords' in db.tables and not force:
        return
    db['passwords'].drop()
    pwtab = db['passwords']
    pwm = HistPw(fname)
    s = time.time()
    pwtab.insert_many(dict(pw=pw, f=c) for pw, c in pwm.iterpasswords())
    e = time.time()
    print("Done inserting in {}s".format((e-s)/1e3))
    s = time.time()
    pwtab.create_index(pw)
    print("Done creating index in {}s".format((time.time()-s)/1e3))


def insert_typos_to_db(db):
    typotab = db['typos']
    for d in db.query('select pw, id from passwords limit PWLIMIT'):
        pw, id_ = d['pw'], d['id']
        apply_edits
        
if __name__ == '__main__':
    import sys
    create_pw_db_(sys.argv[1])
