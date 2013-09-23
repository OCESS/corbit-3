from math import cos
from unum.units import *

class Entity:
    "Base class for all physical objects"
            
    def __init__(self, displacement, velocity, acceleration,
                 name, mass, radius,
                 angular_displacement, angular_velocity, angular_acceleration):
        
        self.displacement = displacement
        self.velocity = velocity
        self.acceleration = acceleration
        
        self.name = name
        self.mass = mass
        self.radius = radius
        
        self.angular_displacement = angular_displacement
        self.angular_velocity = angular_velocity
        self.angular_acceleration = angular_acceleration
    
    def moment_of_inertia(self):
        "Returns the entity's moment of inertia"
        return (2 * self.mass * self.radius*self.radius) / 5
    
    def accelerate(self, force, theta):
        "Called when the entity is accelerated by a force"
        self.acceleration += (force * cos(theta)) / self.mass
        
    def move(self, time):
        "Updates velocities, positions, and rotations for entity"
        
        self.velocity += self.acceleration * time
        self.acceleration = 0 * m/s/s
        self.displacement += self.velocity * time

        self.angular_velocity += self.angular_acceleration * time
        self.angular_acceleration = 0 * rad/s/s
        self.angular_displacement += self.angular_velocity * time