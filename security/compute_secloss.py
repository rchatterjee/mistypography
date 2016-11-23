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
from compute_guesses_numpy import (
    get_topk_typos, get_typodist_nh, read_pw_nh_graph, get_trie_key, get_trie_id,
    N
)

KB = Keyboard()
NH_SIZE = 10
def compute_secloss(guess_file, attpwf, chlpwf, q=100):
    chlpwm = Passwords(chlpwf, max_pass_len=25, min_pass_len=5)
    attpwm = Passwords(attpwf, max_pass_len=25, min_pass_len=5)
    guesses = [w for w, _ in json.load(open(guess_file))]
    guess_set = set(guesses)
    q = len(guesses)
    print("Found {} guesses".format(q))
    lambda_q = sum(chlpwm.pw2freq(pw) for _id, pw, f
                   in attpwm.iterpws(q))/float(chlpwm.totalf())
    print("Normal succces: {}".format(lambda_q))
    union_ball = set([
        rpw
        for w in guesses
        for rpw in KB.word_to_typos(str(w))
        if chlpwm.pw2id(rpw)>=0
    ]) | guess_set

    print("Worst case success rate = {}"\
          .format(sum(chlpwm.pw2freq(w) for w in union_ball)/float(chlpwm.totalf())))

    # global N
    # N = 10000
    # M, A, typo_trie, _ = read_pw_nh_graph(chlpwf, N)
    # Mprime = np.zeros((M.shape[0], NH_SIZE+1))
    # B = [[] for _ in guesses]
    # # for g in xrange(M.shape[0]):
    # M = Mprime
    # fuzzlambda_q = 0.0
    # guess_key_ids = [get_trie_id(typo_trie, g) for g in guess_set]
    # killed = []

    # for rpw in union_ball:
    #     try:
    #         rpwid = typo_trie.key_id(unicode(rpw))
    #         for g in guess_key_ids:
    #             if (M[M[:, 0] == rpwid] == g).any:
    #                 killed.append(rpw)
    #     except KeyError:
    #         continue
    # fuzzlambda_q = sum([chlpwm.pw2freq(w) for w in killed])/chlpwm.totalf()
    # for rpw in union_ball:
    #     a = set(get_topk_typos(rpw, NH_SIZE+1)) & guess_set
    #     if a:
    #         print rpw, chlpwm.pw2freq(rpw)

    fuzzlambda_q = sum(
        chlpwm.pw2freq(rpw)
        for rpw in union_ball
        if len(set(get_topk_typos(rpw, NH_SIZE)) & guess_set)>0
    )/float(chlpwm.totalf())
    # print("fuzzlambda_q:", fuzzlambda_q),

    # lambda_topk_q = sum(
    #     chlpwm.pw2freq(rpw)
    #     for rpw in union_ball
    #     if len(set(get_typodist_nh(rpw, NH_SIZE)) & guess_set)>0
    # )/chlpwm.totalf()
    print("fuzzlambda_q: ", fuzzlambda_q)
    print("Secloss:", fuzzlambda_q - lambda_q)

def compute_secloss_with_varying_q(guess_file, attpwf, chlpwf, q=100):
    chlpwm = Passwords(chlpwf, max_pass_len=25, min_pass_len=5)
    attpwm = Passwords(attpwf, max_pass_len=25, min_pass_len=5)

    guesses = [w for w, _ in json.load(open(guess_file))]
    guess_set = dict((g, i) for i, g in enumerate(guesses))

    q = len(guesses)
    union_ball = list(set([
        rpw
        for w in guesses
        for rpw in KB.word_to_typos(str(w))
        if chlpwm.pw2id(rpw)>=0
    ]))

    freqs = np.array([chlpwm.pw2freq(w) for w in union_ball])
    M = np.full((len(union_ball), NH_SIZE+1), -1, dtype=np.int32)
    for i, rpw in enumerate(union_ball):
        for j, tpw in enumerate(get_topk_typos(rpw, NH_SIZE)):
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
            last_suc += freqs[(M==t).sum(axis=1)>0].sum()/float(chlpwm.totalf())
            freqs[(M==t).sum(axis=1)>0] = 0
        lambda_topk_q.append((tq*10, last_suc))
        print(lambda_topk_q[-1])
        tq *= 10

    with open('guess_file.csv', 'wb') as f:
        csvf = csv.writer(f)
        csvf.writerow('q,lambda_q,secloss'.split())
        for tq, succ in lambda_topk_q:
            lambda_q = chlpwm.sumvalues(tq)/float(chlpwm.totalf())
            csvf.writerow([tq, lambda_q, succ-lambda_q])

if __name__ == "__main__":
    compute_secloss(sys.argv[1], sys.argv[2], sys.argv[3])
    compute_secloss_with_varying_q(sys.argv[1], sys.argv[2], sys.argv[3])
