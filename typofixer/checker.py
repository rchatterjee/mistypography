__author__ ='Rahul Chatterjee'

import os, sys, json, csv
import string, re
import unittest, string
from collections import defaultdict
from correctors import fast_modify, EDITS_NAME_FUNC_MAP
from pwmodel import HistModel, NGramPw
import heapq
from common import (PW_FILTER, DATA_DIR_PATH, 
                    get_most_val_under_prob, TYPO_FIX_PROB,
                    top2correctors, top3correctors, top5correctors)


class Checker(object):
    """This is the Checker class which takes a @set_of_edits, and a
    @policy (discussed bellow), and computes the ball accordingly.
    Note, the identity edit, that is f(pw) = pw, is always part of the 
    @set_of_edits.
    
    policy1: ChkAll, Checks everything after applying edits 
    policy2: ChkBl, Checks everything but that are in Black list 
    policy3: ChkBlspcl, Checks everything but at most one from the Black listed ones
    policy4: Don't allow typo correction on a tpw (entered password) if the
             weight of the ball is higher than rpw_q (q-th most probable password)
    policy5: ChkAOp, Approximate optimal checker, optimally choose the set of password that
             maximizes the utility keeping the total ball weight under Pr(rpw_q)

    The utility of the edits are hardcoded in common.py
    """
    transform_list = []
    transform_list_prob = {}

    #BLACK_LIST = set(x.strip() for x in open(os.path.join(DATA_DIR_PATH, "banned_list_ry1k.txt")))
    BLACK_LIST = set(x.strip() for x in open(os.path.join(DATA_DIR_PATH, "banned_list_twt.txt")))
    #PWMODEL = PWModel(fname='rockyou1M.json.gz')
    # PWMODEL = HistModel(pwfilename='rockyou')
    PWMODEL = NGramPw(pwfilename='/home/rahul/passwords/rockyou-withcount.txt.bz2', n=4)
    def __init__(self, _transform_list, policy_num=1):
        self.transform_list = _transform_list
        if 'same' not in self.transform_list:
            self.transform_list = ['same'] + self.transform_list
        self.policy_num = policy_num
        self.check = eval("self.policy%d" % policy_num)
        self.pwmodel = self.PWMODEL

        q = 1000  # Fix the q
        self._q = q
        # if self.pwmodel:
        #     self.rpw_q = self.pwmodel.qth_pw(q)[1]
        self.rpw_q = -1.0
        self.setup_typo_probs()

    def setup_typo_probs(self):
        tmp_d = {t: TYPO_FIX_PROB[t] for t in self.transform_list}
        total = float(sum(tmp_d.values()))
        self.transform_list_prob = {t: tmp_d[t]/total
                                       for t in self.transform_list}

    def get_ball(self, tpw):
        return self.check(tpw)

    def get_ball_union(self, tpwlist):
        B = set()
        for tpw in tpwlist:
            B |= self.get_ball(tpw)
        return B

    def get_nh(self, rpw):
        return fast_modify(rpw, self.transform_list,
                                      typo=True, pw_filter=PW_FILTER)
        

    def set_approx_pwmodel(self, q):
        """Approx pw model is we divide the pw dist into 3 steps, first high
        probable zone, then mid prob zone and finally low probablity
        zone.  For each zone there is a defacto probability is set,
        and any pw falling in that zone receives that prob
        """
        pass

    def set_pwmodel(self, pwm):
        self.pwmodel = pwm

    def __str__(self):
        tl1, tl2 = self.transform_list[0], self.transform_list[-1]
        tlstr = '[' + '...'.join([str(tl1), str(tl2)]) + ']'
        return 'Checker: transforms=({}) {} (policy={}) (pwmodel={})'\
            .format(len(self.transform_list), tlstr, self.policy_num, self.pwmodel)

    def policy1(self, tpw, rpw=None):
        """This policy is just breat the ball around tpw using given the
        transforms and checks whether or not rpw in that ball, also called ChkAll
        """
        B = fast_modify(tpw, apply_edits=self.transform_list)
        if rpw:
            return rpw in B
        else: 
            return B
    
    def policy2(self, tpw, rpw=None):
        """
        Dont allow any password within the blacklisted set of passwords, a.k.a, ChkBl
        """
        black_list_filter = lambda x: (len(x)>=6) and (x not in Checker.BLACK_LIST)
        B = fast_modify(tpw, apply_edits=self.transform_list, pw_filter=black_list_filter)
        B.add(tpw)
        if rpw:
            return rpw in B
        else:
            return B

    def policy3(self, tpw, rpw=None):
        """
        Allow at most one password from the black list. (Not used in the paper)
        """
        black_list = []
        B = []
        for ename in self.transform_list:
            transform, typo = EDITS_NAME_FUNC_MAP[ename]
            rrpw = transform(tpw)
            if not rrpw or len(rrpw)<6: continue
            if isinstance(rrpw, basestring):
                rrpw = [rrpw]
            for t in rrpw:
                if t in Checker.BLACK_LIST:
                    black_list.append(t)
                else:
                    B.append(t)
        if len(black_list)>0:
            B.append(black_list[0])
        B = set(B)
        if rpw:
            return rpw in B
        else:
            return B

    def policy4(self, tpw, rpw=None):
        """
        Don't correct a tpw if the size of the ball is bigger than
        rpw_q, requires exact pwmodel, (Not used in the paper)
        """
        if rpw and tpw==rpw:
            return True
        B = fast_modify(tpw, apply_edits=self.transform_list)
        B.add(tpw)
        ballmass = sum(self.pwmodel.get(tpw) for tpw in B)
        if ballmass > self.rpw_q:   # Sorry no typo correction 
            # print "Sorry no typo corr for: {} -> {}".format(tpw, B)
            B = set([tpw])
        if rpw:
            return rpw in B
        else:
            return B

    def topq_sorted_by_pwmodel(self, tpw, rpw=None):
        """
        applies keypress eidts, sorts the ball by pwmodel, and outputs top q
        """
        q = 5
        return heapq.nlargest(q, EDITS_NAME_FUNC_MAP['keypress-edit'][0](tpw),
                              key=lambda rpw: self.pwmodel.prob(rpw))


    def policy5(self, tpw, rpw=None):
        """
        Same as policy 4, but approximate info about pwmodel, ChkAOp
        """
        black_list = []
        A = defaultdict(int)
        for ename in self.transform_list:
            transform, typo = EDITS_NAME_FUNC_MAP[ename]
            rrpw = transform(tpw)
            if not rrpw or len(rrpw)<6: continue
            w = self.pwmodel.get(rrpw)*self.transform_list_prob.get(ename, 0.0)
            A[rrpw] += w
        B = set()
        B.add(tpw)
        if tpw in A:
            del A[tpw]

        B |= set(get_most_val_under_prob(A, self.pwmodel,
                                         self.rpw_q - self.pwmodel.get(tpw)))
        if rpw:
            return rpw in B
        else:
            return B

