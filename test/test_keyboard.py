#!/usr/bin/python
import os, sys, json, csv, re
import socket
import random
import pytest
from context import Keyboard, SHIFT_KEY, CAPS_KEY

    
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
    def test_key_prox_chars(self, inp, res):
        kb = Keyboard('US')
        ret = kb.keyboard_prox_chars(inp)
        assert set(ret) == set(res)

    def test_key_prox_keys(self):
        kb = Keyboard('US')
        for inp, res in [('a', 'aqwsxz'),
                         ('t', 'tr456yhgf'),
                         (';', ";lop['/.")]:
            ret = kb.keyboard_prox_key(inp)
            assert set(ret) == set(res)

    def test_keypress_to_w(self):
        for inp, res in [('wor{c}d123', u'worD123'),
                         ('{c}pass{c}wo{c}rd{c}', 'PASSwoRD')]:
            kb = Keyboard('US')
            w = kb.key_presses_to_word(inp.format(s=SHIFT_KEY, c=CAPS_KEY))
            assert w == res


@pytest.mark.parametrize(('inp', 'res'),
                         [('PAasWOrd', u'{s}p{s}aas{s}w{s}ord'),
                          ('password', u'password'),
                          ('Password', u'{s}password'),
                          ('P@ssword12', u'{s}p{s}2ssword12'),
                          ('@!asdASDads', u'{s}2{s}1asd{c}asd{c}ads'),
                          # There is this small issue, what if there is a shit in the middle of a password
                          ('PASSwoRD',  u'{c}pass{c}wo{c}rd{c}')]
)
class TestKeyPresses():
    def test_word_to_key_press(self, inp, res):
        key = {'c': CAPS_KEY,
               's': SHIFT_KEY}
        KB = Keyboard('US')
        t1 = KB.word_to_key_presses(inp)
        t2 = res.format(**key)
        assert t1 == t2, "{!r} <--> {!r}".format(t1, t2)

    def test_key_presses_to_word(self, inp, res):
        key = {'c': CAPS_KEY,
               's': SHIFT_KEY}
        KB = Keyboard('US')
        assert inp == KB.key_presses_to_word(res.format(**key))

    def test_other_key_presses_to_word(self, inp, res):
        key = {'c': CAPS_KEY,
               's': SHIFT_KEY}
        KB = Keyboard('US')
        kw = KB.key_presses_to_word('{c}asdf{s}1{c}sdf'.format(**key))
        assert 'ASDFasdf' == KB.key_presses_to_word('{c}asdf{s}a{c}sdf'.format(**key))
        print kw
        assert 'ASDF!sdf' == KB.key_presses_to_word('{c}asdf{s}1{c}sdf'.format(**key))
                                       
    def test_key_press(self, inp, res):
        inp_res_map = [(('|'), (1,13,1))
                       ]
        kb = Keyboard('US')
        for q, r in inp_res_map:
            assert kb.loc(*q) == r




# class TestPWLogging:
#     def test_logging(self):
#         HOST, PORT = "localhost", 9999
#         sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         sock.settimeout(1)  # wait only 1 msec
#         DB= [('rahulc', 'qwerty'), ('user1', 'Password'), ('user2', 'password'),
#             ('abcd@xyz.com', 'abcd123')]
#         #  clear log file
#         for uid, pw in DB: 
#             data = {'uid': uid, 'password': pw, 'useragent': "User-Agent", 'isValid': -1}
#             try:
#                 sock.sendto(json.dumps(data) + "\n", (HOST, PORT)) 
#                 recvd = sock.recv(1024)
#             except socket.timeout:
#                 print "Cannot reach the logging server."
#             #  TODO - write this test


