# Compute the security loss of edit 1 correction for q guesses.
# Required: A typo model, or a way to generate the neighborhood of a password
# 1. Create the neighborhood graph of the real password, and then
# 2. Create the ball structure (somehow)
# 3. After having a data structure for balls, and neighbors, computing
#    guesses is no brainer.
# Main Challenge: How to store those data structures in disk, and load it.

# What I do right now, create trie of the typos, and a gigantic matrix
# of neigborhood map, this is okay because we decide to have a fixed
# length neighborhood.  The balls are some stored some time they are
# just comptued on the fly.

## TODO: Updatable typo trie, so that givea typo trie, we can add more
## item to it.

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
from word2keypress import Keyboard
from word2keypress.weighted_edist import sample_typos, get_topk_typos
from zxcvbn import password_strength


num2sym = dict(zip("`1234567890-=~!@#$%^&*()_+", "~!@#$%^&*()_+`1234567890-="))

KB = Keyboard()
allowed_chars = string.printable[:-5]
MIN_ENTROPY = 10
REL_ENT_CUTOFF = -3
EDIT_DIST_CUTOFF = 1
MAX_NH_SIZE = 1000
CACHE_SIZE = 5
N = int(1e6) # Number of rockyou password to consider
SPLIT = 10000
Q = 10000
def set_globals(settings_i):
    # MIN_ENT, REL_ENT, MAX_NH_SIZE, CACHE_SIZE,
    global MIN_ENTROPY, REL_ENT_CUTOFF, MAX_NH_SIZE, CACHE_SIZE, Q
    settings = [
        (10, -3, 1000, 5, 10000),
        (0, 0, 1000, 5, 10000),
    ]
    MIN_ENTROPY, REL_ENT, MAX_NH_SIZE, CACHE_SIZE, Q = settings[settings_i]

def get_nh(w):
    """
    Find the neighborhood of a password w, also enforces the policies.
    1. the minimum entropy cutoff
    2. the relative entropy cutoff
    3. edit distance cutoff, no options, only 1
    ## HARD CUTOFF of 300 only
    """
    ent_w = entropy(w)
    ret = ['' for _ in xrange(MAX_NH_SIZE+1)]
    ret[0] = w
    i = 1
    done = set([w])
    def filter_(tpw):
        if tpw in done: return False
        done.add(tpw)
        tpw = str(tpw.encode('utf-8', errors='ignore'))
        if MIN_ENTROPY != 0 and REL_ENT_CUTOFF != 0:
            ent_tpw = entropy(tpw)
            return (ent_tpw>=MIN_ENTROPY and
                    (ent_tpw-ent_w)>=REL_ENT_CUTOFF)
        else:
            return True
    for tpw in KB.word_to_typos(str(w)):
        if not filter_(tpw): continue
        ret[i] = tpw
        i += 1
        if i>MAX_NH_SIZE:
            break
    return ret

def entropy(w):
    try:
        return password_strength(w)['entropy']
    except Exception as e:
        print (e)
        return -1

pwd = os.path.dirname(os.path.abspath(__file__))
from collections import OrderedDict
import marisa_trie

