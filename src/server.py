__version__ = "3.0.0"

from entity import Entity,Habitat
import physics
from scipy import array, linalg
import json
from unum.units import N,m,s,kg,rad,Hz
import atexit
import threading
import time
import itertools
from math import sin,cos,atan2,pi
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
    return m * linalg.norm((A.displacement - B.displacement).asNumber(m))

def angle(A, B):
    return atan2((B.displacement[1] - A.displacement[1]),
                      (B.displacement[0] - A.displacement[0]))
    
def gravitational_force(A, B):
    unit_distance = array([cos(angle(A,B)), sin(angle(A,B))])
    return G * A.mass() * B.mass() / distance(A,B)**2 * unit_distance

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
            rcs_fuel = kg * habitat["rcs_fuel"]
            
        except KeyError:
            print("habitat " + name + " has undefined elements, skipping...")
            break
        json_entities.append(Habitat(name, color, mass, radius,
                                    displacement, velocity, acceleration,
                                    angular_position, angular_speed,
                                    angular_acceleration,
                                    fuel, rcs_fuel))
    
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
    
    def change_main_engines(self, name, increment):
        "Changes the engine usage of the specified entity. Fails if no engines"
        for entity in entities:
            if entity.name == name:
                entity.main_engines.usage += increment
        
    def fire_rcs_thrusters(self, name, direction):
        "Changes the rcs usage of the specified entity. Fails if no thrusters"
        target = Entity
        for entity in entities:
            if entity.name == name:
                target = entity
        
        rcs_thrust = target.rcs.thrust(1/tps)
        theta = direction + target.angular_position
        rcs_thrust_vector = \
            N * array((cos(theta) * rcs_thrust.asNumber(), 
                       sin(theta) * rcs_thrust.asNumber()))
        for angle in target.rcs.engine_positions:
            target.accelerate(
                rcs_thrust_vector/len(target.rcs.engine_positions), angle)
        
    def fire_vernier_thrusters(self, name, amount):
        "Changes the vernier thrusters of the specified entity. Fails if none"
        target = Entity
        for entity in entities:
            if entity.name == name:
                target = entity
       
        vernier_thrust = target.rcs.thrust(1/tps)
        vernier_thrust_vector = \
            N * array((0, vernier_thrust.asNumber())) * amount
        target.accelerate(vernier_thrust_vector, 0)
        target.accelerate(-vernier_thrust_vector, pi)
        #for angle in target.rcs.engine_positions:
            #target.accelerate(
                #vernier_thrust_vector/len(target.rcs.engine_positions), angle)
            #print(vernier_thrust_vector,angle)
            ## this code rotates the vernier_thrust_vector by pi/2, since to
            ## rotate a vector, (x,y) = (-y, x)
            #vernier_thrust_vector[0], vernier_thrust_vector[1] = \
            #-vernier_thrust_vector[1], vernier_thrust_vector[0]

    
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
    
    #for A, B in itertools.combinations(entities, 2):
    #    gravity = gravitational_force(A, B)
    #    theta = angle(A, B)
    #    A.accelerate(gravity, theta)
    #    B.accelerate(-gravity, theta)

    collisions = []
    for A, B in itertools.combinations(entities, 2):
        affected_objects = physics.resolve_collision(A, B, 1/tps)
        if affected_objects != None:
            collisions += affected_objects
    
    for entity in entities:
        already_moved = False
        for name in collisions:
            if entity.name == name:
                already_moved = True
        
        if not already_moved:
            entity.move(1/tps)
    
    entity_lock.release()


daemon = Pyro4.Daemon(HOST, PORT)
daemon.register(telem, "telem")

def exit_handler():
    daemon.close()

atexit.register(exit_handler)

server_thread = threading.Thread(target = daemon.requestLoop)
server_thread.start()


while True:
    time.sleep(1/tps.asNumber(Hz))
    threading.Thread(target = simulate_tick).start()


print("okay")

exit_handler()
