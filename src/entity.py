from unum.units import rad,m,s,kg
import json

class Entity:
    "Base class for all physical objects"
            
    def __init__(self, name, color, mass, radius,
                 displacement, velocity, acceleration,
                 angular_displacement, angular_velocity, angular_acceleration):
        
        self.name = name
        self.color = color
        self.mass = mass
        self.radius = radius
        
        self.displacement = displacement
        self.velocity = velocity
        self.acceleration = acceleration
        
        self.angular_displacement = angular_displacement
        self.angular_velocity = angular_velocity
        self.angular_acceleration = angular_acceleration
    
    def moment_of_inertia(self):
        "Returns the entity's moment of inertia"
        return (2 * self.mass * self.radius*self.radius) / 5
    
    def accelerate(self, force, angle):
        """
        Called when the entity is accelerated by a force
        Force: a cartesian force vector
        Angle: the angle on the entity that the force is applied onto
        """
#         print("self.a: " + str(self.acceleration))
#         print("force: " + str(force))
#         print("self.mass: " + str(self.mass))
#         print("accel: " + str(force/self.mass))
        self.acceleration += force / self.mass
#         print(self.acceleration)
        
    def move(self, time):
        "Updates velocities, positions, and rotations for entity"
        
#         print(self.name + " delta: " + str(self.velocity))
        self.velocity += self.acceleration * time
#         print(self.name + " delta: " + str(self.velocity))
        self.acceleration = 0 * m/s/s
        self.displacement += self.velocity * time

        self.angular_velocity += self.angular_acceleration * time
        self.angular_acceleration = 0 * rad/s/s
        self.angular_displacement += self.angular_velocity * time
    
    def dict_repr(self):
        "Returns a dictionary representation of the Entity"
        
        blob = {}
        
        blob["name"] = self.name
        blob["color"] = self.color  
        blob["mass"] = self.mass.asNumber()
        blob["radius"] = self.radius.asNumber()
        
        blob["displacement"] = self.displacement.asNumber().tolist()
        blob["velocity"] = self.velocity.asNumber().tolist()
        blob["acceleration"] = self.acceleration.asNumber().tolist()
        
        blob["angular_displacement"] = self.angular_displacement.asNumber()
        blob["angular_velocity"] = self.angular_velocity.asNumber()
        blob["angular_acceleration"] = self.angular_acceleration.asNumber()
        
        return blob
        
