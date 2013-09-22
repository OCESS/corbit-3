__version__ = '3.0.0'

from entity import Entity
from scipy import array
import json
from unum.units import *
import sys, pygame
from pygame.locals import *
from socket import *
import pickle


HOST = 'localhost'                 # Symbolic name meaning all available interfaces
PORT = 31415              # Arbitrary non-privileged port
sock = socket(AF_INET, SOCK_STREAM)


print("Corbit " + __version__)


entities = []

#load the default JSON file, and construct all included
config = json.loads(open("res/OCESS.json").read())
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


sock.bind((HOST, PORT))
sock.listen(1)

conn, addr = sock.accept()
print('Connected by', addr)

while True:
    data = conn.recv(1024)
    if not data: break
    
    sunb = pickle.dumps(entities[0])
    sunn = pickle.loads(sunb)
    
    conn.sendall(sunb)
conn.close()
