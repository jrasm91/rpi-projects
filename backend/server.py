#!/usr/bin/python3
import socketio
import eventlet
import json

from database import *
from playhouse.shortcuts import model_to_dict, dict_to_model

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)

def _as_dict(model, **kwargs):
  if not model:
    return None
  if isinstance(model, list):
    return [model_to_dict(item, **kwargs) for item in model]
  return model_to_dict(model, **kwargs)

def _as_json(data):
  return json.dumps(data, default=str)

def _get_zones():
  return _as_dict([zone for zone in Zone.select()])

@sio.event
def connect(sid, environ):
  print('connect ', sid)
  zones = _get_zones()
  sio.emit('zones', data=_as_json(zones), to=sid)

@sio.event
def disconnect(sid):
  print('disconnect ', sid)

@sio.event
def my_event(sid, data):
  pass

@sio.on('my custom event')
def another_event(sid, data):
  pass


if __name__ == '__main__':
  eventlet.wsgi.server(eventlet.listen(('', 3001)), app)
