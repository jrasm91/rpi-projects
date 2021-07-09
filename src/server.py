#!/usr/bin/python3
import asyncio
import json
from utility import Utility, getLogger
import websockets
from database import *
from playhouse.shortcuts import model_to_dict
from scheduler import Scheduler

logger = getLogger(__name__)

class Server():
  def __init__(self):
    self.connections = set()
    self.scheduler = Scheduler()
    self.utility = Utility()

  async def _handle(self, websocket, path):
    self.connections.add(websocket)
    await self._send_data()
    try:
      async for message in websocket:
        data = json.loads(message)
        action = data.get('action')
        valve = data.get('valve')
        id = data.get('id')
        value = data.get('value')

        if action == 'refresh':
          await self._send_data(websocket)
          continue


        logger.info(f'Incoming message: {message}.')

        if id and action == 'cancel_scheduled_item':
          item = WaterHistory.get(id=id)
          if item.state == WaterHistory.PENDING:
            item.state = WaterHistory.CANCELLED
            item.save()

        if id and action == 'adjust_scheduled_duration':
          item = WaterHistory.get(id=id)
          item.water_duration = max(0, item.water_duration + (value or 5))
          item.scheduled_end = item.scheduled_start + timedelta(minutes=item.water_duration)
          item.save()

        if valve and action == 'adjust_zone_override':
          zone = Zone.get(valve=valve)
          zone.schedule_override += value or 1
          zone.save()

        if valve and action == 'schedule_zone':
          zone = Zone.get(valve=valve)
          duration = value or 15
          start_time = self.utility.now()
          end_time = start_time + timedelta(minutes=duration)
          WaterHistory.create(run_type=WaterHistory.MANUAL, valve=zone.valve, name=zone.name, water_duration=duration, water_type=zone.water_type, scheduled_start=start_time, scheduled_end=end_time)

        if valve and action == 'open_valve':
          self.scheduler.turn_on_valve(valve)
          
        if valve and action == 'close_valve':
          self.scheduler.turn_off_valve(valve)
          zone = Zone.get(valve=valve)
          seconds = (zone.last_off - zone.last_on).total_seconds()
          duration = int( seconds/60)
          WaterHistory.create(state= WaterHistory.DONE, valve=zone.valve, name=zone.name, water_duration=duration, water_type=zone.water_type, run_type=WaterHistory.MANUAL, actual_start=zone.last_on, actual_end=zone.last_off)
        
        await self._send_data()
    finally:
      self.connections.remove(websocket)

  async def _send_data(self, connection=None):
    def _as_dict(model, **kwargs):
      if not model:
        return None
      if isinstance(model, list):
        return [model_to_dict(item, **kwargs) for item in model]
      return model_to_dict(model, **kwargs)

    zones = [zone for zone in Zone.select()]
    water_history = [history for history in WaterHistory.select().order_by(WaterHistory.actual_start.desc())]

    await self._notify(json.dumps({ 'zones': _as_dict(zones, extra_attrs=['next_water_date']), 'water_history': _as_dict(water_history), }, default=str), connection)

  async def _notify(self, message, connection):
    connections = self.connections
    if connection:
      connections = [connection]
    if connections:
      await asyncio.wait([connection.send(message) for connection in connections])

  def start(self):
    start_server = websockets.serve(self._handle, 'localhost', 6789)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
  server = Server()
  server.start()
