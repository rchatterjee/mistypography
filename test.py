#!/usr/bin/python
import os, sys, json, csv, re
import socket
import random
import pytest

class TestEdits:
    def test_Checker(self):
        from checker import Checker
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


    def test_builtin_checkers(self):
        from checker import BUILT_IN_CHECKERS
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


class TestPWLogging:
    def test_logging(self):
        HOST, PORT = "localhost", 9999
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)  # wait only 1 msec
        DB= [('rahulc', 'qwerty'), ('user1', 'Password'), ('user2', 'password'),
            ('abcd@xyz.com', 'abcd123')]
        #  clear log file
        for uid, pw in DB: 
            data = {'uid': uid, 'password': pw, 'useragent': "User-Agent", 'isValid': -1}
            try:
                sock.sendto(json.dumps(data) + "\n", (HOST, PORT)) 
                recvd = sock.recv(1024)
            except socket.timeout:
                print "Cannot reach the logging server."
            #  TODO - write this test


import correctors
@pytest.mark.parametrize('w', ['word1', 'Rauhl', 'Nothing'])
class TestCorrectors(object):
    def test_delete_one_char(self, w):
        assert len(set(correctors.delete_one_char(w))) == len(w)

    def test_insert_one_char(self, w):
        for tw in correctors.insert_one_char(w):
            assert w in correctors.delete_one_char(tw)