def create_part_pw_nh_graph(args):
    pwm, s, e = args
    assert e>s
    typodir = '{}/typodir'.format(pwd)
    tpw_trie_fname = '{}/{}__{}_{}_typo.trie'.format(typodir, pwm.fbasename, s, e)
    rpw_nh_graph = '{}/{}__{}_{}_rpw_nh_graph.npz'.format(typodir, pwm.fbasename, s, e)
    if os.path.exists(tpw_trie_fname) and os.path.exists(rpw_nh_graph):
        typo_trie = marisa_trie.Trie()
        typo_trie.load(tpw_trie_fname)
        M = np.load(rpw_nh_graph)['M']
        return typo_trie, M
    typos = OrderedDict()
    k = e-s
    M = np.full((k, MAX_NH_SIZE+1), -1, dtype=int)
    # typo_f = open('{}/typos.txt', 'a')
    def get_typo_id(typo):
        try:
            return typos[typo]
        except KeyError:
            # typo_f.write(typo + '\n')
            typos[typo] = len(typos)
            return typos[typo]
    average_nh_size = 0
    for i, (pwid, f) in enumerate(pwm):
        if i>=e: break
        if i<s: continue
        rpw = str(pwm.id2pw(pwid).encode('ascii', errors='ignore'))
        nh = get_nh(rpw)
        # M[i-s, 0] = pwid
        average_nh_size += len(nh)
        M[i-s, :len(nh)] = np.fromiter((get_typo_id(tpw) for tpw in nh), dtype=int)
        if (i>s and i%400==0):
            print "Done {} -- len(typos)={}".format(i, len(typos))

    if not os.path.exists(typodir):
        os.makedirs(typodir)
    typo_keys = typos.keys()
    typo_trie = marisa_trie.Trie(typo_keys)
    for i in xrange(k):
        M[i] = np.fromiter(
            (typo_trie.key_id(unicode(typo_keys[c])) if c>=0 else -1
             for c in M[i]),
            dtype=int
        )
    np.savez_compressed(rpw_nh_graph, M=M)
    typo_trie.save(tpw_trie_fname)
    print("Average NH size: {}".format(average_nh_size/float(k)))
    return

M = None
def _update_M(global_typo_trie, trie_i, tM):
    A = np.zeros(len(trie_i))
    for k, _id in trie_i.iteritems():
        A[_id] = global_typo_trie.key_id(k)
    for i in xrange(tM.shape[0]):
        tM[i] = A[tM[i]]
    return tM

def join_pw_nh_graphs(args):
    pwm, split, s, e = args
    typodir = '{}/typodir'.format(pwd)
    tpw_trie_fname = '{}/{}__{{}}_{{}}_typo.trie'.format(typodir, pwm.fbasename)
    rpw_nh_graph = '{}/{}__{{}}_{{}}_rpw_nh_graph.npz'.format(typodir, pwm.fbasename)

    joined_tpw_trie_fname = '{}/{}__{}_{}_typo.trie'\
                            .format(typodir, pwm.fbasename, s, e)
    joined_rpw_nh_graph = '{}/{}__{}_{}_rpw_nh_graph.npz'\
                          .format(typodir, pwm.fbasename, s, e)
    if os.path.exists(joined_rpw_nh_graph) and os.path.exists(joined_tpw_trie_fname):
        print(
            "{} and {} exits. So returning"\
            .format(os.path.basename(joined_tpw_trie_fname),
                    os.path.basename(joined_tpw_trie_fname))
        )
        return
    tries = []
    N = e-s
    print("Joining: {}".format(args))
    M = np.full((N, MAX_NH_SIZE+1), fill_value=-1, dtype=int)
    for i in xrange(0, N, split):
        ts, te = i+s, i+s+split
        typo_trie = marisa_trie.Trie()
        typo_trie.load(tpw_trie_fname.format(ts, te))
        tries.append(typo_trie)
        print("Reading: {}".format(rpw_nh_graph.format(ts, te))),
        M[i:i+split] = np.load(rpw_nh_graph.format(ts, te))['M']
        print("...Done")
    print("Joining trees")
    global_typo_trie = marisa_trie.Trie(
        k
        for  tt in tries
        for k in tt.iterkeys()
    )
    print("Number of typos: ", len(global_typo_trie))
    args = ((global_typo_trie, tries[i/split], M[i:i+split])
            for i in xrange(0, N, split))
    # pool = multiprocessing.Pool()
    # res = map(_update_M, args)
    for i in xrange(0, N, split):
        trie_i = tries[i/split]
        # M[i:i+split]  = _update_M(global_typo_trie, trie_i, M[i:i+split])
        M[i:i+split] = _update_M(global_typo_trie, trie_i, M[i:i+split])

    # for i in xrange(M.shape[0]):
    #     if i % split == 0:
    #         print("Accumulating: {}".format(i))
    #     trie_i = tries[i/split]
    #     for j in xrange(M.shape[1]):
    #         if M[i, j]<0: continue
    #         M[i, j] = global_typo_trie.key_id(trie_i.restore_key(M[i, j]))
    print("Saving all data... {} {}".format(joined_tpw_trie_fname, joined_rpw_nh_graph))
    np.savez_compressed(joined_rpw_nh_graph, M=M)
    global_typo_trie.save(joined_tpw_trie_fname)
    print("Done!")

