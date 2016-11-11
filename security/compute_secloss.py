import string
import sys, os, json
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
def compute_secloss(guess_file, pwfname):
    pwm = Passwords(pwfname)
    guesses = [w for w, _ in json.load(open(guess_file))]
    q = len(guesses)
    print("Found {} guesses".format(q))
    print("Normal succces: {}".format(pwm.sumvalues(q)/pwm.totalf()))
    union_ball = set([
        rpw
        for w in guesses
        for rpw in KB.word_to_typos(str(w))
        if pwm.pw2id(rpw)>=0
    ])
    print("Worst case success rate = {}"\
          .format(sum(pwm.pw2freq(w) for w in union_ball)/pwm.totalf()))

    print("Topk Corr: ")
    for rpw in union_ball:
        get_typodist_nh(rpw)
    print("Topk Tpomodel: ")
    
