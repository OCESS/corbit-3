__version__ = "3.0.0"

from entity import Entity
from scipy import array, linalg
import json
from unum.units import N,m,s,kg,rad
import atexit
import threading
import time
import itertools
import math
import Pyro4

print("Corbit SERVER " + __version__)
tps = 60

entity_lock = threading.Lock()

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

def save(output_stream):
    json_data = {}
    json_data["entities"] = []
    
    for entity in entities:
        json_data["entities"].append(entity.dict_repr())
    
    json.dump(json_data, output_stream,
              indent=4, sort_keys=False, separators=(",", ": "))

def load(input_stream):
    "Loads a list of entities when provided with a JSON "
    json_root = json.load(input_stream)
    data = json_root["entities"]
    
    json_entities = []
    
    for entity in data:    
        name = entity["name"]
        color = entity["color"]
        mass = kg * entity["mass"]
        radius = m * entity["radius"]
        
        displacement = m * array(entity["displacement"])
        velocity = m/s * array(entity["velocity"])
        acceleration = m/s/s * array(entity["acceleration"])
        
        angular_displacement = rad * entity["angular_displacement"]
        angular_velocity = rad/s * entity["angular_velocity"]
        angular_acceleration = rad/s/s * entity["angular_acceleration"]
        
        json_entities.append(Entity(name, color, mass, radius,
                                    displacement, velocity, acceleration,
                                    angular_displacement, angular_velocity,
                                    angular_acceleration))
    
    global entities
    entities = json_entities


class Telemetry:
    "Class that transfers data between server and other programs"
    
    def entities(self):
        "Wrapper for accessing entities, callable on a client machine"
        return entities
    
    def save(self, filepath):
        "Wrapper for save(), callable on a client machine"
        with open(filepath, "w") as savefile:
            save(savefile)
            
    def load(self, filepath):
        "Wrapper for load(), callable on a client machine"
        with open(filepath, "r") as loadfile:
            load(loadfile)
        

telem = Telemetry()
entities = []

telem.load("../res/OCESS.json")
telem.save("../res/quicksave.json")


def simulate_tick():
    
    entity_lock.acquire()
    
    for entity in entities:
        entity.move(5*s/tps)
    
    for A, B in itertools.combinations(entities, 2):
        gravity = gravitational_force(A, B)
        #print(gravity)
        theta = angle(A, B)
        A.accelerate(gravity, theta)
        B.accelerate(-gravity, theta)
    
    entity_lock.release()


daemon = Pyro4.Daemon("localhost", 31415)
daemon.register(telem, "telem")

def exit_handler():
    daemon.close()

atexit.register(exit_handler)

server_thread = threading.Thread(target = daemon.requestLoop)
server_thread.start()


while True:
    time.sleep(1/tps)
    threading.Thread(target = simulate_tick).start()


print("okay")

exit_handler()
