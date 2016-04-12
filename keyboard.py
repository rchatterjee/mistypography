import Levenshtein as lv
import re
from common_func import SHIFT_KEY, CAPS_KEY

KEYBOARD_TYPE = 'US'
layout_matrix = {
    "US": ([
        "`1234567890-=",
        "~!@#$%^&*()_+",
        " qwertyuiop[]\\",
        " QWERTYUIOP{}|",
        " asdfghjkl;'\n",
        " ASDFGHJKL:\"\n",
        " zxcvbnm,./",
        " ZXCVBNM<>?",
        "         ",
        "         "
    ], 2),
    "MOBILE_ANDROID": ([
        "qwertyuiop",
        "QWERTYUIOP",
        "1234567890",
        "~`|......",
        "asdfghjkl",
        "ASDFGHJKL",
        "@#$%&-+()",
        "....^.={}",
        "zxcvbnm",
        "ZXCVBNM",
        "*\"':;!?",
        "\....[]",
        "/      .",
        ",_    /.",
        ",<    >.",
        ",<    >."], 4)
}


class KeyPresses(object):
    _keypress_list = []
    _keypress_str = ''
    _KB = None

    def __init__(self, KB, str):
        self._KB = KB
        self._str = str
        self._keypress_str = self._set_key_presses(str)
        self._keypress_list = list(self._keypress_str)

    def key_presses(self):
        return self._keypress_list

    def key_press_string(self):
        return ''.join(self._keypress_list)

    def _set_key_presses(self, word):
        caps_key = CAPS_KEY
        shift_key = SHIFT_KEY
        assert KEYBOARD_TYPE == 'US', "Not implemented for mobile"
        shift_status = [0 for _ in word]
        new_str = ''
        for i, ch in enumerate(word):
            r, c, shift = self._KB.loc(ch)
            rk = self._KB.loc2char(r*self._KB.num_shift(), c)
            if ch.isalpha() and shift:
                new_str += caps_key + rk + caps_key
            elif shift:
                new_str += shift_key + rk
            else:
                new_str += rk

        old_str = ''
        while (not old_str) and old_str != new_str:
            old_str = new_str

            new_str = re.sub(r'%s([0-9]+)' % caps_key, r'\1%s' % caps_key, new_str)
            # drop <c>-<s>-. --> <s>-.-<c>
            new_str = re.sub('%s(%s.)' % (caps_key, shift_key), r'\1%s' % caps_key, new_str)
            new_str = re.sub(r'{0}{0}'.format(caps_key), '', new_str)  # drop continuous caps locks
            if not new_str:
                break
        new_str = re.sub(r'{0}(.){0}'.format(caps_key), r'{}\1'.format(shift_key),
                         new_str)  # drop <c>a<c> to <s>a
        new_str = re.sub(r'%s$' % caps_key, '', new_str)   # drop last caps
        new_str = re.sub(r'([a-z])%s' % caps_key, '%s%s\1' % (caps_key, shift_key), new_str)
        return new_str

    def __len__(self):
        return len(self._keypress_list)

    def __str__(self):
        return self._keypress_str


class Keyboard(object):
    _keyboard_type = 'US'
    # some random parameters, need to learn later
    _shift_discount = 0.8

    def __init__(self, _type, shift_discount=0.8):
        self._keyboard_type = _type
        self._keyboard, self._num_shift = layout_matrix[self._keyboard_type]
        self._shift_discount = shift_discount
        self._loc_map = {}
        assert len(self._keyboard) % self._num_shift==0, "Problem in Keyboard layout. "\
            "Expecting the size of the keyboard ({}) to be multiple of num_shift ({})."\
            .format(len(self._keyboard), self._num_shift)

    def char2key(self, char, capslock_state):
        assert self._keyboard_type == 'US', "Not yet supported non-US keyboards"
        r, c, shift = self.loc(char)
        if capslock_state == 1 and char.isalpha():   # caps lock is on
            shift = (shift+1) % 2  # No need to press shift
        return shift, self._keyboard[r*self._num_shift][c]

    def loc(self, char):
        """
        return location of a key, the row, column and shift on
        or off.
        """
        KM, num_shift = self._keyboard, self._num_shift
        if not self._loc_map:
            for i, r in enumerate(KM):
                for j, ch in enumerate(r):
                    self._loc_map[ch] = (i/num_shift, j, i % num_shift)
        if char not in self._loc_map:
            print "Could not find location of: <{}>".format(repr(char))
        return self._loc_map.get(char, (-1, -1, -1))

    def loc2char(self, r, c):
        """
        Given loc (r,c) returns the actual character
        """
        if r>=0 and r<len(self._keyboard):
            if c>=0 and c<len(self._keyboard[r]):
                return self._keyboard[r][c]
        return ''

    def num_shift(self):
        return self._num_shift

    def keyboard_dist(self, key_o, key_t):
        """
        Returns how close the keys are in keyboard
        key_o = original key
        key_w = typed key
        (Though the output is order agnostic :P)
        """
        oi, oj, oshift = self.loc(key_o)
        ti, tj, tshift = self.loc(key_t)
        print key_o, oi, oj, oshift, '>>><<<<',
        print ti, tj, tshift, key_t

        return abs(oi-ti) + abs(oj-tj) + \
            self._shift_discount*abs(oshift-tshift)

    def is_keyboard_close(self, s, d):
        """
        Checks whether two words are close in terms of keys
        :param s: character
        :param d: character
        :return: weight
        """
        d = self.keyboard_dist(s, d)
        return d < 1.0
    
    def keyboard_close_chars(self, char):
        """Returns the closed by characters of character @c in standard US
        Keyboard.
        :param c: character
        :return: a list of characters
        """
        i, j, shift = self.loc(char)
        ret = []
        KM, num_shift = self._keyboard, self._num_shift
        for sh in xrange(num_shift):
            for r in range(i-1, i+2):
                for c in range(j-1, j+2):
                    ch = self.loc2char(r*num_shift+sh, c)
                    if ch and ch != ' ' and ch != char:
                        ret.append(ch)
        return ret


def find_typo_type(word_o, word_t):
    """
    Find the type of the typo by considering bunch of strategies.
      1. match the original string from the back of the typo string and see if
         final output of the typo was correct or not. This tells that there was
         a typo in the beginning which was fixed later
      2. After 1 we shall get
    :param word_o: original string
    :param word_t: typed string
    :return: What type of typo it is
    """

    pass


class TestKeyPresses():
    def test_key_press(self):
        inp_res_map = [(('|'), (1,13,1))
                       ]
        kb = Keyboard('US')
        for q, r in inp_res_map:
            assert kb.loc(*q) == r

import pytest
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


if __name__ == '__main__':
    kb = Keyboard('US', user_friendly=1)
    pw1 = 'PASSWORD123|'
    pw2 = 'Password!@#\\'
    p1 = KeyPresses(kb, pw1)
    p2 = KeyPresses(kb, pw2)
    print pw1, p1
    print pw2, p2

    print lv.distance(p1, p2)
    print lv.editops(p1, p2)
