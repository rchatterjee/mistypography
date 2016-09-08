"""This file attempts to find maxcoverage given a collection of sets
and a file containing the weights of the elements.  Maximal coverage
is a NP-hard problem. Lets try to put togethter some heuristic here
assuming the set sizes are small etc.

"""

import json, os, sys, gc, random
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
import numpy as np
import time, datetime
from pwmodel.helper import open_
from hashlib import md5
from collections import OrderedDict, defaultdict
from heap import priority_dict

import csv
from subprocess import Popen

# from csvsort import csvsort

random.seed(16892347)

tpwfile = 'data/tempdata/tpwlist.txt.gz'
rpwfile = 'data/tempdata/rpwlist.txt.gz'
# rpwtpw = 'data/tempdata/rpwtpw.csv'
rpwtpw = 'data/tempdata/rpwtpw.txt'
tpwuniq = 'data/tempdata/rpwuniq.txt'
# subsetsfile = 'data/tempdata~test/subsets'

resultfile = 'data/tempdata/results-'
allowed_edits_7 = ['same', 'swc-all', 'swc-first', 'rm-lastc',
                   'rm-firstc', 'sws-last1', 'upncap',
                   'add1-last']
allowed_edits_5 = ['same', 'swc-all', 'swc-first',
                   'sws-last1', 'upncap',
                   'add1-last']
allowed_edits = ['keypress-edit']

# one file contains three arrays (Hats
# off to numpy). rpwlist - a lsit of
# frequencies, tpwlist - a list of typoed passwords
# subsets - the subsets. See below for details.
subsets_file = 'data/tempdata/subsets_' + str(len(allowed_edits))


def create_tpwset_files(pwmodel, aserver):
    """
    Generates a .npz (numpy data) file containing the following data fields.
    - 'tpwlist': list of tpws, ['paswords', '123456', ... ]
    - 'subset_counts': number of subsets, (list of size of subsets for each rpw)
    - 'rpwlist': List of real passwords, index -> freq
    - 'subsets': list of subsets, index->tpwlist_indeices
    - 'total_freq': total freq (int)

    @pwmodel is a attacker pwmodel, that is it has OrderedList of passwords
    @aserver is a typo fix mechanism that gives the ball and neighborhood of a
             password string

    """
    # with open_(rpwfile, 'w') as f:
    #    json.dump(pwmodel.PW2FREQ_map, f, indent=2)

    # tpwfl = open_(tpwfile, 'w')
    t0 = time.time()
    RPW = OrderedDict((pw, i) for i, pw in enumerate(pwmodel.PW2FREQ_map.keys()))
    print "Build RPW dict in {} seconds".format(time.time() - t0)

    # dump all tpw into a temp file
    i = 0
    t0 = time.time()
    with open(rpwtpw, "w") as rpwtpw_file:
        for rpw in RPW:
            for tpw in aserver.get_nh(rpw):
                rpwtpw_file.write(tpw + "\n")
                i += 1
                if (i % 20000 == 0):
                    print "Done dumping {}th tpw in {} seconds".format(i, time.time() - t0)

    t0 = time.time()
    print "Start sorting..."
    Popen("sort " + rpwtpw + " | uniq > " + tpwuniq, shell=True).wait()
    print "Done sorting in {} seconds".format(time.time() - t0)

    k = len(aserver)
    A = []
    i = 0
    done = defaultdict(int)
    tpwarr = []
    # count how many tpw (subset) have same balls
    subset_count = []

    t0 = time.time()
    # always create tpw for "same", and assign it the same id as rpw
    for rpw in RPW:
        # h = md5(rpw).digest()
        # tpwset.add(h)
        # r.sadd(tpwset, h)
        narr = sorted([RPW[rrpw] for rrpw in aserver.get_ball(rpw) if rrpw in RPW])
        tpwarr.append(rpw)
        A.append(narr)
        subset_count.append(1)
        i += 1
    print 'Dump "same" relation in {} seconds'.format(time.time() - t0)

    t0 = time.time()
    with open(tpwuniq, "r") as tpwuniq_file:
        for l in tpwuniq_file:
            # stripping the "\n"
            tpw = l[:-1]
            if tpw in pwmodel.PW2FREQ_map:
                continue
            narr = sorted([RPW[rrpw] for rrpw in aserver.get_ball(tpw) if rrpw in RPW])
            h = md5(repr(narr)).digest()
            if h not in done:
                # tpwfl.write(tpw + '\n')
                tpwarr.append(tpw)
                A.append(narr)
                done[h] = i
                subset_count.append(0)
                i += 1
                if (i % 20000 == 0):
                    print "Done {} -- tpw={}, len(done)={}, in {} seconds".format(i, tpw, len(done), time.time() - t0)
            subset_count[done[h]] += 1

    os.remove(tpwuniq)
    os.remove(rpwtpw)
    """
    t0 = time.time()
    for rpw in RPW:
        for tpw in aserver.get_nh(rpw):
            # check whether this tpw is seen before
            # preventing duplicate subset_count
            # tpwset already contains "same", will always skip
            h = md5(tpw).digest()
            #if h in tpwset:
            if r.sismember(tpwset, h):
                continue
            else:
                #tpwset.add(h)
                r.sadd(tpwset, h)
            narr = sorted([RPW[rrpw] for rrpw in aserver.get_ball(tpw) if rrpw in RPW])
            h = md5(repr(narr)).digest()
            if h not in done:
                #tpwfl.write(tpw + '\n')
                tpwarr.append(tpw)
                A.append(narr)
                done[h] = i
                subset_count.append(0)
                i += 1
                if (i%20000==0):
                    print "Done {} -- rpw={}, len(done)={}, in {} seconds".format(i, rpw, len(done), time.time() - t0)
            subset_count[done[h]] += 1
    """

    subsets_arr = np.array(A)
    print "Going to save the files at {}".format(subsets_file),
    np.savez_compressed(subsets_file,
                        rpwlist=pwmodel.PW2FREQ_map.values(),
                        tpwlist=tpwarr,
                        subsets=subsets_arr,
                        subset_counts=subset_count,
                        total_freq=pwmodel.total_freq())
    print "..Saved!"
    # np.save(subsetsfile, subsets_arr)
    # print subsets_arr