def create_pw_nh_graph(fname):
    pwm = Passwords(fname, max_pass_len=25, min_pass_len=5)
    split = SPLIT
    # N = 1000
    pool = multiprocessing.Pool()
    # Create with split 1000
    args = [(pwm, i, i+split) for i in xrange(0, N, split)]
    pool.map(create_part_pw_nh_graph, args)
    print("Done creating all the parts")
    # Join 10 at time.
    multiplier = 10
    if N<1e5:
        join_pw_nh_graphs(pwm, split, 0, N)
    else:
        args1 = [(pwm, split, i, i+split*100) for i in xrange(0, N, split*100)]
        pool.map(join_pw_nh_graphs, args1)
        join_pw_nh_graphs((pwm, split*100, 0, N))

    # while split < N:
    #     args = [(pwm, split, i, i+split*multiplier)
    #             for i in xrange(0, N, split*multiplier)]
    #     pool.map(join_pw_nh_graphs, args)
    #     split *= multiplier

def read_pw_nh_graph(fname, q=-1):
    """Reads the typo trie file and the neighborhood map created by
    `create_pw_nh_graph` function.

    Returns: (M, A, typo_trie)
    M is the rpw -> Neighborhood information
      - M[i][0] is the rpw_id, of i-th most probable password
      - M[i][1:] is the neighborhood, truncted to MAX_NH_SIZE (500)
    A is the weight of the balls of all the typos we collected
      - A[i] = Total sum of frequencies of all the rpw in the ball
               of i-th password in trie. (see typo_trie)
    typo_trie is a maping from typo_id to typos, so, to retrieve
    the i-th typo in A[i], use typo_trie.restore_key(i).
    typo_trie is not required for computing the total success of
    an attacker.
    q: Prune the typo list based on q value, so that don't worry
       about typos that are very low in the tail, for example, a
       typo with total ball weight < 10*q-th most probable typo, is
       most likely useless. Where assume the average ball size is 10.
    """
    # N = 1000
    typodir = '{}/typodir'.format(pwd)
    pwm = Passwords(fname, max_pass_len=25, min_pass_len=5)
    tpw_trie_fname = '{}/{}__{}_{}_typo.trie'\
                     .format(typodir, pwm.fbasename, 0, N)
    rpw_nh_graph = '{}/{}__{}_{}_rpw_nh_graph.npz'\
                   .format(typodir, pwm.fbasename, 0, N)

    typo_trie = marisa_trie.Trie()
    typo_trie.load(tpw_trie_fname)
    M = np.load(rpw_nh_graph)['M']
    ## Extra fix ##
    M[M==0] = -1
    d = len(typo_trie)
    A = np.zeros(len(typo_trie))
    for i in xrange(M.shape[0]):
        if M[i, 0] <=0:
            continue
        p_rpw = pwm.pw2freq(typo_trie.restore_key(M[i, 0]))
        A[M[i, M[i]>=0]] += p_rpw

    print("Done creating the 'A' array. Size={}".format(A.shape))
    # # Prune the typos, Not all typos are useful, any typo with
    # # frequency less than i_th most probable password will never be
    # # queried.
    # b = (M>0).sum() / float(A.shape[0])   # average ball size
    # print("Average ball size: {}".format(b))
    # bq_th_pw_f = pwm.id2freq(M[int(b*q)][0])
    # useful_typos = (A>=bq_th_pw_f)
    # print("Useful typos (> {}): {}/{}".format(
    #     bq_th_pw_f, useful_typos.sum(), A.shape[0]
    # ))
    return M, A, typo_trie, pwm

