#!/usr/bin/python3
import sys
import logging
from utility import resolveFile
from logging.handlers import TimedRotatingFileHandler

_logger = None

def getLogger(name=''):
  global _logger
  if not _logger:
    logPath = resolveFile('sprinklers.log')
    logging.root.handlers = []
    logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s [%(levelname)s] %(message)s",
      handlers=[
          TimedRotatingFileHandler(logPath, when='midnight', interval=1, backupCount=6),
          logging.StreamHandler(sys.stdout)
      ]
    )
    _logger = logging
  return _logger.getLogger(name)
