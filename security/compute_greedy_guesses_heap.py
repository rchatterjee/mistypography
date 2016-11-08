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
import os, sys, json
import time
import multiprocessing
import pyximport
# pyximport.install(
#     setup_args={"include_dirs": np.get_include()},
#     reload_support=True
# )
# from fastedit import apply_edits
from word2keypress import Keyboard
from word2keypress.weighted_edist import sample_typos, get_topk_typos
from zxcvbn import password_strength

KB = Keyboard()
allowed_chars = string.printable[:-5]
PWLIMIT = int(2e6)

nhplus = None
def job_parallel(func, n_proc=7, *args):
    pool = Pool(n_proc)
    tpws, nhplus = args
    each_part = len(tpws)/n_proc+1
    chunks = (args[i*each_part:i+each_part] for i in range(n_proc))
    return itertools.chain(*pool.map(func, chunks))

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
    global pwm
    pwm = Passwords(fname)
    subset_heap = priority_dict()
    covered = set()
    guess_list = []
    ballsize = 2000 # I don't care any bigger ball
    freq_cache = {}
    done = set()
    pwfreq = np.copy(pwm.values()) # deep copy of the frequencies
    l = 1
    st = time.time()
    pool = multiprocessing.Pool(5)
    for i, (pwid, f) in enumerate(pwm):
        rpw = pwm.id2pw(pwid)
        if len(rpw)<6: continue
        pw = pwm.id2pw(pwid)
        p = pwm.prob(pw)
        neighbors = set(apply_edits(pw.encode('ascii', errors='ignore'))) - done
        for tpw, w in subset_heap.sorted_iter():
            w = -w
            ball = getball(tpw)
            nw = pwfreq[ball].sum()
            if w == nw:
                if w >= f*ballsize: # correct value
                    print("Guess({}/{}): {} weight: {}"\
                        .format(len(guess_list), q, tpw, w/pwm.totalf()))
                    done.add(tpw)
                    guess_list.append(tpw)
                    pwfreq[ball] = 0
                    if len(guess_list)>=q:
                        break
                else:  # The ball weight is still small
                    subset_heap[tpw] = -nw
                    break
            else:
                subset_heap[tpw] = -nw
        b_max = 0
        for tpw, ball in zip(neighbors, pool.map(getball, iter(neighbors))):
            subset_heap[tpw] = -pwfreq[ball].sum()
            b_max = max(b_max, ball.shape[0])
        ballsize = ballsize*0.9 + b_max*0.1

        if len(subset_heap) > l:
            print(">< ({}) : Heap size: {} ballsize: {}".format(
                time.time()-st, len(subset_heap), ballsize
            ))
            l = len(subset_heap) * 2
        if i%10==0:
            print("({}) : {}: {} ({})".format(time.time()-st, i, rpw, f))
        if len(guess_list)>=q:
            break
    normal_succ = pwm.sumvalues(q=q)/pwm.totalf()
    guessed_pws = np.unique(np.concatenate(pool.map(getball, guess_list)))
    fuzzy_succ = pwm.values()[guessed_pws].sum()/pwm.totalf()
    print("normal succ: {}, fuzzy succ: {}".format(normal_succ, fuzzy_succ))
    with open('guess_{}.json'.format(q), 'w') as f:
        json.dump(guess_list, f)
    return guess_list

pwm = None
def approx_guesses(fname, q):
    """
    TODO: WRITE SOMETHING HERE
    """
    global pwm
    pwm = Passwords(fname)
    subset_heap = priority_dict()
    covered = set()
    guess_list = []
    ballsize = 1000 # I don't care any bigger ball
    freq_cache = {}
    done = set()
    pwfreq = np.copy(pwm.values()) # deep copy of the frequencies
    l = 1
    st = time.time()
    for i, (pwid, f) in enumerate(pwm):
        rpw = pwm.id2pw(pwid)
        if len(rpw)<6: continue
        pw = pwm.id2pw(pwid)
        p = pwm.prob(pw)
        neighbors = [rpw]
        for tpw, w in subset_heap.sorted_iter():
            w = -w
            ball = getball(tpw)
            nw = pwfreq[ball].sum()
            if w == nw:
                if w >= f*ballsize: # correct value
                    print "Guess({}/{}): {} weight: {}"\
                        .format(len(guess_list), q, tpw, w/pwm.totalf())
                    done.add(tpw)
                    guess_list.append(tpw)
                    pwfreq[ball] = 0
                    if len(guess_list)>=q:
                        break
                else:  # The ball weight is still small
                    subset_heap[tpw] = -nw
                    break
            else:
                subset_heap[tpw] = -nw
        for tpw, ball in zip(neighbors, map(getball, iter(neighbors))):
            ballsize = ballsize*0.9 + ball.shape[0]*0.1
            subset_heap[tpw] = -pwfreq[ball].sum()

        if len(subset_heap) > l:
            print(">> ({}) : Heap size: {} ballsize: {}".format(
                time.time()-st, len(subset_heap), ballsize
            ))
            l = len(subset_heap) * 2
        if i%30==0:
            print(">> ({}) : {}: {!r} ({})".format(time.time()-st, i, rpw, f))
        if len(guess_list)>=q:
            break
    normal_succ = pwm.sumvalues(q=q)/pwm.totalf()
    pool = multiprocessing.Pool(7)
    guessed_pws = np.unique(np.concatenate(pool.map(getball, guess_list)))
    fuzzy_succ = pwm.values()[
        guessed_pws
    ].sum()/pwm.totalf()
    print("normal succ: {}, fuzzy succ: {}".format(normal_succ, fuzzy_succ))
    with open('approx_guess_{}.json'.format(q), 'wb') as f:
        json.dump(guess_list, f)
    return guess_list

if __name__ == '__main__':
    import sys
    # create_pw_db_(sys.argv[1])
    # approx_guesses(sys.argv[1], 1000)
    greedy_maxcoverage_heap(sys.argv[1], 1000)
