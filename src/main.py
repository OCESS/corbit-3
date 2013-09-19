from entity import Entity
from scipy import array
import json
from unum.units import *

#distance = 100 * m
#print(distance)
#print(distance.asUnit(mile))

print("Corbit v3")

config = json.loads(open("../res/OCESS.json").read())
data = config["entities"][0]

entities = []

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



