__version__ = "3.0.0"

from entity import Entity
from scipy import array, linalg
import json
from unum.units import N,m,s,kg,rad
import atexit, threading, time, itertools, math
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

def angle(A, B):
    return math.atan2((B.displacement[1] - A.displacement[1]).asNumber(),
                      (B.displacement[0] - A.displacement[0]).asNumber())
    
def gravitational_force(A, B):
    unit_distance = array([math.cos(angle(A,B)), math.sin(angle(A,B))])
    return G * A.mass * B.mass / distance(A,B)**2 * unit_distance

class Telemetry:
    "Class that transfers data between server and other programs"
    def entities(self):
        return entities
    
    def save(self, filename):
        with open(filename, "w") as outfile:
            for entity in entities:
                json.dump(entity.dict_repr(), outfile,
                          indent=4, sort_keys=True, separators=(",", ": "))
        

telem = Telemetry()
entities = []

#load the default JSON file, and construct all included
with open("../res/OCESS.json", "r") as infile:
    datafile = json.load(infile)
data = datafile["entities"]

for entity in data:
    
    name = entity["name"]
    #print(name)
    color = entity["color"]
    #print(color)
    mass = kg * entity["mass"]
    #print(mass)
    radius = m * entity["radius"]
    #print(radius)
    
    displacement = m * array(entity["displacement"])
    #print(displacement)
    velocity = m/s * array(entity["velocity"])
    #print(velocity)
    acceleration = m/s/s * array(entity["acceleration"])
    #print(acceleration)
    
    angular_displacement = rad * entity["angular_displacement"]
    #print(angular_displacement)
    angular_velocity = rad/s * entity["angular_velocity"]
    #print(angular_velocity)
    angular_acceleration = rad/s/s * entity["angular_acceleration"]
    #print(angular_acceleration)
    
    entities.append(Entity(name, color, mass, radius,
                 displacement, velocity, acceleration,
                 angular_displacement, angular_velocity, angular_acceleration))


telem.save("../res/quicksave.json")

def simulate_tick():
    with entities_lock:
        
        for entity in entities:
            entity.move(s/tps)
        
        for A, B in itertools.combinations(entities, 2):
            gravity = gravitational_force(A, B)
            theta = angle(A, B)
            A.accelerate(gravity, theta)
            B.accelerate(-gravity, theta)


daemon = Pyro4.Daemon("localhost", 31415)
daemon.register(telem, "telem")

def exit_handler():
    daemon.close()

atexit.register(exit_handler)

server_thread = threading.Thread(target = daemon.requestLoop)
server_thread.start()


while True:
    simulate_tick()
    time.sleep(1/tps)


print("okay")

exit_handler()
