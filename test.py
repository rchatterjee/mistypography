#!/usr/bin/python
import os, sys, json, csv, re
import socket
import random
import pytest
from keyboard import Keyboard, SHIFT_KEY, CAPS_KEY

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

class TestKeyPresses():
    @pytest.mark.parametrize(('inp', 'res'),
                             [('PAasWOrd', '{c}pa{c}as{c}wo{c}rd'),
                              ('password', 'password'),
                              ('Password', '{s}password'),
                              ('P@ssword12', '{s}p{s}2ssword12'),
                              ('@!asdASDads', '{s}2{s}1asd{c}asd{c}ads'),
                              # There is this small issue, what if there is a shit in the middle of a password
                              ('PASSwoRD',  '{c}pass{c}wo{c}rd{c}')]
    )
    def test_word_to_key_press(self, inp, res):
        key = {'c': CAPS_KEY,
               's': SHIFT_KEY}
        KB = Keyboard('US')
        assert KB.word_to_key_presses(inp) == res.format(**key)

    @pytest.mark.parametrize(('inp', 'res'),
                             [('PAasWOrd', '{c}pa{c}as{c}wo{c}rd'),
                              ('password', 'password'),
                              ('Password', '{s}password'),
                              ('P@ssword12', '{s}p{s}2ssword12'),
                              ('@!asdASDads', '{s}2{s}1asd{c}asd{c}ads'),
                              # There is this small issue, what if there is a shit in the middle of a password
                              ('PASSwoRD',  '{c}pass{c}wo{c}rd{c}')]
    )
    def test_key_presses_to_word(self, inp, res):
        key = {'c': CAPS_KEY,
               's': SHIFT_KEY}
        KB = Keyboard('US')
        assert inp == KB.key_presses_to_word(res.format(**key))

    def test_other_key_presses_to_word(self):
        key = {'c': CAPS_KEY,
               's': SHIFT_KEY}
        KB = Keyboard('US')
        kw = KB.key_presses_to_word('{c}asdf{s}1{c}sdf'.format(**key))
        assert 'ASDFAsdf' == KB.key_presses_to_word('{c}asdf{s}a{c}sdf'.format(**key))
        print kw
        assert 'ASDF!sdf' == KB.key_presses_to_word('{c}asdf{s}1{c}sdf'.format(**key))
                                       
    def test_key_press(self):
        inp_res_map = [(('|'), (1,13,1))
                       ]
        kb = Keyboard('US')
        for q, r in inp_res_map:
            assert kb.loc(*q) == r
    
class TestKeyboard():
    def test_loc(self):
        inp_res_map = [(('t'), (1,5,0)),
                      (('T'), (1,5,1)),
                      (('a'), (2,1,0)),
                      (('('), (0,9,1)),
                      (('M'), (3,7,1))]
        kb = Keyboard('US')
        for q, r in inp_res_map:
            assert kb.loc(*q) == r

    def test_keyboard_dist(self):
        inp_res_map = [(('t', 't'), (0)),
                       (('t', 'T'), (0.8)),
                       (('a', 'S'), (1.8)),
                       (('a', 'w'), (2)),
                       (('w', '$'), (3.8)),
                       (('<', '>'), (1))
                   ]
        kb = Keyboard('US')
        for q, r in inp_res_map:
            assert kb.keyboard_dist(*q) == r


    @pytest.mark.parametrize(('inp', 'res'), [('a', 'AQWSXZqwsxz'),
                                               ('g', 'GRTYHNBVFrtyhnbvf'),
                                               ('r', 'R#$%TGFDE345tgfde')])
    def test_key_close_chars(self, inp, res):
        kb = Keyboard('US')
        ret = kb.keyboard_close_chars(inp)
        assert set(ret) == set(res)

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
    def test_length_delete_one_char(self, w):
        assert len(set(correctors.delete_one_char(w))) == len(w) or \
            len(set(w))<len(w)

    def test_insert_one_char(self, w):
        for tw in correctors.insert_one_char(w):
            assert w in correctors.delete_one_char(tw)

    def test_key_presses_edit(self, w):
        w = 'password'
        ball = set(correctors.edit_on_keypress_seq(w))
        for i in xrange(20):
            r = random.randint(1, len(w)-1)
            l = len(w)#r + random.randint(1, len(w)-r)
            w = w[:r] + w[r:l].upper() + w[l:]
            assert w in ball
