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


HOST = "localhost"  # IP address to bind to
PORT = 31415        # Arbitrary port I picked

entities = []

class Server:
    "Class for storing server's data, shared by Pyro"
    def entities(self):
        return entities

server = Server()


print("Corbit " + __version__)

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
    print(name)
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

daemon = Pyro4.Daemon(HOST, PORT)
uri = daemon.register(server, "server")
print("uri =", uri)


daemon.requestLoop()


def exit_handler():
    daemon.close()

atexit.register(exit_handler())

def simulate_tick():
    for entity in server.entities:
        entity.move(s/tps)

def receive_input():
    None

"""
while True:
    print("loop")
    simulate_tick()
    receive_input()
    time.sleep(1/tps)
"""

print("okay")

exit_handler()