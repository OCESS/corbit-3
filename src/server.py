#todo: find out why the client is not seeing the entities gravitate
#might have something to do with Entity.accelerate()?
__version__ = '3.0.0'

from entity import Entity
from scipy import array, linalg
import json
from unum.units import N,m,s,kg,rad
from socket import *
import pickle, atexit, threading, time, sys, itertools, math
import Pyro4

print("Corbit SERVER " + __version__)
tps = 60

entities_lock = threading.Lock()

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.clear()
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")

HOST = "localhost"  # IP address to bind to
PORT = 31415        # Arbitrary port I picked


G = 6.6720E-11 * N*m**2/kg**2


def distance(A, B):
    return m * linalg.norm(A.displacement.asNumber() - B.displacement.asNumber())

def gravitational_force(A, B):
    return (G * A.mass * B.mass) / (distance(A, B) * distance(A, B))

def angle(A, B):
    return math.atan2((B.displacement[1] - A.displacement[1]).asNumber(),
                      (B.displacement[0] - A.displacement[0]).asNumber())

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
    displacement = m * array(entity["displacement"])
    #print(displacement)
    velocity = m/s * array(entity["velocity"])
    #print(velocity)
    acceleration = m/s**2 * array(entity["acceleration"])
    #print(acceleration)
    
    name = entity["name"]
    #print(name)
    mass = kg * entity["mass"]
    #print(mass)
    radius = m * entity["radius"]
    #print(radius)
    
    angular_displacement = rad * entity["angular_displacement"]
    #print(angular_displacement)
    angular_velocity = rad/s * entity["angular_velocity"]
    #print(angular_velocity)
    angular_acceleration = rad/s**2 * entity["angular_acceleration"]
    #print(angular_acceleration)
    
    entities.append(Entity(displacement, velocity, acceleration,
                 name, mass, radius,
                 angular_displacement, angular_velocity, angular_acceleration))


daemon = Pyro4.Daemon("localhost", 31415)
daemon.register(telem, "telem")


def exit_handler():
    daemon.close()

atexit.register(exit_handler)

print(distance(entities[0], entities[1]))

def simulate_tick():
    with entities_lock:
        
        for entity in entities:
            entity.move(s/tps)
        
        for A, B in itertools.combinations(entities, 2):
            gravity = gravitational_force(A, B)
            theta = angle(A, B)
            A.accelerate(gravity, theta)
            B.accelerate(-gravity, theta)
        

"""
    while (itX != entities.end() ) {
        auto itY = itX;
        ++itY;
        while (itY != entities.end() ) {
            // if (calc::distance2 (*itX, *itY) > (itX->radius + itY->radius) * (itX->radius + itY->radius) ) {
            vect grav (cos (calc::theta (*itX, *itY)), sin (calc::theta (*itX, *itY)));
            grav *= calc::gravity (*itX, *itY);
            itX->accelerate ( grav, 0);
            itY->accelerate (-grav, 0);
            // }
            ++itY;
        }
        ++itX;
    }
"""

server_thread = threading.Thread(target = daemon.requestLoop)
server_thread.start()


while True:
    simulate_tick()
    time.sleep(1/tps)


print("okay")

exit_handler()