def get_topk_typos(rpw, nh_size):
    add_at_end = ['1`0/234']
    ret = [
        rpw.swapcase(), rpw[1].lower()+row[1:],
        rpw[:-1] + num2sym.get(rpw[-1], rpw[-1]),
        rpw[0] + rpw,
    ]
    ret.extend((rpw + c for c in add_at_end))
    return ret


def get_typodist_nh(rpw, nh_size, topk=True):
    ent_rpw = entropy(rpw)
    ret = ['' for _ in range(nh_size+1)]
    ret[0] = rpw
    done = set([rpw])
    i = 1
    if topk:
        typos = get_topk_typos(rpw, 2*nh_size)
    else:
        assert 0, "Useless process. Run with topk=True"
        typos = sample_typos(rpw, 2*nh_size)
    for tpw in typos:
        if tpw in done: continue
        done.add(tpw)
        ent_tpw = entropy(tpw)
        if (ent_tpw>=MIN_ENTROPY and
            (ent_tpw-ent_rpw)>=REL_ENT_CUTOFF):
            ret[i] = tpw
            i += 1
            if i>nh_size: break;
    return ret

def compute_guesses_using_typodist(fname, q, nh_size=5, topk=False):
    """
    Computes the Neighborhood based on sampling from the typo distribution.
    """
    # Re-create the neighborhood, it should be small
    global proc_name
    if topk:
        proc_name = "TYPODIST-TOPK"
    else:
        proc_name = "TYPODIST"
    pwm = Passwords(fname, max_pass_len=25, min_pass_len=5)
    typos = OrderedDict()
    def get_typo_id(_typo):
        if not _typo: return -1
        try:
            return typos[_typo]
        except KeyError:
            # typo_f.write(typo + '\n')
            typos[_typo] = len(typos)
            return typos[_typo]

    M = np.full((N, nh_size+1), -1, dtype=int)
    B = [[] for _ in xrange((nh_size+1)*N)]
    A = np.zeros(N*(nh_size+1))
    i = 0
    for (pwid, f) in pwm:
        if i>=N: break
        rpw = str(pwm.id2pw(pwid).encode('ascii', errors='ignore'))
        if pwid != pwm.pw2id(rpw):
            print("Pwid changed for {!r}".format(rpw))
            continue
        # if any(M[:, 0] == pwid):
        #     print("{!r} is already considered".format(rpw))
        #     continue
        if len(rpw)<4: continue
        T = get_typodist_nh(rpw, nh_size, topk)
        M[i] = [
            get_typo_id(tpw)
            for tpw in T
        ]
        A[M[i, M[i]>=0]] += f
        for tpwid in M[i, M[i]>=0]:
            B[tpwid].append(i)
        if (i>0 and i%10000==0):
            print("Processed: {}".format(i))
        i += 1

    # A = A[A>0]
    # typo_trie = marisa_trie.Trie(typos.keys())
    # assert A.shape[0] == len(typos)
    typos = typos.keys()
    guesses = []
    i = 0
    killed = np.ones(M.shape[0], dtype=bool)
    while len(guesses)<q:
        gi = A.argmax() # tpwid of the i-th guess
        # Set of rows where gi exists
        killed_gi = B[gi]
        killed[killed_gi] = False
        e = (typos[gi], A[gi]/pwm.totalf())
        assert e not in guesses, "Guesses={}, e={}, killed_gi={}, M[killed_gi]={}"\
            .format(guesses, e, gi, M[killed_gi])
        guesses.append(e)
        for row in M[killed_gi]:
            f = pwm.pw2freq(typos[row[0]])
            assert f>0, "RPW freq is zero! rpw={}, f={}, guess={}"\
                .format(typos[row[0]], f, typos[gi])
            A[row] -= f
        print("({}): {}> {:30s}: {:.3e} (killed={}/{})".format(
            proc_name,
            len(guesses), guesses[-1][0],
            guesses[-1][1]*100, len(killed_gi), M.shape[0]-killed.sum()
        ))
        # if (0.99*M.shape[0] > killed.sum()):
        #     M = M[killed]
        #     killed = np.ones(M.shape[0], dtype=bool)
        #     print("New shape of M: {}".format(M.shape))
    # for i, (g, p) in enumerate(guesses):
    #     print "{}: {} -> {}".format(i, typo_trie.restore_key(g), p)
    print("({}): Total fuzzy success: {}"\
          .format(proc_name, 100*sum(g[1] for g in guesses)))
    print("({}): Total normal success: {}"\
          .format(proc_name, 100*pwm.sumvalues(q)/pwm.totalf()))
    guess_f = 'guesses/{}_guesses_{}_typodist_{}_{}.json'\
              .format(pwm.fbasename, q, nh_size, proc_name)
    with open(guess_f, 'w') as f:
        json.dumps(guesses, f, indent=4)

