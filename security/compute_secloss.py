import string
import sys, os, json, csv
homedir = os.path.expanduser('~')
sys.path.append('{}/passwords/'.format(homedir))
from readpw import Passwords
# from pwmodel import fast_fuzzysearch, HistPw
from heap import priority_dict
import numpy as np
import multiprocessing
from word2keypress import Keyboard
from word2keypress.weighted_edist import sample_typos, get_topk_typos
from zxcvbn import password_strength
from compute_guesses_numpy import get_topk_typos, get_typodist_nh

KB = Keyboard()
NH_SIZE = 10
def compute_secloss(guess_file, pwfname):
    pwm = Passwords(pwfname)
    guesses = [w for w, _ in json.load(open(guess_file))]
    guess_set = set(guesses)
    q = len(guesses)
    print("Found {} guesses".format(q))
    lambda_q = pwm.sumvalues(q)/pwm.totalf()
    print("Normal succces: {}".format(lambda_q))
    union_ball = set([
        rpw
        for w in guesses
        for rpw in KB.word_to_typos(str(w))
        if pwm.pw2id(rpw)>=0
    ])
    print("Worst case success rate = {}"\
          .format(sum(pwm.pw2freq(w) for w in union_ball)/pwm.totalf()))

    lambda_corr_q = sum(
        pwm.pw2freq(rpw)
        for rpw in union_ball
        if len(set(get_topk_typos(rpw, NH_SIZE)) & guess_set)>0
    )/pwm.totalf()
    print("lambda-Topk Corr:", lambda_corr_q),

    lambda_topk_q = sum(
        pwm.pw2freq(rpw)
        for rpw in union_ball
        if len(set(get_typodist_nh(rpw, NH_SIZE)) & guess_set)>0
    )/pwm.totalf()
    print("lambda-typodist: ", lambda_topk_q)
    print("Secloss:", lambda_topk_q - lambda_q)
    
def compute_secloss_with_varying_q(guess_file, pwfname):
    pwm = Passwords(pwfname)
    guesses = [w for w, _ in json.load(open(guess_file))]
    guess_set = dict((g, i) for i, g in enumerate(guesses))
    
    q = len(guesses)
    union_ball = list(set([
        rpw
        for w in guesses
        for rpw in KB.word_to_typos(str(w))
        if pwm.pw2id(rpw)>=0
    ]))
    freqs = np.array([pwm.pw2freq(w) for w in union_ball])
    M = np.full((len(union_ball), NH_SIZE+1), -1, dtype=np.int32)
    for i, rpw in enumerate(union_ball):
        for j, tpw in enumerate(get_typodist_nh(rpw, NH_SIZE)):
            M[i, j] = guess_set.get(tpw, -1)
    print("Useful typos:", (M>0).sum())
    tq = 1
    lambda_topk_q = []
    while tq<q:
        if lambda_topk_q:
            last_suc = lambda_topk_q[-1][1]
        else:
            last_suc = 0
        for g in guesses[tq:tq*10]:
            t = guess_set[g]
            last_suc += freqs[(M==t).sum(axis=1)>0].sum()
            freqs[(M==t).sum(axis=0)>0] = 0
        lambda_topk_q.append((tq*10, last_suc/pwm.totalf()))
        print(tq, lambda_topk_q[-1])
        tq *= 10

    with open('guess_file.csv', 'wb') as f:
        csvf = csv.writer(f)
        csvf.writerow('q,lambda_q,lambda_typodist_q'.split())
        for tq, succ in lambda_topk_q:
            lambda_q = pwm.sumvalues(tq)/pwm.totalf()
            csvf.writerow([tq, lambda_q, succ])
    
if __name__ == "__main__":
    compute_secloss(sys.argv[1], sys.argv[2])
    
