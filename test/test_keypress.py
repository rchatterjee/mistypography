import pytest
from context import Keyboard, SHIFT_KEY, CAPS_KEY

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
