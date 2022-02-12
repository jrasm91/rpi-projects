from os import path

def resolveFile(name):
  return path.abspath(path.join(path.dirname(path.abspath(__file__)), '..', name))