rpwlist, tpwlist, subsets, subset_counts = None, None, None, None
rpw2subset = None  # a 2D array where i'th row contain the index of
# the subsets where the element i is present in subsets array
total_freq = 0


def read_required_files():
    """
    Reads all the required files, such as rpwlist, tpwlist, and subsets.npy
    Retursn three objects,
      rpwlist = is OrderedDict,
      tpwlist = an array
      subsets = numpy array
    """
    global rpwlist, tpwlist, subsets, rpw2subset, subset_counts, total_freq
    if rpwlist is not None and tpwlist is not None and subsets is not None: return
    d = np.load(subsets_file + '.npz')
    rpwlist = d['rpwlist']
    tpwlist = d['tpwlist']
    subsets = d['subsets']
    subset_counts = d['subset_counts']
    total_freq = d['total_freq']
    A = [[] for _ in rpwlist]
    for i, a in enumerate(subsets):
        for x in a:
            A[x].append(i)
    rpw2subset = np.array(A)
    print "Done reading the .npz file"
    return


def greedy_maxcoverage_heap(attacker_pwmodel, typofixer, q=100):
    """
    Creates a list of q possible 
    """
    print "Guessing for DETERMINISTIC typo correction"
    subset_heap = priority_dict()
    b = typofixer.max_ball_size
    n = typofixer.max_nh_size
    pwlist = attacker_pwmodel.iterpasswords()
    guess_list = []
    tpw_done = set()  # to make the probabiltiy zero, 
    rpw_done = set()  # to refrain from reintroducing a ball
    l = 0
    estimated_ball_weight = 0.0

    def totp(l):
        return sum(attacker_pwmodel.prob(pw) for pw in l)

    def power(tpw):
        return totp((typofixer.get_ball(tpw)|set([tpw]))-rpw_done)

    while len(guess_list) < q:
        rpw, _ = pwlist.next()
        p = attacker_pwmodel.prob(rpw)
        if estimated_ball_weight <= 0:
            estimated_ball_weight = p * b()  # The weight of the heaviest ball in rpw's neighbor
        if subset_heap:  # if subset heap is not empty, take out the heaviest ball in it
            [tpw, weight] = subset_heap.pop_smallest()
            weight = -weight
            if weight <= 0:
                print "You have exhaused all the options"
                break;
            while weight >= b()*p > 0 and len(guess_list) < q:
                # w =  -sum(attacker_pwmodel.prob(pw) for pw in typofixer.get_ball(tpw)-done)
                # assert w  == weight, "{!r} ::= {} <---> {}".format(tpw, w, weight)
                print "Guess {:04d}:  {!r}, weight={}, new_ball={}, actual-cover={}" \
                    .format(len(guess_list), tpw, weight,
                    typofixer.check(tpw)|set([tpw]) - rpw_done,
                    power(tpw))
                guess_list.append((tpw, weight))
                tpw_done.add(tpw)
                new_killed = (typofixer.check(tpw) | set([tpw])) - rpw_done
                rpw_done |= new_killed

                for rrpw in new_killed:  # kill all these passwords
                    tp = attacker_pwmodel.prob(rrpw)  # get its probability
                    for ttpw in typofixer.get_nh(rrpw)|set([rrpw]):  # inform all its neighbors, rrpw is not in the nh of rrpw,
                        if ttpw in subset_heap and typofixer.check(ttpw, rrpw):
                            subset_heap[ttpw] += tp
                            if subset_heap[ttpw] >= 0:
                                 del subset_heap[ttpw]
                if subset_heap:
                    tpw, weight = subset_heap.pop_smallest()
                    weight = -weight
                else:
                    break;

            if tpw and weight > 0 and tpw not in subset_heap and tpw not in tpw_done:
                # assert tpw not in subset_heap
                subset_heap[tpw] = -weight

        # Insert the neighbors of this rpw
        for ttpw in typofixer.get_nh(rpw) | set([rpw]): # all the neighbors including itself
            if (ttpw not in subset_heap) and (ttpw not in tpw_done): # if it is not already dead or in the heap
                subset_heap[ttpw] = -power(ttpw)
                # mw = max(mw, subset_heap[ttpw])
        # estimated_ball_weight = estimated_ball_weight * 0.8 - mw * 0.2
        if len(subset_heap) > l:
            print >> sys.stderr, "Heap size: {}".format(len(subset_heap))
            l = len(subset_heap) * 2

    return {
        'guesslist': guess_list,
        'attacker_model': str(attacker_pwmodel),
        'typofixer': str(typofixer)
    }


