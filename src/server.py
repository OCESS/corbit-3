__version__ = "3.0.0"

from entity import Entity,Habitat
from scipy import array, linalg
import json
from unum.units import N,m,s,kg,rad,Hz
import atexit
import threading
import time
import itertools
import math
import Pyro4

print("Corbit SERVER " + __version__)
tps = 60 * Hz

entity_lock = threading.Lock()

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.clear()
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
HOST = "localhost"  # IP address to bind to
PORT = 3141        # Arbitrary port I picked

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
    json_entities = []
    
    try:
        data = json_root["entities"]
    except KeyError:
        print("no entities found")
    for entity in data:
        try:
            name = entity["name"]
        except:
            print("unnamed entity found, skipping")
            break
        try:
            color = entity["color"]
            mass = kg * entity["mass"]
            radius = m * entity["radius"]
            
            displacement = m * array(entity["displacement"])
            velocity = m/s * array(entity["velocity"])
            acceleration = m/s/s * array(entity["acceleration"])
            
            angular_position = rad * entity["angular_position"]
            angular_speed = rad/s * entity["angular_speed"]
            angular_acceleration = rad/s/s * entity["angular_acceleration"]
            
        except KeyError:
            print("entity " + name + " has undefined elements, skipping...")
            break
        
        json_entities.append(Entity(name, color, mass, radius,
                                    displacement, velocity, acceleration,
                                    angular_position, angular_speed,
                                    angular_acceleration))
    
    data = json_root["habitats"]
    for habitat in data:
        try:
            name = habitat["name"]
        except KeyError:
            print("unnamed habitat found, skipping")
            break
        try:
            color = habitat["color"]
            mass = kg * habitat["mass"]
            radius = m * habitat["radius"]
            
            displacement = m * array(habitat["displacement"])
            velocity = m/s * array(habitat["velocity"])
            acceleration = m/s/s * array(habitat["acceleration"])
            
            angular_position = rad * habitat["angular_position"]
            angular_speed = rad/s * habitat["angular_speed"]
            angular_acceleration = rad/s/s * habitat["angular_acceleration"]
        
            fuel = kg * habitat["fuel"]
            
        except KeyError:
            print("habitat " + name + " has undefined elements, skipping...")
            break
        json_entities.append(Habitat(name, color, mass, radius,
                                    displacement, velocity, acceleration,
                                    angular_position, angular_speed,
                                    angular_acceleration,
                                    fuel))
    
    global entities
    entities = json_entities


class Telemetry:
    "Class that transfers data between server and other programs"
    
    def entities(self):
        "Wrapper for accessing entities, callable on a client machine"
        return entities
    
    def entity(self, name):
        "Accesses the first entity specified by name"
        for entity in entities:
            if entity.name == name:
                return entity
    
    def accelerate(self, name, force, angle):
        "Wrapper for accelerating entities, callable on a client machine"
        for entity in entities:
            if entity.name == name:
                entity.accelerate(force, angle)
    
    def change_engines(self, name, increment):
        "Changes the engine usage of the specified entity. Fails if no engines"
        for entity in entities:
            if entity.name == name:
                entity.engine_usage += increment
        
    def save(self, filepath):
        "Wrapper for save(), callable on a client machine"
        with open(filepath, "w") as savefile:
            save(savefile)
             
    def load(self, filepath):
        "Wrapper for load(), callable on a client machine"
        with open(filepath, "r") as loadfile:
            load(loadfile)
        

telem = Telemetry()


telem.load("../res/OCESS.json")

def simulate_tick():
    
    entity_lock.acquire()

    for entity in entities:
        entity.move(1/tps)
    
    #for A, B in itertools.combinations(entities, 2):
    #    gravity = gravitational_force(A, B)
    #    theta = angle(A, B)
    #    A.accelerate(gravity, theta)
    #    B.accelerate(-gravity, theta)
    
    entity_lock.release()


daemon = Pyro4.Daemon(HOST, PORT)
daemon.register(telem, "telem")

def exit_handler():
    daemon.close()

atexit.register(exit_handler)

server_thread = threading.Thread(target = daemon.requestLoop)
server_thread.start()


while True:
    time.sleep(1/tps.asNumber())
    threading.Thread(target = simulate_tick).start()


print("okay")

exit_handler()
