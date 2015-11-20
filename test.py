#!/usr/bin/python
import os, sys, json, csv, re
import unittest
from checker import Checker
from pwmodel import PWModel

class TestEdits(unittest.TestCase):
    def test_modify(self):
        return
        import random
        E = Edits()
        all_allowed_edits = E.ALLOWED_EDITS
        for pw in ['password23', 'asdfawer', '#df46gd!@`', 'beyonce45',
                   'azielmtz5', 'sexyme543', 'ABEJA', 'aaa13081956']:
            print "Password: {}".format(pw),
            random.shuffle(all_allowed_edits)
            allowed_edits = all_allowed_edits[:random.randint(0,len(all_allowed_edits))]
            if 'same' not in allowed_edits:
                allowed_edits.append('same')
            typos = E.modify(pw, apply_edits=allowed_edits, typo=True)
            for p in typos:
                #print "TYPED PW: <{}>".format(p)
                self.assertTrue(pw in E.modify(p, allowed_edits), "Failed at: pw={}"\
                                "\tp={}\nallowed_edits={}\n".format(pw, p, allowed_edits))
            print '....passed'

    def test_fast_modify(self):
        return 
        import random
        E = Edits()
        all_allowed_edits = E.ALLOWED_EDITS
        for pw in ['password23', 'asdfawer', '#df46gd!@`']:
            print "Password: {}".format(pw),
            random.shuffle(all_allowed_edits)
            for i in xrange(len(all_allowed_edits)):
                allowed_edits = all_allowed_edits[:i+1]
                if 'same' not in allowed_edits:
                    allowed_edits.append('same')
                typos = E.fast_modify(pw, apply_edits=allowed_edits, typo=True)
                for p in typos:
                    #  print "TYPED PW: <{}>".format(p)
                    self.assertTrue(pw in E.fast_modify(p, allowed_edits),
                                    "Failed at: pw={}\tp={}\nallowed_edits={}\n".format(pw, p, allowed_edits))
            print '....passed'

    def test_Checker(self):
        # policy1 - accepts all
        pwmodel = PWModel(fname='data/rockyou1M.json.gz')
        aserver = Checker([], 1)
        for pw in ['flower', 'password', '1234567', ]:
            self.assertTrue(pw in aserver.BLACK_LIST, "{} should be in BLACK_LIST: {}"\
                            .format(pw, aserver.BLACK_LIST))
        top5 = ['same', 'swc-all', 'swc-first','rm-lastc', 'rm-firstc', 'n2s-last']
        top3 = ['same', 'swc-all', 'swc-first','rm-lastc']

        policy = 1
        aserver = Checker(top5, policy, pwmodel=pwmodel)
        for pw,res in (zip(['password1', '1234567', '#df46gd!@`'], 
                           [set(['password1', 'PASSWORD1', 'Password1','password', 'assword1', 'password!']), 
                            set(['1234567', '123456', '123456&', '234567']),
                        set(['#df46gd!@', '#df46gd!@`', 'df46gd!@`', '#Df46gd!@`', '#DF46GD!@`'])])):
            self.assertTrue(res==aserver.check(pw), "Output of {} for policy={} failed."\
                            "\nExpecting: {},\nGot: {}"\
                            .format(pw, policy, res, aserver.check(pw)))
            for rpw in res:
                self.assertTrue(pw in aserver.get_nh(rpw), "Neighborhood not correct. '{}'"
                                " should be in nh({}) = {}"\
                                .format(pw, rpw, aserver.get_nh(rpw)))

        policy = 2
        aserver = Checker(['same', 'swc-all', 'swc-first', 'rm-lastd'], policy)
        for pw,res in (zip(['password', '1234567', '#df46gd!@`'], 
                       [set(['password']), 
                        set(['1234567']),
                        set(['#DF46GD!@`', '#df46gd!@`', '#Df46gd!@`'])])):
            self.assertTrue(res==aserver.check(pw), "Output of {} for policy={} failed."\
                            "\nExpecting: {},\nGot: {}"\
                            .format(pw, policy, res, aserver.check(pw)))

        policy = 4
        aserver = Checker(['same', 'swc-all', 'swc-first', 'rm-lastd'], policy, pwmodel=pwmodel)
        for pw,res in (zip(['password', '1234567', '#df46gd!@`'], 
                       [set(['password']), 
                        set(['1234567']),
                        set(['#DF46GD!@`', '#df46gd!@`', '#Df46gd!@`'])])):
            self.assertTrue(res==aserver.check(pw), "Output of {} for policy={} failed."\
                            "\nExpecting: {},\nGot: {}"\
                            .format(pw, policy, res, aserver.check(pw)))
        # print "Policy: {}. Fix: {}".format(policy, aserver.typo_fix_rate())

        policy = 5
        aserver = Checker(['same', 'swc-all', 'swc-first', 'rm-lastd'], policy, pwmodel=pwmodel)
        for pw,res in (zip(['password', '1234567', '#df46gd!@`', 'RAULARTURO'], 
                       [set(['password']), 
                        set(['1234567']),
                        set(['#df46gd!@`', '#Df46gd!@`']), 
                        set(['raularturo', 'RAULARTURO'])])):
            self.assertTrue(res==aserver.check(pw), "Output of {} for policy={} failed."\
                            "\nExpecting: {},\nGot: {}"\
                            .format(pw, policy, res, aserver.check(pw)))
        # print "Policy: {}. Fix: {}".format(policy, aserver.typo_fix_rate())

        

# class TestEvaluate(unittest.TestCase):
#     def test_evaluate_guesses(self):
#         gfname = 'data/Guesses_myspace_1000_PW1e+06_Policy1.txt'
#         return
#         allowed_edits = config.ALLOWED_EDITS
#         policy_num = config.get_policy_from_fname(gfname)
#         guesses_dict = dict(sorted(json.load(open(gfname)).items(),
#                                    key=lambda x: int(x[0].split('_', 1)[0])))
    
#         pwmodel = PWModel(leakname=guesses_dict.values()[0].get('leakname', 'rockyou'),
#                           evaluation_model=False)
#         keys = ['2_swc-all', '3_rm-lasts']
#         inds = [int(x.split('_')[0]) for x in keys]
#         aserver1 = config.Checker(allowed_edits[:inds[0]], policy_num, pwmodel)
#         aserver2 = config.Checker(allowed_edits[:inds[1]], policy_num, pwmodel)
#         print allowed_edits[inds[0]-1], allowed_edits[inds[1]-1]
#         print keys
    
#         l = 1000
#         glist1 = guesses_dict[keys[0]]['Guesses'][:l]
#         glist2 = guesses_dict[keys[1]]['Guesses'][:l]
        
#         c1, c2 = 0, 0
#         for i, t in enumerate(zip(evaluate_guesses(aserver1, glist1),
#                                   evaluate_guesses(aserver2, glist2))):
            
#             c1 += t[0]
#             c2 += t[1]
#             diff = c1 - c2
#             if diff>1e-9:
#                 print i, glist1[i], glist2[i], t, diff
                
                

unittest.main()
                