def greedy_maxcoverage_random_typos(pwmodel, typofixer, q=10, k=6, verbose=True):
    """Find best q-guesses for a randomimsed typo correction. The
    registration is randomized, not the autheticaiton. That means, a
    random subset of the neighborhood is stored beside the real
    password. During authenticaiton, any of the stored password is
    allowed.

    :param pwmodel: attacker's password model.

    """
    print "Guessing for RANDOMIZED typo correction"
    subset_heap = priority_dict()
    b = typofixer.max_ball_size
    n = typofixer.max_nh_size
    pwlist = pwmodel.iterpasswords()
    guess_list = []
    done = set()

    def kw_by_nw(_pw, done):
        nw = len(typofixer.get_nh(_pw) - done)
        return min(1, k / nw)

    def ball_weight(_tpw, done):
        return pwmodel.prob(_tpw) + sum(pwmodel.prob(pw) * kw_by_nw(pw, done)
                                        for pw in typofixer.get_ball(_tpw))

    while len(guess_list) < q:
        rpw, _ = pwlist.next()
        p = pwmodel.prob(rpw)
        if subset_heap:
            # print subset_heap.smallest(), rpw, p
            [tpw, weight] = subset_heap.pop_smallest()
        else:
            tpw, weight = '', 0
        if weight > 0:
            print "You have exhaused all the options"
            break;
        print rpw, p, -weight
        while weight < 0 and -weight >= (b() * p * k) / (n() + 1):  # TODO - check
            print tpw, -weight, pwmodel.prob(tpw)
            guess_list.append((tpw, -weight))
            done.add(tpw)
            for rrpw in typofixer.get_ball(tpw):
                # done.add(rrpw)
                # tp = p(rrpw) * k/n, probability that we hit this rrpw
                tp = pwmodel.prob(rrpw) * kw_by_nw(rrpw, done)
                for ttpw in typofixer.get_nh(rrpw):
                    if ttpw in subset_heap:
                        subset_heap[ttpw] += tp
                        if subset_heap[ttpw] >= 0:
                            done.add(ttpw)
                            del subset_heap[ttpw]
            if subset_heap:
                tpw, weight = subset_heap.pop_smallest()
            else:
                tpw, weight = '', 0

        if tpw and weight < 0:
            assert tpw not in subset_heap
            subset_heap[tpw] = weight
        for ttpw in typofixer.get_nh(rpw):
            if (ttpw not in subset_heap) and (ttpw not in done):
                subset_heap[ttpw] = -ball_weight(ttpw, done)
    return {
        'guesslist': guess_list,
        'attacker_model': str(pwmodel),
        'typofixer': str(typofixer)
    }


