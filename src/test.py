#!/usr/bin/python3
from datetime import datetime, date, timedelta
from database import db, Zone, WaterHistory
from scheduler import Scheduler

class Test():
  def create_tables(self):
    tables = [Zone, WaterHistory]
    db.connect()
    db.drop_tables(tables)
    db.create_tables(tables)
    db.close()

  def create_zones_v1(self):
    Zone.create( valve=1, name='Zone 1',                        water_duration=60,  water_type=Zone.SPRAY, jan_f=1,  feb_f=2,  mar_f=3,  apr_f=4,  may_f=5,  jun_f=6,  jul_f=7,  aug_f=8,  sep_f=9,  oct_f=10, nov_f=11, dec_f=12)

  def create_zones_v2(self):
    Zone.create( valve=1, name='Zone 1',                        water_duration=60,  water_type=Zone.SPRAY, jan_f=5,  feb_f=5,  mar_f=5,  apr_f=4,  may_f=3,  jun_f=3,  jul_f=3,  aug_f=3,  sep_f=4,  oct_f=5,  nov_f=6,  dec_f=6)
    Zone.create( valve=2, name='Zone 2',                        water_duration=60,  water_type=Zone.DRIP,  jan_f=7,  feb_f=6,  mar_f=5,  apr_f=5,  may_f=4,  jun_f=4,  jul_f=4,  aug_f=4,  sep_f=5,  oct_f=6,  nov_f=7,  dec_f=8)

  def create_zones_v8(self):
    Zone.create( valve=1, name='Orange Tree',                   water_duration=120, water_type=Zone.DRIP,  jan_f=28, feb_f=28, mar_f=21, apr_f=14, may_f=14, jun_f=10, jul_f=7,  aug_f=7,  sep_f=10, oct_f=14, nov_f=21, dec_f=28)
    Zone.create( valve=2, name='Lawn',                          water_duration=120, water_type=Zone.SPRAY, jan_f=28, feb_f=28, mar_f=14, apr_f=10, may_f=7,  jun_f=2,  jul_f=2,  aug_f=2,  sep_f=3,  oct_f=10, nov_f=21, dec_f=28)
    Zone.create( valve=3, name='Fred',        is_enabled=False, water_duration=11,  water_type=Zone.DRIP,  jan_f=10, feb_f=10, mar_f=10, apr_f=10, may_f=10, jun_f=10, jul_f=10, aug_f=10, sep_f=10, oct_f=10, nov_f=10, dec_f=10)
    Zone.create( valve=4, name='New Veggies', is_enabled=False, water_duration=15,  water_type=Zone.DRIP,  jan_f=5,  feb_f=5,  mar_f=4,  apr_f=3,  may_f=2,  jun_f=1,  jul_f=1,  aug_f=1,  sep_f=1,  oct_f=3,  nov_f=3,  dec_f=3, )
    Zone.create( valve=5, name='Bushes',                        water_duration=60,  water_type=Zone.DRIP,  jan_f=28, feb_f=21, mar_f=14, apr_f=10, may_f=7,  jun_f=5,  jul_f=5,  aug_f=5,  sep_f=7,  oct_f=14, nov_f=21, dec_f=28)
    Zone.create( valve=6, name='Veggies',                       water_duration=15,  water_type=Zone.MULTI,  jan_f=7,  feb_f=7,  mar_f=7,  apr_f=3,  may_f=2,  jun_f=1,  jul_f=1,  aug_f=1,  sep_f=2,  oct_f=3,  nov_f=5,  dec_f=7)  
    Zone.create( valve=7, name='Young Tree', is_enabled=False,  water_duration=60,  water_type=Zone.DRIP,  jan_f=10, feb_f=7,  mar_f=7,  apr_f=5,  may_f=5,  jun_f=3,  jul_f=3,  aug_f=3,  sep_f=5,  oct_f=7,  nov_f=7,  dec_f=10)
    Zone.create( valve=8, name='Sam',        is_enabled=False,  water_duration=5,   water_type=Zone.DRIP,  jan_f=10, feb_f=10, mar_f=10, apr_f=10, may_f=10, jun_f=10, jul_f=10, aug_f=10, sep_f=10, oct_f=10, nov_f=10, dec_f=10)

  def year_simulation(self, start_date, end_date):
    today =  start_date
    scheduler = Scheduler(simulation=True)

    while today < end_date:
      start_time = scheduler.schedule(today)
      if start_time:
        scheduler.auto_run(start_time)    
      today = today.replace(hour=1, minute=1) + timedelta(days=1)

if __name__ == '__main__':
  test = Test()
  test.create_tables()
  #test.create_zones_v1()
  #test.create_zones_v2()
  test.create_zones_v8()

  # test.year_simulation(
  #   datetime.now() - timedelta(days=14),
  #   datetime.now() + timedelta(days=14)
  # )

  test.year_simulation(
    datetime.now().replace(microsecond=0) - timedelta(days=1),
    datetime.now().replace(microsecond=0) + timedelta(days=12)
  )
