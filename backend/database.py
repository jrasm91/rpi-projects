from peewee import * 
from datetime import datetime

from logger import getLogger
from utility import resolveFile

import os
import config

logger = getLogger(__name__)

db = SqliteDatabase(config.getDatabaseName())

class Zone(Model):
  id          = AutoField()
  name        = TextField(default='New Zone')
  gpio        = TextField()
  enabled     = BooleanField(default=True)
  category    = TextField()

  class Meta:
    db_table='zone'
    database = db

class ZoneSchedule(Model):
  zoneId      = ForeignKeyField(Zone)
  month       = IntegerField(choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
  timesPerDay = IntegerField(default=5)
  duration    = IntegerField(default=15)
  interval    = IntegerField(default=240)
  notBefore   = DateField()
  notAfter    = DateField()
  startTime   = DateField()

  class Meta:
    db_table='zone_schedule'
    database = db

class ZoneRunHistory(Model):
  zoneId         = ForeignKeyField(Zone)
  trigger        = TextField(choices=['manual', 'automatic'])
  startTime      = DateTimeField()
  endTime        = DateTimeField()
  scheduledStart = DateTimeField()
  scheduledEnd   = DateTimeField()

  class Meta:
    db_table='zone_run_history'
    database = db
