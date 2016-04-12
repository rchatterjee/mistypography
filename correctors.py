__author__ ='Rahul Chatterjee'
"""
LICENSED to modify and distribute any or all parts of the code.
"""

import os, sys, json, csv
import string, re
import unittest, string
from collections import defaultdict
from common import ALLOWED_EDITS
from keyboard import Keyboard

ALLOWED_CHARACTERS = string.letters + string.digits + '`~!@#$%^&*()_+-=,/?.<>;\':"[]{}\\| \t'
NOTSHIFT_2_SHIFT_MAP = dict(zip('`1234567890-=[]\;\',./',
                                '~!@#$%^&*()_+{}|:"<>?'))
SHIFT_2_NOTSHIFT_MAP = dict(zip('~!@#$%^&*()_+{}|:"<>?',
                                '`1234567890-=[]\;\',./'))
SHIFT_SWITCH_MAP = dict(zip('`1234567890-=[]\;\',./~!@#$%^&*()_+{}|:"<>?',
                            '~!@#$%^&*()_+{}|:"<>?`1234567890-=[]\;\',./'))
SYMDIGIT_re = re.compile(r'(?P<last>(%s)+)$' % '|'.join(map(re.escape, SHIFT_SWITCH_MAP.keys())))

KB = Keyboard('US')

"""This is the set of correctors we consider.  A corrector is a
function which tries to fix a typo in a password but applying some
generic modifications. By generic I meant the modification is not
dependent on the specific password it is modifying.  

Every corrector comes with an inverse function which defines the
mistyped password or passwords that this corrector can fix. e.g.,
if "adding a 1 to the end" be a corrector, then removing the last
one will be the typo version of that corrector.

In the EDITS_NAME_FUNC_MAP, the first entry is the corrector
function while the second entry is the typo (inverse of the
corrector) of that function.


"""


shift_swtich_regex = re.compile(r'(?P<last>(%s)+)$' % '|'.join(map(re.escape, SHIFT_SWITCH_MAP.keys())))

def same(word):
    return word

def _switch_case_letter(ch):
    """switch the case of the character"""
    return ch.swapcase()

def switch_case_all(word):
    """Switch the case of all the letters if the word contains at
    least one letter. This simulates the effect of caps-lock error.

    """
    w =  word.swapcase()
    if w != word:
        return w

def switch_case_first(word):
    """Shift error. Switches the case of first character."""
    i = 0
    while i<len(word) and not word[i].isalpha():
        i+=1
    if i<len(word):
        return word[:i] + _switch_case_letter(word[i]) + word[i+1:]

def upper_n_capital(word):
    """Switch between Upper case and title case. The user switched
    between shift key and caps lock key.

    """
    if word.isupper():
        return word.title()
    elif word.istitle():
        return word.upper()

def upper_2_capital(word):
    """Pressed caps-lock instead of shift"""
    if word.isupper():
        return word.title()


def capital_2_upper(word):
    """Pressed caps-lock instead of shift key"""
    if word.istitle():
        return word.upper()

def add1_last(word):
    return word + '1'

def remove1_last(word):
    if word[-1] == '1':
        return word[:-1] 

def remove_last_digit(word):
    if word[-1].isdigit():
        return word[:-1]

def remove_last_symbol(word):
    if not word[-1].isalnum():
        return word[:-1]

def remove_last_letter(word):
    if word[-1].isalpha():
        return word[:-1]

def remove_first_char(word):
    return word[1:]

def remove_last_char(word):
    return word[:-1]

def add_last_digit(word):
    return [word+c for c in string.digits]

def add_last_symbol(word):
    return [word+c for c in string.punctuation]

def add_last_letter(word):
    return [word+c for c in string.ascii_letters]

def add_first_char(word):
    return [c+word for c in ALLOWED_CHARACTERS]

def add_last_char(word):
    return [word+c for c in ALLOWED_CHARACTERS]

def _change_shift_status_last(word, shift_map):
    shift_regex = re.compile(r'(?P<last>(%s)+)$' % '|'.join(map(re.escape, shift_map.keys())))
    def _replace_(mo):
        text = mo.string[mo.start():mo.end()]
        return ''.join(shift_map.get(ch, ch) for ch in text)

    return shift_regex.sub(_replace_, word)

def switch_shift_lastn(word):
    """
    change the shift state of last digit+symbols string
    e.g., "asdf123" -> "asdf!@#"
    """
    done = 0;
    new_str = list(word)
    for i in xrange(len(word),0,-1):
        if not done:
            try:
                new_str[i-1] = SHIFT_SWITCH_MAP[word[i-1]]
            except:
                break
    w = ''.join(new_str)
    if w != word:
        return w
    # return _change_shift_status_last(word, SHIFT_SWITCH_MAP)

def n2s_last(word):
    if word[-1].isdigit():
        return switch_shift_last1(word)

def s2n_last(word):
    if not word[-1].isalnum():
        return switch_shift_last1(word)

def add_shift_lastn(word):
    """
    if the last digit+symbol string is not shifted, shift it
    """
    return _change_shift_status_last(word, NOTSHIFT_2_SHIFT_MAP)

def remove_shift_lastn(word):
    """
    if the last digit+symbol string is not shifted, shift it
    """
    return _change_shift_status_last(word, NOTSHIFT_2_SHIFT_MAP)

def switch_shift_last1(word):
    ch = word[-1]
    return word[:-1] + SHIFT_SWITCH_MAP.get(ch, ch)

def add_shift_last1(word):
    ch = word[-1]
    return word[:-1] + NOTSHIFT_2_SHIFT_MAP.get(ch, ch)

