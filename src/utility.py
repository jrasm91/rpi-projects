#!/usr/bin/python3
import math
import os
import sys
import time
import logging
from datetime import datetime, date, timedelta 
from configparser import ConfigParser
from logging.handlers import TimedRotatingFileHandler

_logger = None
_config = None

def getLogger(name=''):
  global _logger
  if not _logger:
    logPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sprinklers.log')
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

def getConfig():
  global _config
  if not _config:
    configPath = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sprinklers.conf'))
    print(configPath)
    config = ConfigParser()
    config.read(configPath)
    _config = config
  return _config

logger = getLogger(__name__)
config = getConfig()

latitude = 33.330046
longitude = -111.880642

def _str(now):
  return now.strftime('%H:%M:%S')

class Utility():
  def __init__(self, simulation=False):
    self.simulation = simulation

  def get_gpio_number(self, valve):
    valve = str(valve)

    if not config.has_option('valves', valve):
      raise f'Invalid Value ({valve}). No associated GPIO pin.'
    return int(config.getint('valves', valve))

  def now(self):
    return datetime.now().replace(microsecond=0)

  def now_str(self, now=None):
    if not now:
      now = datetime.now()

    if self.simulation:
      return now.strftime('%Y/%m/%d %H:%M:%S')
    else:
      return datetime.now().strftime('%H:%M:%S')

  def send_slack_message(self, message):
    logger.info('Slack Message: ' + message)
    if self.simulation:
      return

    try:
      from slack_sdk.webhook import WebhookClient
      url = config.get('params', 'slack_url')
      webhook = WebhookClient(url)
      webhook.send(text=message)
    except Exception as e:
      logger.warning('Unable to send slack notification:', str(e))


  def sleep(self, seconds):
    if self.simulation:
      return
    time.sleep(seconds)

  def sleep_until(self, start_time, now=None):
    if not now:
      now = datetime.now()

    if self.simulation or now > start_time:
      return

    delta = (start_time - now).total_seconds()
    logger.info(f'sleep_until({start_time}, {now}) => seconds={delta}')
    time.sleep(delta)

  def get_sunrise(self, date=date.today()):
    return self._get_sun_time(date, True)

  def get_sunset(self, date=date.today()):
    return self._get_sun_time(date, False)

  def _get_sun_time(self, today=date.today(), isRiseTime=True, zenith=90.8):
    if isinstance(today, datetime):
      today = today.date()

    # 1. first calculate the day of the year
    N = today.timetuple().tm_yday

    # 2. convert the longitude to hour value and calculate an approximate time
    lngHour = longitude / 15

    if isRiseTime:
      t = N + ((6 - lngHour) / 24)
    else: #sunset'
      t = N + ((18 - lngHour) / 24)

    # 3. calculate the Sun's mean anomaly
    M = (0.9856 * t) - 3.289

    # 4. calculate the Sun's true longitude
    L = M + (1.916 * math.sin(math.radians(M))) + (0.020 * math.sin(math.radians(2 * M))) + 282.634
    L = self._force_range(L, 360 ) 

    # 5a. calculate the Sun's right ascension
    RA = math.degrees(math.atan(0.91764 * math.tan(math.radians(L))))
    RA = self._force_range(RA, 360) 

    # 5b. right ascension value needs to be in the same quadrant as L
    Lquadrant  = (math.floor( L/90)) * 90
    RAquadrant = (math.floor(RA/90)) * 90
    RA = RA + (Lquadrant - RAquadrant)

    # 5c. right ascension value needs to be converted into hours
    RA = RA / 15

    # 6. calculate the Sun's declination
    sinDec = 0.39782 * math.sin(math.radians(L))
    cosDec = math.cos(math.asin(sinDec))

    # 7a. calculate the Sun's local hour angle
    cosH = (math.cos(math.radians(zenith)) - (sinDec * math.sin(math.radians(latitude)))) / (cosDec * math.cos(math.radians(latitude)))
    if cosH > 1 or cosH < -1:
      return None

    # 7b. finish calculating H and convert into hours
    H = math.degrees(math.acos(cosH))
    if isRiseTime:
      H = 360 - math.degrees(math.acos(cosH))
    H = H / 15

    #8. calculate local mean time of rising/setting
    T = H + RA - (0.06571 * t) - 6.622

    #9. adjust back partial hour
    T = T - (lngHour - int(lngHour))
    T = self._force_range(T, 24)

    # Return
    result = datetime.combine(today, datetime.min.time()) + timedelta(hours=T)
    return datetime(year=today.year, month=today.month, day=today.day, hour=result.hour, minute=result.minute, second=0, microsecond=0)


  def _force_range(self, v, max):
    # force v to be >= 0 and < max
    if v < 0:
      return v + max
    elif v >= max:
      return v - max
    return v

if __name__ == '__main__':
  utility = Utility()
  print(utility.get_gpio_number(1))