def compute_guesses_random(fname, q, k=5):
    """
    Goal is to compute the fuzzy success rate given query budget of q.
    This time instead of considering 500 points in the neighborhood, we took
    random 5 of them, and compute guessing success given that new
    neighborhood graph.
    """
    global proc_name
    proc_name = "RANDOM"
    M, A, typo_trie, pwm = read_pw_nh_graph(fname)
    guess_f = 'guesses/{}_guesses_{}_random_{}.json'.format(pwm.fbasename, q, k)
    A = np.zeros(len(typo_trie))
    tM = np.full((M.shape[0], -1, k+1), dtype=int)
    for i in xrange(M.shape[0]):
        tM[i, 0] = M[i, 0]
        if tM[i, 0] == -1:
            continue
        try:
            tM[i, 1:] = np.random.choice(M[i, M[i]>0][1:], k, replace=False)
        except ValueError as e:
            print("{}: No neighbor for {!r} ({})".format(proc_name, pwm.id2pw(tM[i, 0]), tM[i, 0]))
            tM[i, 1:] = np.zeros(k)
        p_rpw = pwm.pw2freq(typo_trie.restore_key(M[i, 0]))
        A[tM[i, tM[i, :]>=0]] += p_rpw
    with open(guess_f, 'w') as f:
        json.dump(_comptue_fuzz_success(pwm, tM, A, typo_trie, q), f, indent=4)

proc_name = 'ALL'
def compute_guesses_all(fname, q):
    """We computed neighborhood graph, considering the neighborhood graph
    of size 500. Given this neighborhood graph we compute the best set
    of guesses in greedy procedure.
    """
    M, A, typo_trie, pwm = read_pw_nh_graph(fname)
    guess_f = 'guesses/{}_guesses_{}_all.json'.format(pwm.fbasename, q)
    with open(guess_f, 'w') as f:
        json.dump(_comptue_fuzz_success(pwm, M, A, typo_trie, q), f, indent=4)

