# Compute the security loss of edit 1 correction for q guesses.
# 1. for each password compute all the passwords B^2 that are within
#    edit-distance 2 from the original passwrod w
# 2. Then for each point in the neighborhood around w, find the subset 
#    of the points in B^2 which are within edit distance 1. 
# 3. Then as usual.

import string
import sys, os
homedir = os.path.expanduser('~')
sys.path.append('{}/passwords/'.format(homedir))
from readpw import Passwords
# from pwmodel import fast_fuzzysearch, HistPw
from heap import priority_dict
import numpy as np
import os, sys
import time
import multiprocessing
import pyximport
pyximport.install(
    setup_args={"include_dirs": np.get_include()},
    reload_support=True
)
# from fastedit import apply_edits

allowed_chars = string.printable[:-5]
PWLIMIT = int(2e6)
guessed_set = set()
subset_heap = priority_dict()

nhplus = None
def job_parallel(func, n_proc=7, *args):
    p = Pool(n_proc)
    tpws, nhplus = args
    each_part = len(tpws)/n_proc+1
    chunks = (args[i*each_part:i+each_part] for i in range(n_proc))
    return itertools.chain(*p.map(func, chunks))

def apply_edits(w):
    yield w.capitalize()
    yield w[0].upper() + w[1:]
    yield w[0].lower() + w[1:]
    for c in allowed_chars:
        for i in range(len(w)):
            yield w[:i] + c + w[i:]
            yield w[:i] + c + w[i+1:]
        yield w + c
    for i in range(len(w)):
        yield w[:i] + w[i+1:]


def getball(tpw):
    return np.array(filter(
        lambda x: x>=0,
        [
            pwm.pw2id(pw)
            for pw in apply_edits(tpw)
            if len(pw)>=6
        ]
    ))

    
pwm = None
def greedy_maxcoverage_heap(fname, q, **kwargs):
    global pwm, guessed_set, subset_heap
    pwm = Passwords(fname)
    subset_heap = priority_dict()
    covered = set()
    guess_list = []
    ballsize = 2000 # I don't care any bigger ball
    freq_cache = {}
    done = set()
    pwfreq = pwm.values()[::] # deep copy of the frequencies
    p = multiprocessing.Pool(6)
    l = 1
    st = time.time()
    for i, (pwid, f) in enumerate(pwm):
        rpw = pwm.id2pw(pwid)
        if len(rpw)<6: continue
        pw = pwm.id2pw(pwid)
        neighbors = set(apply_edits(pw.encode('ascii', errors='ignore'))) - done
        for tpw, w in subset_heap.sorted_iter():
            w = -w
            ball = getball(tpw)
            nw = pwfreq[ball].sum()
            if w == nw:
                if w >= f*ballsize: # correct value
                    print "Guess: {} weight: {}".format(tpw, w/pwm.totalf())
                    done.add(tpw)
                    guess_list.append(tpw)
                    pwfreq[ball] = 0
                else:  # The ball weight is still small
                    subset_heap[tpw] = -nw
                    break
            elif nw>=p:
                subset_heap[tpw] = -nw

        for tpw, ball in zip(neighbors, p.map(getball, iter(neighbors))):
            subset_heap[tpw] = -pwfreq[ball].sum()
            
        if len(subset_heap) > l:
            print("({}) : Heap size: {}".format(time.time()-st, len(subset_heap)))
            l = len(subset_heap) * 2
        if i%10==0:
            print("({}) : {}: {} ({})".format(time.time()-st, i, rpw, f))
        if len(guess_list)>=q:
            break
    with open('guess_{}.json'.format(q), 'w') as f:
        json.dump(f, guess_list)
    return guess_list

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
        apply_edits(pw)
        
if __name__ == '__main__':
    import sys
    # create_pw_db_(sys.argv[1])
    greedy_maxcoverage_heap(sys.argv[1], 1000)
