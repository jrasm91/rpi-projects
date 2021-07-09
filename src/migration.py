#!/usr/bin/python3
import peewee
from database import *
from playhouse.migrate import *

def main():
  migrator = SqliteMigrator(db)
  migrate(
      migrator.add_column('zone', 'schedule_override', Zone.schedule_override),
  )

if __name__ == '__main__':
  main()
