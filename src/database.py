import peewee 
import os
from datetime import datetime, timedelta 
from utility import config

dbName = 'sprinklers.db'
if config.has_option('params', 'db_name'):
  dbName = config.get('params', 'db_name')

databasePath= os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', dbName))
db = peewee.SqliteDatabase(databasePath)

class BaseModel(peewee.Model):
  class Meta:
    database = db

class Zone(BaseModel):
  SPRAY = 'spray'
  DRIP = 'drip'
  MULTI = 'multi'

  valve = peewee.IntegerField(unique=True, primary_key=True)
  is_running = peewee.BooleanField(default=False)
  last_on = peewee.DateTimeField(null=True)
  last_off = peewee.DateTimeField(null=True)
  is_enabled = peewee.BooleanField(default=True)
  name = peewee.CharField()
  water_duration = peewee.IntegerField(default=10)
  water_type = peewee.TextField(choices=['spray', 'drip', 'multi'], default='drip')
  last_water_date = peewee.DateField(default=datetime(year=2021, month=1, day=1))
  schedule_override = peewee.IntegerField(default=0)

  jan_f = peewee.IntegerField(default=5)
  feb_f = peewee.IntegerField(default=5)
  mar_f = peewee.IntegerField(default=5)
  apr_f = peewee.IntegerField(default=5)
  may_f = peewee.IntegerField(default=5)
  jun_f = peewee.IntegerField(default=5)
  jul_f = peewee.IntegerField(default=5)
  aug_f = peewee.IntegerField(default=5)
  sep_f = peewee.IntegerField(default=5)
  oct_f = peewee.IntegerField(default=5)
  nov_f = peewee.IntegerField(default=5)
  dec_f = peewee.IntegerField(default=5)

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.next_water_date = self.get_next_run_day()

  def label(self):
    return f'{self.name} ({self.valve}) [{self.water_type.upper()}]'  

  def is_spray(self):
    return self.water_type == Zone.SPRAY

  def is_drip(self):
    return self.water_type == Zone.DRIP

  def is_multi(self):
    return self.water_type == Zone.MULTI
  
  def should_run_on(self, today):
    if isinstance(today, datetime):
      today = today.date()
    next_water_date = self.get_next_run_day()
    return next_water_date <= today

  def get_next_run_day(self):
    days = self.get_interval_for(self.last_water_date.month) + self.schedule_override
    return self.last_water_date + timedelta(days=days)

  def get_interval_for(self, month):
    months = [
        self.jan_f, 
        self.feb_f, 
        self.mar_f, 
        self.apr_f, 
        self.may_f, 
        self.jun_f, 
        self.jul_f, 
        self.aug_f, 
        self.sep_f, 
        self.oct_f, 
        self.nov_f, 
        self.dec_f
    ]

    return months[month - 1]

class WaterHistory(BaseModel):
  ACTIVE = 'active'
  DONE = 'done'
  PENDING='pending'
  CANCELLED='cancelled'
  MANUAL='manual'
  AUTOMATIC='automatic'

  state = peewee.TextField(choices=['pending', 'active', 'done', 'cancelled'], default='pending')
  valve = peewee.IntegerField()
  name = peewee.CharField(default='New Zone')
  water_duration = peewee.IntegerField(default=15)
  water_type = peewee.TextField(choices=['spray', 'drip'], default='drip')
  run_type = peewee.TextField(choices=['manual', 'automatic'], default='automatic')
  scheduled_start= peewee.DateTimeField(null=True)
  scheduled_end = peewee.DateTimeField(null=True)
  actual_start= peewee.DateTimeField(null=True)
  actual_end = peewee.DateTimeField(null=True)
