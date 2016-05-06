import os
import sys
main_dir = os.path.dirname(__name__)
if main_dir not in sys.path:
    sys.path.insert(0, main_dir)
from typofixer.keyboard import Keyboard, SHIFT_KEY, CAPS_KEY
from typofixer import correctors
from typofixer.checker import Checker, BUILT_IN_CHECKERS
# from .correctors import *
# from .checkers import *
