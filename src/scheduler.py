#!/usr/bin/python3
import sys
import time
from datetime import timedelta
from database import *
from utility import Utility, _str, getLogger

logger = getLogger(__name__)

class GPIODummy():
  OUT = 1
  BOARD = 'dummy_board'

  @staticmethod
  def setmode(mode):
    logger.debug(f'Dummy.setmode({mode})')

  @staticmethod
  def setup(gpio_number, state, initial=0):
    logger.debug(f'Dummy.setup({gpio_number, state, initial})')

  @staticmethod
  def output(gpio_number, value):
    logger.debug(f'Dummy.output({gpio_number},{value})')

  @staticmethod
  def cleanup(gpio_number=None):
    logger.debug('Dummy.cleanup()')

try:
  import RPi.GPIO as GPIO
except (RuntimeError, ModuleNotFoundError):
  logger.warning('Failed in import RPi.GPIO, using GPIODummy')
  GPIO = GPIODummy

class Scheduler():
  def __init__(self, simulation=False):
    self.utility = Utility(simulation)
    self.simulation = simulation
    if simulation:
      logger.warning('Starting scheduler in simulation mode')
      global GPIO
      GPIO = GPIODummy

  def turn_on_valve(self, valve, now=None):
    if not now:
      now = self.utility.now()

    gpio_number = self.utility.get_gpio_number(valve)
    GPIO.setmode(GPIO.BOARD)    
    GPIO.setup(gpio_number, GPIO.OUT, initial=1)
    GPIO.output(gpio_number, 0)
    
    zone = Zone.get(valve=valve)
    if zone:
      zone.is_running = True
      zone.last_on = now
      zone.save()
    if not self.simulation:
      time.sleep(5)

  def turn_off_valve(self, valve, now=None):
    if not now:
      now = self.utility.now()

    gpio_number = self.utility.get_gpio_number(valve)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(gpio_number, GPIO.OUT, initial=0)
    GPIO.output(gpio_number, 1)
    GPIO.cleanup(gpio_number)
    zone = Zone.get(valve=valve)
    if zone:
      zone.is_running = False
      zone.last_off = now
      zone.save()
    if not self.simulation:
      time.sleep(5)

  def schedule(self, now=None, smartSchedule=True):
    if not now:
      now = self.utility.now()
    
    today = now
    
    logger.info(f'Scheduling for {today.date()}')

    first_start_time = today.replace(hour=1,minute=0,second=0,microsecond=0)
    multi_start_times = [
      today.replace(hour=10,minute=0,second=0,microsecond=0),
      today.replace(hour=13,minute=0,second=0,microsecond=0),
      today.replace(hour=16,minute=0,second=0,microsecond=0),
    ]

    zones = self._get_zones_for(today)
    if len(zones) == 0:
      logger.info('  No zones should run.')
      return None

    spray_zones = self._get_spray_zones(zones)
    drip_zones = self._get_drip_zones(zones)
    multi_zones = self._get_multi_zones(zones)

    spray_end =  today.replace(hour=5,minute=0,second=0,microsecond=0)
    spray_delta = timedelta(minutes=sum([zone.water_duration for zone in spray_zones]))
    drip_delta = timedelta(minutes=sum([zone.water_duration for zone in drip_zones]))
    multi_delta = 4 * (timedelta(minutes=sum([zone.water_duration for zone in multi_zones])))
    total_run_time = spray_delta + drip_delta + multi_delta

    if smartSchedule:
      spray_end = self.utility.get_sunrise(today)
      logger.info(f'  Changed Spray End to {spray_end.time()} via Smart Schedule')

    # first watering
    start_time = end_time = max(first_start_time, spray_end - spray_delta)
    start_time, end_time = self._schedule_zones(start_time, end_time, spray_zones + multi_zones + drip_zones, first_start_time)

    # second+ waterings
    for multi_start_time in multi_start_times:
      start_time = end_time = max(multi_start_time, start_time)
      start_time, end_time = self._schedule_zones(start_time, end_time, multi_zones)

    emojis = dict() 
    emojis[Zone.SPRAY] = ':shower:'
    emojis[Zone.DRIP] = ':droplet:'
    emojis[Zone.MULTI] = ':sweat_drops:'

    slack_message = f''':sunrise: Scheduled {len(zones)} Zones'''
    for item in WaterHistory.select().where(WaterHistory.state == WaterHistory.PENDING).order_by(WaterHistory.scheduled_start.asc()):
      emoji = emojis[item.water_type]
      slack_message += f'\n\t- {emoji} {item.name} ({item.valve}) from {_str(item.scheduled_start)} to {_str(item.scheduled_end)} (+{item.water_duration}m)'
    self.utility.send_slack_message(slack_message)
    return start_time

  def run(self, now=None): 
    if not now:
      now = self.utility.now()
    
    active_zone = WaterHistory.select().where(WaterHistory.state == WaterHistory.ACTIVE).first() 
    
    if active_zone: 
      # Still running
      if now < active_zone.actual_start + timedelta(minutes=active_zone.water_duration):
        return False

      # Finished current zone
      active_zone.state = WaterHistory.DONE
      active_zone.actual_end = now
      active_zone.save()
      self.turn_off_valve(active_zone.valve, now)
      self.utility.send_slack_message(f':red_circle: Turned *OFF* {active_zone.name} ({active_zone.valve}) at {_str(now)}')

    pending_zone = WaterHistory.select().where(WaterHistory.state == WaterHistory.PENDING).order_by(WaterHistory.scheduled_start).first() 
    
    # All done
    if not pending_zone:
      now_str = self.utility.now_str(now)
      #self.utility.send_slack_message(f':checkered_flag: Finished at {now_str}')
      return True

    # Start a new zone
    if now > pending_zone.scheduled_start: 
      pending_zone.state = WaterHistory.ACTIVE
      pending_zone.actual_start = now
      pending_zone.save()
      self.utility.send_slack_message(f':large_green_circle: Turned *ON* {pending_zone.name} ({pending_zone.valve}) at {_str(now)}')
      self.turn_on_valve(pending_zone.valve, now)

    return False

  def auto_run(self, start_time, sleep_time=60):
    self.utility.sleep_until(start_time)
    while True:
      if self.simulation:
        done = self.run(now=start_time)
      else:
        done = self.run()
      if done:
        break
      self.utility.sleep(sleep_time)
      start_time += timedelta(seconds=sleep_time)

  def _get_zones_for(self, today):
    return [zone for zone in Zone.select() if zone.is_enabled and zone.should_run_on(today)]

  def _get_spray_zones(self, zones):
    return [zone for zone in zones if zone.is_spray()]

  def _get_drip_zones(self, zones):
    return [zone for zone in zones if zone.is_drip()]

  def _get_multi_zones(self, zones):
    return [zone for zone in zones if zone.is_multi()]

  def _schedule_zones(self, start_time, end_time, zones, not_before=None):
    for zone in zones:
      # logger.info(f'  Processing {zone.label()}: start_time={start_time.time()}, end_time={end_time.time()}, not_before={not_before}')
      if not_before and not_before < start_time - timedelta(minutes=zone.water_duration): 
        start_time = self._schedule_before(zone, start_time)
      else:
        end_time = self._schedule_after(zone, end_time)
    return (start_time, end_time)

  def _schedule_before(self, zone, start_time):
    end_time =  start_time
    start_time = end_time - timedelta(minutes=zone.water_duration)
    logger.info(f'  Added Schedule {_str(start_time)} to {_str(end_time)}: {zone.label()} to START (+{zone.water_duration}m)')
    self._schedule(zone, start_time, end_time)
    return start_time

  def _schedule_after(self, zone, end_time):
    start_time = end_time
    end_time =  start_time + timedelta(minutes=zone.water_duration)
    logger.info(f'  Added Schedule {_str(start_time)} to {_str(end_time)}: {zone.label()} to END (+{zone.water_duration}m)')
    self._schedule(zone, start_time, end_time)
    return end_time

  def _schedule(self, zone, start_time, end_time):
    WaterHistory.create(valve=zone.valve, name=zone.name, water_duration=zone.water_duration, water_type=zone.water_type, scheduled_start=start_time, scheduled_end=end_time)
    zone.last_water_date = end_time.date() 
    zone.schedule_override = 0
    zone.save()

if __name__ == '__main__':
  if len(sys.argv) > 1:
    command = sys.argv[1]
  else:
    comand = 'auto-run'

  scheduler = Scheduler(simulation=False)
  if command == 'schedule':
    scheduler.schedule()
  elif command == 'run':
    scheduler.run()
  elif command == 'autorun':
    scheduler.auto_run()
  else:
    logger.error(f'Invalid Command: {command}. \n\tusage: ./scheduler.py run | schedule | autorun')

# * * * /path/to/file/scheduler.py schedule
# * * * /path/to/file/scheduler.py run