def remove_shift_last1(word):
    """Convert the last shift character (if any) to unshifted version.
    e.g., abcd123! --> abcd1231
    or, iop{} --> iop[]"""
    ch = word[-1]
    return word[:-1] + SHIFT_2_NOTSHIFT_MAP.get(ch, ch)


################################################################################
########################### Edit based correctors ##############################
################################################################################
def insert_one_char(word):
    """insert 1 character in the word at some location. Returns a list of
    modifications of @word
    """
    return [word[:i]+c+word[i:] 
            for i in xrange(len(word))
            for c in ALLOWED_CHARACTERS]

def delete_one_char(word):
    """
    deletes one of the characters in the word.
    """
    return [word[:i]+word[i+1:] 
            for i in xrange(len(word))]

def replace_one_char(word):
    """Replace each character in the word with a character from the
    allowed character list (one at a time).
    """
    return [word[:i]+c+word[i+1:] 
            for i in xrange(len(word))
            for c in ALLOWED_CHARACTERS
            if word[i] != c]

def replace_keyboard_prox_chars(word):
    """Replace each of the character in the word with a character that is
    closed by in standard US keyboard.
    """
    return [word[:i]+c+word[i+1:]
            for i in xrange(len(word))
            for c in KB.keyboard_close_chars(word[i])]

def edit_on_keypress_seq(word):
    """Update the keypress sequence to obtain possible corrections. This will enable fewer number of possible corrections, and might lead to better correctors.
    1.  First convert the string @word into key-press sequence. 
    2.  Then try to insert/delete/replace characters and then move the key press sequence back to the original string. 
    """

    pass


def check_invalid_edits(edits):
    """Checks if any of the corrector in the edits array is invalid or not defined""" 
    assert all(e in ALLOWED_EDITS for e in edits), "Some edit is not in the list: {}".format(edits)


# This is a funcname to func map, first entry in the value part is transform, 
# second one is the typos that it can fix.
EDITS_NAME_FUNC_MAP = {
    "same": [same, same],
    "swc-all": [switch_case_all, switch_case_all],  # insertion of caps-lock
    "swc-first": [switch_case_first, switch_case_first],  # deletion of shift
    "add1-last": [add1_last, remove1_last],  # missed last 1
    "rm-lastl": [remove_last_letter, add_last_letter],  # addion of a char
    "rm-lastd": [remove_last_digit, add_last_digit],  # addion of a digit
    "rm-lasts": [remove_last_symbol, add_last_symbol],  # addtion of a symbol
    "rm-firstc": [remove_first_char, add_first_char],  # addition of a char at the beginning
    "rm-lastc": [remove_last_char, add_last_char],  # addition of a char at the end
    "sws-last1": [switch_shift_last1, switch_shift_last1],  # deletion of last shift
    "sws-lastn": [switch_shift_lastn, switch_shift_lastn],  # deletion of last shift
    "upncap": [upper_n_capital, upper_n_capital],  # typed caps instead of shift switch
    "up2cap": [upper_2_capital, upper_2_capital],  # typed caps instead of shift switch
    "cap2up": [capital_2_upper, upper_2_capital],  # typed shift instead of caps switch
    "n2s-last": [n2s_last, s2n_last] # convert last number to symbol
}


def modify(word, apply_edits=["All"], typo=False):
    """
    ---This function is no where used--- (TODO: remove)
    If typo is True, then apply the reverse edits, i.e., EDIT_TO_TYPOS
    returns:   {tpw: set of edits that will convert word to tpw}
    in case typo is true, then it will be {tpw: set of words that can be edited back to word}
    """
    if 'All' in apply_edits:
        apply_edits = ALLOWED_EDITS
    mutated_words = defaultdict(set)
    istypo = 1 if typo else 0
    # return the ball that will be accepted due to allowing these edits
    allowed_edits = set(EDITS_NAME_FUNC_MAP[a][istypo] for a in apply_edits)
    for e in allowed_edits:
        tpw = e(word)
        if isinstance(tpw, basestring):
            mutated_words[tpw].add(e)
        else:
            for t in tpw:
                mutated_words[t].add(e)
    return mutated_words



def fast_modify(word, apply_edits=["All"], typo=False, pw_filter=None):
    """
    If typo is True, then apply the inverse of the corrector.
    @word is the typed/entered password 
    @E is an instance of the Correctors
    returns:   if typo==True:
                  set of mistyped passwords that can can be corrected by the given edits
               elif typo==False:
                  set of corrected passwords after applying the corrector functions.

    """
    # if not pw_filter(word):
    #     print "I am modifying a password ('{}') which does not pass its own filter ({})"\
    #     .format(word, pw_filter)
    if not pw_filter:
        pw_filter = lambda x: len(x)>=6

    if 'All' in apply_edits:
        apply_edits = ALLOWED_EDITS
    mutated_words = set()
    istypo = 1 if typo else 0
    # if istypo --- returns the ball that will be accepted due to allowing these edits
    # else --- return the candidate real passwords after apllying the edits.
    for a in apply_edits:
        e = EDITS_NAME_FUNC_MAP[a][istypo]
        tpw = e(word)
        if not tpw:
            # print "Tpw='{}' is None for rpw='{}' "\
            #     "a={} and e={}".format(tpw, word, a, str(e))
            continue
        if isinstance(tpw, basestring):
            tpw = [tpw]
        elif not isinstance(tpw, list):
            print "WTF!! tpw ('{!r}') is of type = {}".format(tpw, type(tpw))
            raise ValueError
        mutated_words |= set(filter(pw_filter, tpw))
    return mutated_words