################################################################################
# Different preimplemented checkers
################################################################################ 
BUILT_IN_CHECKERS = {
    # ChkAll checkers with all three corrector sets
    "ChkAllTop2": Checker(top2correctors, 1),
    "ChkAllTop3": Checker(top3correctors, 1),
    "ChkAllTop5": Checker(top5correctors, 1),

    # ChkBl checkers with all three corrector sets
    "ChkBlTop2": Checker(top2correctors, 2),
    "ChkBlTop3": Checker(top3correctors, 2),
    "ChkBlTop5": Checker(top5correctors, 2),

    # ChkAOp checkers with all three corrector sets
    "ChkAOpTop2": Checker(top2correctors, 5),
    "ChkAOpTop3": Checker(top3correctors, 5),
    "ChkAOpTop5": Checker(top5correctors, 5),

    # ChkAll with singleton corrector sets
    "ChkAll_swcall": Checker(['swc-all'], 1),
    "ChkAll_swcfirst": Checker(['swc-first'], 1),
    "ChkAll_rmlastc": Checker(['rm-lastc'], 1),
    "ChkAll_rmfirstc": Checker(['rm-firstc'], 1),
    "ChkAll_swslast": Checker(['sws-last1'], 1)
}

if __name__ == '__main__':
    chk = Checker(top2correctors, 1)
    print "{} -> {}".format(sys.argv[1], 
                                   chk.topq_sorted_by_pwmodel(sys.argv[1]))