def _comptue_fuzz_success(pwm, M, A, typo_trie, q):
    """
    pwm: object of type Password (readpw.py)
    M: a 2D numpy matrix, containing rpwid|tpwid_1|tpwid_2....
    typo_trie: trie of all typos.
    A: Of size eualto the size of typo_trie, and contains the
       weight of the ball around each typo.
    computes the best q guesses using greedy approach.
    """
    assert M.shape[0]>2*q, "We don't have enough data to make guesses. "\
        "Only {}".format(M.shape[0])
    killed = np.ones(M.shape[0], dtype=bool)
    guesses = []
    i = 0
    B = np.array(A.shape[0], dtype=bool)
    for r in xrange(M.shape[0]):
        t = M[r]
        B[t][B[t]<r] = r

    while len(guesses)<q:
        gi = A.argmax()
        # Set of rows where gi exists
        killed_gi = ((M[:r]==gi).sum(axis=1))>0
        killed[killed_gi] = False
        guesses.append((typo_trie.restore_key(gi), A[gi]/pwm.totalf()))
        for row in M[killed_gi]:
            A[row] -= pwm.pw2freq(typo_trie.restore_key(row[0]))
        print("({}): {}> {:30s}: {:.3f} (killed={}/{})".format(
            proc_name,
            len(guesses),
            guesses[-1][0],
            guesses[-1][1]*100, killed_gi.sum(), M.shape[0]-killed.sum()
        ))
        if (0.99*M.shape[0] > killed.sum()):
            M = M[killed]
            killed = np.ones(M.shape[0], dtype=bool)
            print("({}): New shape of M: {}".format(proc_name, M.shape))
    # for i, (g, p) in enumerate(guesses):
    #     print "{}: {} -> {}".format(i, typo_trie.restore_key(g), p)
    print("({}): Total fuzzy success: {}"\
          .format(proc_name, 100*sum(g[1] for g in guesses)))
    print("({}): Total normal success: {}"\
          .format(proc_name, 100*pwm.sumvalues(q)/pwm.totalf()))
    return guesses

import random
def verify(fname):
    pwm = Passwords(fname)
    typodir = '{}/typodir'.format(pwd)
    tpw_trie_fname = '{}/{}__{}_{}_typo.trie'.format(typodir, pwm.fbasename, 0, N)
    rpw_nh_graph = '{}/{}__{}_{}_rpw_nh_graph.npz'.format(typodir, pwm.fbasename, 0, N)
    print tpw_trie_fname, rpw_nh_graph
    typo_trie = marisa_trie.Trie()
    typo_trie.load(tpw_trie_fname)
    M = np.load(rpw_nh_graph)['M']
    for i, (pwid, f) in enumerate(pwm):
        if random.randint(0, 10000)<=1:
            continue
        if i>=N: break
        rpw = str(pwm.id2pw(pwid).encode('ascii', errors='ignore'))
        nh = get_nh(rpw)
        assert rpw == typo_trie.restore_key(M[i, 0]), \
            "{} <--> {}".format(pwm.id2pw(pwid), typo_trie.restore_key(M[i, 0]))
        nh_t = [typo_trie.restore_key(c) for c in M[i] if c>=0]
        assert nh == nh_t, ">>> i: {}\nNH-NH_t={}\nNH_t-NH={},\nlen(nh)={}"\
            .format(i, set(nh)-set(nh_t), set(nh_t)-set(nh), len(nh))
        if (i%100==0):
            print "Done {}".format(i)


if __name__ == '__main__':
    import sys
    # create_pw_db_(sys.argv[1])
    # approx_guesses(sys.argv[1], 1000)
    # greedy_maxcoverage_heap(sys.argv[1], 1000)
    fname = sys.argv[1]
    set_globals(settings_i=1)
    create_pw_nh_graph(fname)
    print("Done creating all the graphs")
    # verify(fname)
    q = Q
    # from multiprocessing import Process
    process = {
        'p_all':  Process(target=compute_guesses_all, args=(fname, q)),
        'p_random': Process(target=compute_guesses_random, args=(fname, q)),
        'p_typodist': Process(target=compute_guesses_using_typodist, args=(fname, q, 5, True)),
        'p_topk': Process(target=compute_guesses_using_typodist, args=(fname, q, 5, True))
    }
    process['p_typodist'].start()
    process['p_topk'].start()

    process['p_typodist'].join()
    process['p_all'].join()

    # for pname, proc in process.items():
    #     print("\n*** {} ***\n".format(pname.upper()))
    #     proc.start()
    # for pname, proc in process.items():
    #     proc.join()
    #     pass
