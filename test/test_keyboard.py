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


