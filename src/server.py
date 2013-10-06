__version__ = '3.0.0'

from entity import Entity
from scipy import array
import json
from unum.units import m,s,kg,rad
from socket import *
import pickle
import atexit
import threading
import time
import sys
import Pyro4

print("Corbit SERVER " + __version__)

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.clear()
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")

HOST = "localhost"  # IP address to bind to
PORT = 31415        # Arbitrary port I picked

class Telemetry:
    "Class that transfers data between server and other programs"
    def entities(self):
        return entities

telem = Telemetry()
entities = []

#load the default JSON file, and construct all included
config = json.loads(open("../res/OCESS.json").read())
data = config["entities"][0]

for entity in config["entities"]:
    displacement = m/1 * array(entity["displacement"])
    #print(displacement)
    velocity = m/s * array(entity["velocity"])
    #print(velocity)
    acceleration = m/s/s * array(entity["acceleration"])
    #print(acceleration)
    
    name = entity["name"]
    #print(name)
    mass = kg/1 * entity["mass"]
    #print(mass)
    radius = m * entity["radius"]
    #print(radius)
    
    angular_displacement = rad/1 * entity["angular_displacement"]
    #print(angular_displacement)
    angular_velocity = rad/s * entity["angular_velocity"]
    #print(angular_velocity)
    angular_acceleration = rad/s/s * entity["angular_acceleration"]
    #print(angular_acceleration)
    
    entities.append(Entity(displacement, velocity, acceleration,
                 name, mass, radius,
                 angular_displacement, angular_velocity, angular_acceleration))


daemon = Pyro4.Daemon("localhost", 31415)
daemon.register(telem, "telem")


def exit_handler():
    daemon.close()

atexit.register(exit_handler)

def simulate_tick():
    for entity in telem.entities:
        entity.move(s/tps)

def receive_input():
    None

daemon.requestLoop()

"""
while True:
    print("loop")
    simulate_tick()
    receive_input()
    time.sleep(1/tps)
"""

print("okay")

exit_handler()