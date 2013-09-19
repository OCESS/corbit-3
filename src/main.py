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

displacement = m/1 * array(data["displacement"])
print(displacement)
velocity = m/s * array(data["velocity"])
print(velocity)
acceleration = m/s/s * array(data["acceleration"])
print(acceleration)

name = data["name"]
print(name)
mass = kg/1 * data["mass"]
print(mass)
radius = m * data["radius"]
print(radius)

angular_displacement = rad/1 * data["angular_displacement"]
print(angular_displacement)
angular_velocity = rad/s * data["angular_velocity"]
print(angular_velocity)
angular_acceleration = rad/s/s * data["angular_acceleration"]
print(angular_acceleration)


sun = Entity(displacement, velocity, acceleration,
             name, mass, radius,
             angular_displacement, angular_velocity, angular_acceleration)


print (sun)