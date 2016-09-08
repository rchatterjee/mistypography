import Levenshtein as lv
import re
from .common import SHIFT_KEY, CAPS_KEY, ALLOWED_KEYS
import ipdb

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
        
    def change_shift(self, char):
        if not char.isalpha(): return char
        r, c, shift = self.loc(char)
        nshift = (shift+1) % self._num_shift
        char = self.loc2char(r*self._num_shift + nshift, c)
        return char, shift
        
    def loc(self, char):
        """
        return location of a key, the row, column and shift on
        or off.
        """
        KM, num_shift = self._keyboard, self._num_shift
        if not self._loc_map:
            self._loc_map = {ch: (i//num_shift, j, i % num_shift)
                             for i, r in enumerate(KM)
                             for j, ch in enumerate(r)}
            self._loc_map[' '] = (3, 0, 0)
        if char not in self._loc_map:
            raise Exception( "Could not find location of: <{}>".format(repr(char)))
            
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
        print(key_o, oi, oj, oshift, '>>><<<<',
              ti, tj, tshift, key_t)

        return abs(oi-ti) + abs(oj-tj) + \
            self._shift_discount*abs(oshift-tshift)

    def is_keyboard_prox(self, s, d):
        """
        Checks whether two words are close in terms of keys
        :param s: character
        :param d: character
        :return: weight
        """
        d = self.keyboard_dist(s, d)
        return d < 1.0
    
    def keyboard_prox_chars(self, char):
        """Returns the closed by characters of character @c in standard US
        Keyboard.
        :param c: character
        :return: a list of characters
        """
        i, j, shift = self.loc(char)
        ret = []
        KM, num_shift = self._keyboard, self._num_shift
        for sh in range(num_shift):
            for r in range(i-1, i+2):
                for c in range(j-1, j+2):
                    ch = self.loc2char(r*num_shift+sh, c)
                    if ch and ch != ' ' and ch != char:
                        ret.append(ch)
        return ret

    def keyboard_prox_key(self, char):
        """Returns the closed by characters of character @c in standard US
        Keyboard.
        :param c: character
        :return: a list of keys
        """
        if char == SHIFT_KEY: 
            return CAPS_KEY
        elif char == CAPS_KEY:
            return SHIFT_KEY

        i, j, shift = self.loc(char)
        ret = []
        KM, num_shift = self._keyboard, self._num_shift
        for r in range(i-1, i+2):
            for c in range(j-1, j+2):
                ch = self.loc2char(r*num_shift, c)
                if ch and ch != ' ':
                    ret.append(ch)
        return ''.join(ret)

    def word_to_key_presses(self, word):
        """
        Converts a @word into a key press sequence for the keyboard KB.
        >>> KB = Keyboard('US')
        >>> KB.word_to_keyseq('Password12!@')
        <s>password12<s>1<s>2
        >>> KB.word_to_keyseq('PASSword!@')
        <c>pass</c>word<s>1<s>2
        >>> KB.word_to_keyseq('PAasWOrd') # this is not what it should but close!
        <s>p<s>aas<s>w<s>ord
        <c>pa</c>as<c>wo</c>rd
        """
        if isinstance(word, str):
            word.encode('ascii', 'ignore')
        caps_key = CAPS_KEY
        shift_key = SHIFT_KEY
        assert KEYBOARD_TYPE == 'US', "Not implemented for mobile"
        new_str = ''
        # Add shift keys
        for i, ch in enumerate(word):
            try:
                ch, shift = self.remove_shift(ch)
            except Exception as e:
                print (e,  repr(word))
                raise e
            if shift:
                new_str += shift_key + ch
            else:
                new_str += ch

        # finding continuous use of shift and replace that with capslock
        for s in re.findall(r'(({0}[a-z]){{3,}})'.format(shift_key), new_str):
            o_s, _ = s
            n_s = re.sub(r'{0}([a-z])'.format(shift_key), r'\1'.format(caps_key), o_s)
            new_str = re.sub(re.escape(o_s), '{0}{1}{0}'.format(caps_key, n_s), new_str)

        
        # drop <c>a<c> to <s>a
        new_str = re.sub(r'{0}(.){0}'.format(re.escape(caps_key)),
                         r'{}\1'.format(shift_key),
                         new_str)  

        # move the last capslock to the end
        # PASSOWRD123 -> <c>password<c>123 -> <c>password123<c>
        new_str = re.sub(r'{0}([^a-z]+)$'.format(re.escape(caps_key)),
                         r'\1{0}'.format(caps_key),
                         new_str)  
        
        # convert last sequence of shift into caps sequence
        # passwoRD123 -> passwo<s>r<s>d123 -> passwo<c>rd123<c>
        # r'(<s>[a-z][^a-z]*)+{2,}$ ->
        m = re.match(r'.*?(?P<endshifts>({0}[a-z][^a-z{0}]*){{2,}}({0}.[^a-z]*)*)$'.format(shift_key), new_str)
        if m:
            s = m.group('endshifts')
            ns = caps_key + re.sub(r'{0}([a-z])'.format(shift_key), r'\1', s) + caps_key
            # print m.groups(), ns, s
            new_str = new_str.replace(s, ns)

        return new_str

    def print_key_press(self, keyseq):
        """print the @key_str as the human readable format.
        """
        return keyseq.replace(SHIFT_KEY, '<s>').replace(CAPS_KEY, '<c>')

    def part_key_press_string(self, keyseq, shift=False, caps=False):
        """
        returns the word for a part of the keyseq, and returns (word, shift, caps)
        """
        assert KEYBOARD_TYPE == 'US', "Not implemented for mobile"
        ret = ''
        i = 0
        while i<len(keyseq):
            a = keyseq[i]
            if keyseq[i] == CAPS_KEY:
                caps = caps^True
            elif keyseq[i] == SHIFT_KEY:
                shift = True
            else:
                if a.isalpha():
                    a = self.add_shift(a)[0] if caps^shift else a
                else:
                    a = self.add_shift(a)[0] if shift else a
                shift = False
                ret += a
            i += 1
        return ret, shift, caps
        
    def apply_shift_caps(self, c, shift, caps):
        if c.isalpha():
            return self.add_shift(c)[0] if shift^caps else c
        else:
            return self.add_shift(c)[0] if shift else c

    def sub_word_table(self, keyseq):
        """n = len(word), returns an 2-D array,
        TT = shift-caps, both true, TF, FT and FF are similar
        i/j  0     1      2     3       4 
        0  [:0] [0:]FF [:0]FT  [:0]TF  [:0]TT
        1  [:1] [1:]FF [:1]FT  [:1]TF  [:1]TT
        .
        .
        n  [:n] [n:]FF [:n]FT  [:n]TF  [:n]TT

        """
        n = len(keyseq)
        A = [[(), (), (), (), ()] for i in range(n+1)]
        A[0] = [('', False, False),
                self.part_key_press_string(keyseq, False, False),# FF
                self.part_key_press_string(keyseq, False, True), # FT
                self.part_key_press_string(keyseq, True, False), # TF
                self.part_key_press_string(keyseq, True, True)]  # TT
        A[n] = [A[0][1], ('', False, False), ('', False, True), ('', True, False), ('', True, True)]
        for j in range(1, n):
            last_row = A[j-1]
            row = A[j]
            c = keyseq[j-1]
            nc = keyseq[j] if j<n else ''
            shifted_nc = self.add_shift(nc)[0] if nc not in [SHIFT_KEY, CAPS_KEY] else ''
            if c==SHIFT_KEY:
                row[0] = (last_row[0][0], True, last_row[0][2]) # case 0: only pre
                row[1] = (nc + last_row[1][0][1:], last_row[1][1], last_row[1][2]) # shift-caps = FF, remove the shift from next char
                row[2] = ((shifted_nc if nc.isalpha() else nc) + last_row[2][0][1:], last_row[2][1], last_row[2][2]) # shift-caps = FT
                row[3] = last_row[3] # shift-caps = TF
                row[4] = last_row[4] # shift-caps = TT
            elif c == CAPS_KEY:
                row[0] = (last_row[0][0], last_row[0][1], last_row[0][2]^True) # case 0: only pre
                row[1] = (last_row[1][0].swapcase(), last_row[1][1], last_row[1][2]^True) # shift-caps = FF
                row[2] = last_row[1]  # shift-caps = FT
                row[3] = (last_row[3][0].swapcase(), last_row[3][1], last_row[3][2]^True) # shift-caps = TF
                row[4] = last_row[3] # shift-caps = TT
            else:
                row[0] = (last_row[0][0] + self.apply_shift_caps(c, *last_row[0][1:]), False, last_row[0][2])
                row[1] = (last_row[1][0][1:], last_row[1][1], last_row[1][2]) # shift-caps = FF
                row[2] = (last_row[2][0][1:], last_row[2][1], last_row[2][2]) # shift-caps = FT
                row[3] = (shifted_nc + last_row[3][0][2:] if shifted_nc else last_row[3][0][1:],
                          last_row[3][1], last_row[3][2]) # shift-caps = TF
                row[4] = (nc + last_row[4][0][2:] if nc.isalpha() else
                          shifted_nc + last_row[4][0][2:],
                          last_row[4][1], last_row[4][2]) # shift-caps = TT
        return A

    def key_press_insert_edits(self, keyseq, insert_keys=[], replace_keys=[]):
        """It will insert/replace/delete one key at a time from the
        keyseq. And return a set of words. Which keys to insert is
        specified by the @insert_keys parameter. 
        :param pos: int, position of the edit, pos=0..len(keyseq): insert,delete and replace.
                    if pos=len(keyseq)+1, then only insert
        """
        spcl_keys = SHIFT_KEY+CAPS_KEY
        sub_words = self.sub_word_table(keyseq)
        # print '\n'.join(str(r) for r in sub_words)
        smart = not insert_keys and not replace_keys
        for i,c in enumerate(keyseq):
            if smart:
                if c in spcl_keys: # if replacing a caps or shift, replace with everything
                    replace_keys = ALLOWED_KEYS
                else: # else use only the closed by keys or spcl keys
                    replace_keys = self.keyboard_prox_key(c) + spcl_keys
                # Use all keys if the inserting at the edge, else
                # replace with closed by keys of the preivious key
                keys_i = set(replace_keys + \
                             (self.keyboard_prox_key(keyseq[i-1]) \
                              if i>0 else ALLOWED_KEYS))

            pre_w, shift, caps  = sub_words[i][0]
            t = 2*shift + caps + 1
            # print "Going to Insert at {}".format(i) 
            # insert
            for k in insert_keys:
                if k==SHIFT_KEY:
                    yield pre_w + sub_words[i][3+caps][0]
                elif k==CAPS_KEY:
                    yield pre_w + sub_words[i][2*shift+2][0]
                else:
                    yield pre_w + self.apply_shift_caps(k, shift, caps) + sub_words[i][caps+1][0]
            # if i==0:
            #     yield self.apply_shift_caps(k, True, caps) + sub_words[i][1][0]
            # print "Going to delete"
            # delete
            if c==SHIFT_KEY:
                yield pre_w + sub_words[i+1][1+caps][0]
            elif c==CAPS_KEY:
                yield pre_w + sub_words[i+1][2*shift+2][0]
            else:
                yield pre_w + sub_words[i+1][t][0]
            # replace
            # print "Going to Replace @ {}".format(i)
            for k in replace_keys:
                if k==SHIFT_KEY:
                    yield pre_w + sub_words[i+1][3+caps][0]
                elif k==CAPS_KEY:
                    yield pre_w + sub_words[i+1][2*shift + 2 - caps][0] # If already caps, then this will cancel that
                else:
                    yield pre_w + self.apply_shift_caps(k, shift, caps) + sub_words[i+1][1+caps][0]

        # For inserting at the end
        pre_w, shift, caps = sub_words[-1][0]
        if smart:
            insert_keys = ALLOWED_KEYS
        for k in insert_keys:
            if k not in spcl_keys:
                yield pre_w + self.apply_shift_caps(k, shift, caps)

    def keyseq_to_word(self, keyseq):
        """This is the same function as word_to_keyseq, just trying to
        make it more efficient. Remeber the capslock and convert the
        shift.

        """
        return self.part_key_press_string(keyseq)[0]


    def keyseq_to_word_slow(self, keyseq):
        """
        Converts a keyseq sequence to a word
        """
        caps_key = CAPS_KEY
        shift_key = SHIFT_KEY
        assert KEYBOARD_TYPE == 'US', "Not implemented for mobile"

        word = keyseq
        def caps_change(m):
            return ''.join(self.change_shift(c)[0] if c !=shift_key else shift_key
                           for c in m.group(1))

        def shift_change(m):
            return ''.join(self.add_shift(c)[0] if c != caps_key else caps_key
                           for c in m.group(1))

        word = re.sub(r'({0})+'.format(shift_key), r'\1', word)
        word = re.sub(r'({0})+'.format(caps_key), r'\1', word)
        # only swap <s><c> to <c><s>
        word = re.sub(r'({1}{0})+([a-zA-Z])'.format(caps_key, shift_key),
                      r'{0}{1}\2'.format(caps_key, shift_key), 
                      word)

        if word.count(caps_key)%2 == 1:
            word += caps_key

        try:
            # apply all shift keys
            word = re.sub(r'{0}+([\w\W])'.format(shift_key),
                          shift_change, word)
            # apply all capslocks
            word = re.sub(r'{0}(.*?){0}'.format(caps_key),
                          caps_change, word)
        except Exception as e:
            print(">>>> I could not figure this out: {!r}, stuck at {!r}\n{}"\
                   .format(keyseq, word, e))
            raise e
        word = word.strip(shift_key).strip(caps_key)
        return word



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



if __name__ == '__main__':
    kb = Keyboard('US')
    ks = '{s}wo{c}rd123{s}{c}'.format(c=CAPS_KEY, s=SHIFT_KEY)
    # p1 = kb.word_to_keyseq(pw1)
    # print "{!r} -> {!r} --> {!r}".format(pw1, p1, pw11)
    print("{!r} -> {!r}".format(ks, kb.keyseq_to_word(ks)))