def old_greedy_maximum_coverage_random_typos(q=100, k=5, verbose=True):
    """Finds q sets from subsets, similar to greedy_maximum_coverage,
    difference is that now each rpw accepts only randomly-chosen k typoes
    """
    t0 = time.time()
    read_required_files()
    print "Files loaded in", time.time() - t0, "seconds wall time"

    # create adjusted frequency table
    adjust_freq = rpwlist.astype(float)
    large_k = np.array([sum((subset_counts[i] for i in rpw2subset[_])) - 1 for _ in range(len(rpwlist))])
    little_k = np.minimum(large_k, np.ones(len(rpwlist)) * k)
    print "Max Large K: {}, Min Little K: {}, Sum Large K: {}".format(np.max(large_k), np.min(little_k),
                                                                      np.sum(large_k))
    subset_counts_left = np.copy(subset_counts)

    # creating heap
    t0 = time.time()
    subset_heap = priority_dict()

    # parameter is set id instead of set
    def setweight(sset):
        ret = sum(adjust_freq[rpwi] * little_k[rpwi] / large_k[rpwi] for rpwi in subsets[sset] if
                  rpwi != sset and large_k[rpwi] != 0.0)
        if sset < len(adjust_freq):
            ret += adjust_freq[sset]
        return ret

    print "Creating heap"
    for i, subset in enumerate(subsets):
        w = setweight(i)
        assert (w >= 0)
        subset_heap[i] = -w
    print "Done creating the heap in", time.time() - t0, "seconds wall time"

    # Start guessing
    guess_list = []
    t0 = time.time()
    print "Start Guessing ..."
    while len(guess_list) < q:
        [setid, weight] = subset_heap.pop_smallest()
        subset_counts_left[setid] -= 1
        if subset_counts_left[setid] > 0:
            subset_heap[setid] = weight
        if verbose:
            print setid, tpwlist[setid], subset_counts[setid], -weight, subsets[setid]
        guess_list.append((setid, subset_counts_left[setid], -weight))
        # adjusting weight
        # for each real password in the subset
        for rpwid in subsets[setid]:
            # adjust its frequencey according to P_n = (K-k)p/(K-pk)
            # multiply by total_freq to get adjust *frequency* (prevent underflow)
            if rpwid == setid:
                adjust_freq[rpwid] = 0.0
            else:
                adjust_freq[rpwid] = adjust_freq[rpwid] * (large_k[rpwid] - little_k[rpwid]) \
                                     * total_freq / (large_k[rpwid] * total_freq - little_k[rpwid] * adjust_freq[rpwid])

            # large K changes to K - 1
            large_k[rpwid] -= 1
            # for each subset containing this password
            # recalculate its weight
            for nsetid in rpw2subset[rpwid]:
                # it should be in the heap
                if nsetid in subset_heap:
                    # calling setweight() for accuracy
                    # could consider calculate difference for efficiency
                    subset_heap[nsetid] = -setweight(nsetid)
    print "Guess complete in {} seconds".format(time.time() - t0)
    subset_heap = None
    adjust_freq = None
    little_k = None
    large_k = None
    subset_counts_left = None
    return guess_list


def naive_greedy_maximum_coverage(q=100):
    """Finds q sets from subsets which are indexed by tpwlist such that

    the total weight of the covered elements is maximized.
    """
    read_required_files()
    guess_list = []
    while len(guess_list) < q:
        m = max((sum(rpwlist[rpwid] for rpwid in subset if rpwid < len(rpwlist)), i) \
                for i, subset in enumerate(subsets))
        for rpwid in subsets[m[1]]:
            rpwlist[rpwid] = 0
        print tpwlist[m[1]], m[0]
        guess_list.append(m)
    return guess_list


def greedy_maximum_coverage_evaluation(guesses, k=5):
    """Finds q sets from subsets, similar to greedy_maximum_coverage,
    difference is that now each rpw accepts only randomly-chosen k typoes
    """
    t0 = time.time()
    read_required_files()
    print "Files loaded in", time.time() - t0, "seconds wall time"

    t0 = time.time()
    # this dict is from subset of guess to the rank of guess
    guess2rank = {}
    for i, [setid, no, weight] in enumerate(guesses):
        guess2rank[(setid, no)] = i
    print "Generated guess ranks in", time.time() - t0, "seconds wall time"

    t0 = time.time()
    # this array stores freq of passwords compromised *at* this number of guess
    success_freq = [0.0 for _ in guesses]

    # iterating through all true passwords, randomly select a neighborhood
    # and check whether a guess hits the selected nh
    for i, freq in enumerate(rpwlist):
        assert i in rpw2subset[i], "{} {}".format(i, rpw2subset[i])
        possibilities = [(setid, no) for setid in rpw2subset[i] for no in range(subset_counts[setid]) if setid != i]
        little_k = min(k, len(possibilities))
        random.shuffle(possibilities)
        possibilities = [(i, 0)] + possibilities[:little_k]
        # for each selected neighbor, check whether it is in attacker's guesses
        m = len(guesses)
        for p in possibilities:
            if p in guess2rank and guess2rank[p] < m:
                m = guess2rank[p]
        if m < len(guesses):
            success_freq[m] += freq
        if (i % 500000 == 0):
            print "Done evalutating {}, cumulatively {} seconds".format(i, time.time() - t0)
    return success_freq


