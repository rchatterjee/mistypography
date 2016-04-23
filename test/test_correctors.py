import pytest
from context import correctors
from context import Checker, BUILT_IN_CHECKERS
import random

@pytest.mark.parametrize('w', ['word123', 'Rahul123', 'Nothing', 
                               'Password12', 'P@ssword12!'])
class TestCorrectors(object):
    def test_length_delete_one_char(self, w):
        assert len(set(correctors.delete_one_char(w))) == len(w) or \
            len(set(w))<len(w)

    def test_insert_one_char(self, w):
        for tw in correctors.insert_one_char(w):
            assert w in correctors.delete_one_char(tw)

    # def test_key_presses_edit(self, w):
    #     ball = set(correctors.edit_on_keypress_seq_corr(w))
    #     for i in xrange(20):
    #         r = random.randint(1, len(w)-1)
    #         l = len(w)#r + random.randint(1, len(w)-r)
    #         w = w[:r] + w[r:l].upper() + w[l:]
    #         assert w in ball

    def test_nh_ball(self, w):
        C = Checker(['keypress-edit'], policy_num=1)
        nh = C.get_nh(w)
        fail = 0
        for tw in nh:
            if random.randint(0,20)==0:
                continue
            print "{!r} in ball({!r})".format(w, tw)
            if w not in C.get_ball(tw):
                fail += 1
        assert fail<len(nh)/10

    # def test_balls(self, w):
    #     C = Checker(['keypress-edit'], policy_num=1)
    #     ball = C.get_ball(w)
    #     for rw in ball:
    #         print "{!r} in nh({!r})".format(w, rw)
    #         assert w in C.get_nh(rw)

    # def test_nh(self, w):
    #     C = Checker(['keypress-edit'], policy_num=1)
    #     nh = C.get_nh(w)
    #     for tw in nh:
    #         assert w in C.get_ball(tw)


class TestEdits:
    @pytest.mark.skip(reason="The pwmodel does not support password sorting")
    def test_Checker(self):
        # policy1 - accepts all
        aserver = Checker([], 1)
        for pw in ['flower', 'password', '1234567', ]:
            assert pw in aserver.BLACK_LIST
        top5 = ['same', 'swc-all', 'swc-first','rm-lastc', 'rm-firstc', 'n2s-last']
        top3 = ['same', 'swc-all', 'swc-first','rm-lastc']

        policy = 1
        aserver = Checker(top5, policy)
        for pw,res in (zip(['password1', '1234567', '#df46gd!@`'], 
                           [set(['password1', 'PASSWORD1', 'Password1','password', 'assword1', 'password!']), 
                            set(['1234567', '123456', '123456&', '234567']),
                        set(['#df46gd!@', '#df46gd!@`', 'df46gd!@`', '#Df46gd!@`', '#DF46GD!@`'])])):
            assert res==aserver.check(pw)
            for rpw in res:
                assert pw in aserver.get_nh(rpw)

        policy = 2
        aserver = Checker(['same', 'swc-all', 'swc-first', 'rm-lastd'], policy)
        for pw,res in (zip(['password', '1234567', '#df46gd!@`'], 
                       [set(['password']), 
                        set(['1234567']),
                        set(['#DF46GD!@`', '#df46gd!@`', '#Df46gd!@`'])])):
            assert res==aserver.check(pw)

        policy = 4
        aserver = Checker(['same', 'swc-all', 'swc-first', 'rm-lastd'], policy)
        for pw,res in (zip(['password', '1234567', '#df46gd!@`'], 
                       [set(['password']), 
                        set(['1234567']),
                        set(['#DF46GD!@`', '#df46gd!@`', '#Df46gd!@`'])])):
            assert res==aserver.check(pw)

        policy = 5
        aserver = Checker(['same', 'swc-all', 'swc-first', 'rm-lastd'], policy)
        for pw,res in (zip(['password', '1234567', '#df46gd!@`', 'RAULARTURO'], 
                       [set(['password']), 
                        set(['1234567']),
                        set(['#df46gd!@`', '#DF46GD!@`', '#Df46gd!@`']), 
                        set(['raularturo', 'rAULARTURO', 'RAULARTURO'])])):
            assert res==aserver.check(pw)


    @pytest.mark.skip(reason="The pwmodel does not support password sorting")
    def test_builtin_checkers(self):
        checker = BUILT_IN_CHECKERS['ChkAllTop5']
        for pw,res in (zip(['password1', '1234567', '#df46gd!@`'], 
                           [set(['password1', 'PASSWORD1', 'Password1','password', 'assword1', 'password!']), 
                            set(['1234567', '123456', '123456&', '234567']),
                        set(['#df46gd!@', '#df46gd!@`', 'df46gd!@`', '#Df46gd!@`', '#DF46GD!@`', '#df46gd!@~'])])):
            assert res==checker.get_ball(pw)
            for rpw in res:
                assert pw in checker.get_nh(rpw)

        checker = BUILT_IN_CHECKERS['ChkBlTop3']
        for pw,res in (zip(['password', '1234567', '#df46gd!@`'], 
                       [set(['password', 'passwor']), 
                        set(['1234567']),
                        set(['#DF46GD!@`', '#df46gd!@`', '#Df46gd!@`', '#df46gd!@'])])):
            assert res==checker.check(pw)

        checker = BUILT_IN_CHECKERS['ChkAOpTop3']        
        for pw,res in (zip(['password', '1234567', '#df46gd!@`', 'RAULARTURO'], 
                       [set(['password']), 
                        set(['1234567']),
                        set(['#df46gd!@`', '#DF46GD!@`', '#Df46gd!@`', '#df46gd!@']), 
                        set(['raularturo', 'rAULARTURO', 'RAULARTURO', 'RAULARTUR'])])):
            assert res==checker.get_ball(pw)

        # for k, v in BUILT_IN_CHECKERS.items():
        #     for pw in ['password', '123456']:
        #         print k, v.get_ball(pw)

