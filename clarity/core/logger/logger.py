import logging
import logging.config

import yaml


logging_configurations = yaml.safe_load(open('clarity/logging.cfg', 'r'))
logging.config.dictConfig(logging_configurations)
logger = logging.getLogger('base')
