import Levenshtein as lv
import re
from common import SHIFT_KEY, CAPS_KEY

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


def word_to_key_presses(KB, word):
    """
    Converts a @word into a key press sequence for the keyboard KB.
    >>> KB = Keyboard('US')
    >>> word_to_key_presses(KB, 'Password12!@')
    <s>password12<s>1<s>2
    >>> word_to_key_presses(KB, 'PASSword!@')
    <c>pass</c>word<s>1<s>2
    >>> word_to_key_presses(KB, 'PAasWOrd') # this is not what it should but close!
    <s>p<s>aas<s>w<s>ord
    <c>pa</c>as<c>wo</c>rd
    """
    caps_key = CAPS_KEY
    shift_key = SHIFT_KEY
    assert KEYBOARD_TYPE == 'US', "Not implemented for mobile"
    shift_status = [0 for _ in word]
    new_str = ''
    # Add shift keys
    for i, ch in enumerate(word):
        ch, shift = KB.remove_shift(ch)
        if shift:
            new_str += shift_key + ch
        else:
            new_str += ch

    # finding continuous use of shift and replace that with capslock
    for s in re.findall(r'(({0}[a-z]){{2,}})'.format(shift_key), new_str):
        o_s, _ = s
        n_s = re.sub(r'{0}([a-z])'.format(shift_key), r'\1'.format(caps_key), o_s)
        new_str = re.sub(re.escape(o_s), '{0}{1}{0}'.format(caps_key, n_s), new_str)

    old_str = ''
    new_str = re.sub(r'{0}(.){0}'.format(caps_key),
                     r'{}\1'.format(shift_key),
                     new_str)  # drop <c>a<c> to <s>a
    # new_str = re.sub(r'%s$' % caps_key, '', new_str)   # drop last caps
    # new_str = re.sub(r'([a-z])%s' % caps_key, 
    #                  r'%s%s\1' % (caps_key, shift_key), 
    #                  new_str)
    return new_str

def key_presses_to_word(KB, keyseq):
    """
    Converts a keypress sequence to a word
    """
    caps_key = CAPS_KEY
    shift_key = SHIFT_KEY
    assert KEYBOARD_TYPE == 'US', "Not implemented for mobile"
    capsloc_state = 0
    def isspecialkey(w, key):
        if re.match(r'^{0}.*'.format(key), w):
            return True
        return False
    word = keyseq
    def addshift(m):
        return ''.join(KB.add_shift(c)[0] for c in m.group(1))
    # change all shift keys
    word = re.sub(r'{0}([\w\W])'.format(re.escape(shift_key)), 
                  addshift, word)
    # change all capslocks
    word = re.sub(r'{0}(\w+){0}'.format(re.escape(caps_key)),
                  addshift, word)
    return word



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
        r, c, shift = self.loc(self, char)
        if capslock_state == 1 and char.isalpha():   # caps lock is on
            shift = (shift+1) % 2  # No need to press shift
        return shift, self._keyboard[r*self._num_shift][c]

    def remove_shift(self, char):
        r, c, shift = self.loc(char)
        if shift:
            char = self.loc2char(r*self._num_shift, c)
        return char, shift

    def add_shift(self, char):
        r, c, shift = self.loc(char)
        if not shift:
            char = self.loc2char(r*self._num_shift+1, c)
        return char, shift
        
    def chage_shift(self, word):
        r, c, shift = self.loc(char)
        char = self.loc2char(r*self._num_shift + (shift+1)%self._num_shift, c)
        return char, shift
        
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



import pytest
@pytest.mark.parametrize(('inp', 'res'),
                         [('PAasWOrd', '{c}pa{c}as{c}wo{c}rd'),
                          ('password', 'password'),
                          ('Password', '{s}password'),
                          ('P@ssword12', '{s}p{s}2ssword12'),
                          ('@!asdASDads', '{s}2{s}1asd{c}asd{c}ads'),
                          # There is this small issue, what if there is a shit in the middle of a password
                          ('PASSwoRD',  '{c}pass{c}wo{c}rd{c}')]
)
class TestKeyPresses():
    def test_word_to_key_press(self, inp, res):
        key = {'c': CAPS_KEY,
               's': SHIFT_KEY}
        KB = Keyboard('US')
        assert word_to_key_presses(KB, inp) == res.format(**key)

    def test_key_presses_to_word(self, inp, res):
        key = {'c': CAPS_KEY,
               's': SHIFT_KEY}
        KB = Keyboard('US')
        assert inp == key_presses_to_word(KB, res.format(**key))

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


if __name__ == '__main__':
    kb = Keyboard('US')
    pw1 = 'PASSWORD123|'
    #    pw2 = 'PAasWOrd'
    p1 = word_to_key_presses(kb, pw1)
    pw11 = key_presses_to_word(kb, p1)
    #   p2 = word_to_key_presses(kb, pw2)
    print "{!r} -> {!r} --> {!r}".format(pw1, p1, pw11)
    #    print "{!r} -> {!r}".format(pw2, p2)


    # print lv.distance(str(p1), str(p2))
    # print lv.editops(str(p1), str(p2))
