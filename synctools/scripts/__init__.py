from scripts import *

import logging
log = logging.getLogger('synctools')
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())
del logging, log