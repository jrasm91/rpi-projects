from os import path
from configparser import ConfigParser
from utility import resolveFile
from logger import getLogger

logger = getLogger(__name__)

_config = None

def getConfig():
  global _config
  if not _config:
    configPath = resolveFile('sprinklers.conf')
    config = ConfigParser()
    try:
      config.read(configPath)
    except:
      print(f'Unable to read {configPath}')
    _config = config
  return _config

def getParam(name, default=None):
  return getConfig().get('params', 'db_name', fallback=default)

def getDatabaseName():
  dbName = resolveFile(getParam('db_name', 'sprinklers.db'))
  logger.info(f'Reading database from {dbName}')
  return dbName
