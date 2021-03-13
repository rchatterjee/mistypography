"""Goal: Best set of guesses for the optimal attacker against a relaxed checker.
The best guesses are computed using greedy algorithm (and iterated greedy (TODO)
algoritm).

Returns: a file containing the list of guesses, and the guessing probability for
q=5,10,100,1000, q (user input)

"""

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



rpw_done = set()  # to refrain from reintroducing a ball
global_attacker_pwmodel = None # Only used in power
global_typofixer = None # Only used in power
def power(tpw):
    global global_typofixer, global_attacker_pwmodel, rpw_done
    return -sum(
        global_attacker_pwmodel.prob(pw)
        for pw in
        ((global_typofixer.check(tpw)|set([tpw]))-rpw_done)
    )

def greedy_maxcoverage_heap(attacker_pwmodel, typofixer, q=100):
    """
    Creates a list of q best guesses.
    """
    print("Guessing for DETERMINISTIC typo correction")
    global rpw_done, global_typofixer, global_attacker_pwmodel
    global_typofixer = typofixer
    global_attacker_pwmodel = attacker_pwmodel

    subset_heap = priority_dict()
    b = typofixer.max_ball_size  # ball size
    pwlist = attacker_pwmodel.iterpasswords()
    guess_list = []
    l = 0
    normal_guesses = []
    def totp(l):
        return sum(attacker_pwmodel.prob(pw) for pw in l)

    while len(guess_list) < q:
        rpw, _ = next(pwlist)
        if len(rpw)<6:
            continue
        if len(normal_guesses)<q:
            normal_guesses.append(rpw)
        p = attacker_pwmodel.prob(rpw)
        # if subset heap is not empty, take out the heaviest ball in it
        if subset_heap:
            [tpw, weight] = subset_heap.pop_smallest()
            weight = -weight
            if weight <= 0:
                print("You have exhaused all the options")
                break;
            while weight >= b()*p > 0 and len(guess_list) < q:
                # w =  -sum(attacker_pwmodel.prob(pw) for pw in typofixer.get_ball(tpw)-done)
                # assert w  == weight, "{!r} ::= {} <---> {}".format(tpw, w, weight)
                print("Guess {:04d}:  {!r}, weight={}, new_ball={}, actual-cover={}" \
                      .format(len(guess_list), tpw, weight,
                              list((typofixer.check(tpw)|set([tpw])) - rpw_done)[:10],
                              power(tpw)))
                guess_list.append(tpw)
                new_killed = (typofixer.check(tpw) | set([tpw])) - rpw_done
                rpw_done |= new_killed

                for rrpw in new_killed:  # kill all these passwords
                    tp = attacker_pwmodel.prob(rrpw)  # get its probability
                    # inform all its neighbors, rrpw is not in the nh of rrpw,
                    for ttpw in typofixer.get_nh(rrpw)|set([rrpw]):
                        if ttpw in subset_heap and typofixer.check(ttpw, rrpw):
                            subset_heap[ttpw] += tp
                            if subset_heap[ttpw] >= 0:
                                 del subset_heap[ttpw]
                if subset_heap:
                    tpw, weight = subset_heap.pop_smallest()
                    weight = -weight
                else:
                    break;

            if tpw and weight > 0 and tpw not in subset_heap and tpw not in guess_list:
                # assert tpw not in subset_heap
                subset_heap[tpw] = -weight

        # Insert the neighbors of this rpw
        # all the neighbors including itself
        # if it is not already dead or in the heap
        all_nhs = [ttpw for ttpw in typofixer.get_nh(rpw) | set([rpw])
                   if (ttpw not in subset_heap) and (ttpw not in guess_list)]
        # weights = [power(ttpw) for ttpw in all_nhs]
        with joblib.Parallel(n_jobs=7) as parallel:
            weights = parallel(
                joblib.delayed(power)(ttpw)
                for ttpw in all_nhs
            )
        for ttpw, pwr in zip(all_nhs, weights):
            subset_heap[ttpw] = pwr # -power(ttpw)
            # mw = max(mw, subset_heap[ttpw])
        # estimated_ball_weight = estimated_ball_weight * 0.8 - mw * 0.2
        if len(subset_heap) > l:
            print("Heap size: {0}".format(len(subset_heap)))
            l = len(subset_heap) * 2

    return {
        'typo_guesslist': guess_list,
        'normal_guesslist': normal_guesses,
        'attacker_model': str(attacker_pwmodel),
        'typofixer': str(typofixer)
    }



################################################################################
from pwmodel import HistPw
from typofixer.checker import Checker, BUILT_IN_CHECKERS
OUTPUT_f = "guesslist-{}.json"

def compute_guesses_and_success_rate(checker, q, passwordFile, attackerFile):
    q = int(q)
    pwm = HistPw(passwordFile)
    ######################## Parameters #######################
    attacker_pwmodel = HistPw(os.path.expanduser(attackerFile))
    typofixer = BUILT_IN_CHECKERS[checker]
    params = '{}-{}'.format(checker, q) # attacker's pw dist is always rockyou
    ############################################################
    global OUTPUT_f
    OUTPUT_f = OUTPUT_f.format(params)
    if os.path.exists(OUTPUT_f):
        A = json.load(open(OUTPUT_f))
    else:
        A = greedy_maxcoverage_heap(attacker_pwmodel, typofixer, q=q)
        with open(OUTPUT_f.format(params), 'w') as logf:
            json.dump(A, logf, indent=2)
    typo_guesses = A['typo_guesslist']
    normal_guesses = A['normal_guesslist']

    print("\n{:*^60}".format("Security loss"))
    print("{:>5s}, {:>9s}, {:>13s}, {:>8s}".format("q", "lambda_q", "lambda_t_q", "secloss"))

    def totprob(l):
        return sum(pwm.prob(pw) for pw in l)

    for tq in [10, 100, 1000]:
        if tq>q:
            continue
        ball = set()
        for guess in typo_guesses[:tq]:
            guesses = typofixer.check(guess)
            for pw in guesses:
                ball.add(pw)
        # print "Passwords that are not queried:", set(normal_guesses[:tq]) - ball
        # print "New passwords that will be compromised:", ball - set(normal_guesses[:tq])
        lambda_q = totprob(normal_guesses[:tq])
        lambda_tilde_q = totprob(ball)
        # print(normal_guesses[:tq])
        # print(ball)
        print("{:5d}, {:-9.5f}, {:-13.5f}, {:-8.5f}" \
            .format(tq, lambda_q, lambda_tilde_q, (lambda_tilde_q - lambda_q)))


if __name__ == "__main__":
    # attacker_model = ""
    # real_pw_model = ""
    if len(sys.argv)<4:
        print("""
You need to provide 3 things: a checker, a value of 'q', and a filename for real password distribution
e.g.: $ python {} ChkBl_Top3 10 ~/passwrods/rockyou-withcount.txt.bz2\n""".format(__file__) )
        exit(1)
    else:
        chker = sys.argv[1]
        q = int(sys.argv[2])
        passwordFile = sys.argv[3]
        attackerFile = sys.argv[4]
        if chker not in BUILT_IN_CHECKERS:
            print("Your cheker ({}) is not in my list. Please use one of the following.".format(chker))
            print(BUILT_IN_CHECKERS.keys())
            exit(2)
        compute_guesses_and_success_rate(chker, q, passwordFile, attackerFile)