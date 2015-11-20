#!/usr/bin/python

"""This file is a smaller version of PWModel, only the functions
required for Dropbox to run the experiment on different checkers we
developed.  It takes a name of the password leak, and creates an
OrderDict of passwords to their probabilities.

Now it uses simple file reading and it is slow to load a large
password leak file.  But this can be made faster if we use specilized
data structures, such as dawg (directed acyclic graph) or prefix-trie.
"""

import sys, os, json
from collections import OrderedDict, defaultdict
import gzip
import heapq
from common import (MIN_LENGHT_PW, MIN_PROB, open_,
                    DATA_DIR_PATH)


class PWModel(object):
    """Takes a file with json serialized OrderedDict of pw->freq map
    in gzip or bz or uncompressed format. The passwords should be listed
    in decreasing order of their prob/freq.

    """
    HARD_LIMIT = int(1e6)
    def __init__(self, fname='rockyou1M.json.gz'):
        self.read_pw_file(fname=fname)

    def read_pw_file(self, fname):
        """The name says it all! Given a file in json format and it
        will create OrderedDict of that file.

        """
        if not os.path.exists(fname):
            fname = os.path.join(DATA_DIR_PATH, fname)
        self.fname = fname
        self.PW2FREQ_map = json.load(open_(fname), object_pairs_hook=OrderedDict)
        self.leakname = fname.split('.', 1)[0]
        self._total_freq = float(sum(self.PW2FREQ_map.values()))

    def sum_top_q(self, q):
        """Total probability of top-q passwords""" 
        return sum(self.PW2FREQ_map.values()[:q])/self._total_freq

    def get(self, pw):
        """Returns the probability of the password."""
        return self.PW2FREQ_map.get(pw, 0.0)/self._total_freq

    def pw2frec(self, pw):
        """Returns the frequency of the password. (This function is hardly used)"""
        return self.PW2FREQ_map.get(pw, 0)

    def total_freq(self):
        """Total frequency of the loaded password list."""
        return self._total_freq

    def qth_pw(self, q):
        """returns the qth most (staring from 1st) probable password
        and its probability
        """
        pw, f = '', 0.0
        if q<=len(self.PW2FREQ_map):
            pw, f = self.PW2FREQ_map.items()[q-1]
            f /= self._total_freq
        return pw, f

    def __len__(self):
        return len(self.PW2FREQ_map)

    def __iter__(self):
        for pw, v in self.PW2FREQ_map.iteritems():
            yield pw, v/self._total_freq
    
    def __bool__(self):
        if self.PW2FREQ_map:
            return True
        else:
            return False

    def __str__(self):
        return "PwModel: {}".format(self.fname)


        
if __name__ == "__main__":
    pass