################################################################################
from pwmodel import HistPw
from typofixer.checker import Checker, BUILT_IN_CHECKERS


def test_evaluation():
    t0 = time.time()
    q = 1000000
    n = 10

    for k in [200, 160, 20, 60, 100, 140]:
        t1 = time.time()
        A = greedy_maximum_coverage_random_typos(q, k, verbose=False)
        eva = []
        for i in range(n):
            print("Running {}th evaluation").format(i)
            eva.append(greedy_maximum_coverage_evaluation(A, k))
        cum = [np.cumsum(_) for _ in eva]
        # with timestamp
        with open(resultfile + datetime.datetime.now().strftime("%y%m%d-%H%M%S") + ".json", "w") as f:
            json.dump({"k": k, "q": q, "n": n, "allowed_edits": allowed_edits,
                       "average": list(np.average(eva, axis=0)),
                       "stddev": list(np.std(eva, axis=0)),
                       "cum-average": list(np.average(cum, axis=0)),
                       "cum-stddev": list(np.std(cum, axis=0))}, f, indent=2)
        print("Done k={} in {} seconds").format(k, time.time() - t1)
    print("Full process ended in {} seconds").format(time.time() - t0)


def test_coverage(q=10):
    q = int(q)
    # A = old_greedy_maximum_coverage_random_typos(10, 5)
    # A = greedy_maximum_coverage_heap(1000)
    attacker_pwmodel = HistPw(os.path.expanduser('~/passwords/rockyou-withcount.txt.bz2'))
    # typofixer = BUILT_IN_CHECKERS['ChkBl_keyedit']
    typofixer = BUILT_IN_CHECKERS['ChkBl_Top3']

    A = greedy_maxcoverage_heap(attacker_pwmodel, typofixer, q=q)
    # print '=='*50
    # print A
    # print '-'*80
    with open('coverage.log', 'w') as logf:
        json.dump(A, logf, indent=2)

        # A = greedy_maxcoverage_random_typos(attacker_pwmodel, typofixer, q=20)
        # print '=='*50
        # print A


def success_rate(real_pwm_f):
    pwm = HistPw(real_pwm_f)
    attacker_pwmodel = HistPw(os.path.expanduser('~/passwords/rockyou-withcount.txt.bz2'))
    import itertools
    Q = [10, 100, 1000]
    typofixer = BUILT_IN_CHECKERS['ChkBl_Top3']
    tpw_data = json.load(open('coverage.log'))['guesslist'][:max(Q)]
    tpwlist, tpwp_ = zip(*tpw_data)
    print sum(tpwp_)

    def totprob(l):
        return sum(pwm.prob(pw) for pw in l)

    print "len(tpwlist):", len(tpwlist)
    normal_guesses = [pw for pw, c in attacker_pwmodel.iterpasswords(n=len(tpwlist))]
    print real_pwm_f
    ######################################### Debug ##############################
    assert len(normal_guesses) == len(tpwlist)
    done = set()
    nwp, tpwp = 0, 0
    for i, w in enumerate(normal_guesses):
        tpw = tpwlist[i]
        killing = (typofixer.get_ball(tpw) | set([tpw])) - done
        done |= killing
        weight = totprob(killing)
        nwp += pwm.prob(w)
        tpwp += weight
        if tpwp < nwp:
            print "{!r},{!r},{}<-->{}".format(w, tpw, pwm.prob(w), weight)
            ###########################################################################
    tpwp = pwm.correction(tpwp)
    nwp = pwm.correction(nwp)
    print tpwp, nwp, tpwp - nwp
    for q in Q:
        ball = typofixer.get_ball_union(tpwlist[:q])
        print set(normal_guesses[:q]) - ball
        lambda_q = totprob(normal_guesses[:q])
        lambda_tilde_q = totprob(ball)
        print "{:.3f}, {:.3f}, {:.3f}" \
            .format(lambda_q, lambda_tilde_q, (lambda_tilde_q - lambda_q))


if __name__ == "__main__":
    test_coverage()
