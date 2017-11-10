import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../flange')))

# import flange package module
from flange import flange
from util import iterutils, registry, url_scheme_python as pyurl