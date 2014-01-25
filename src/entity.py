from unum.units import rad,m,s,kg,N
import collections
from math import atan2,cos,sin,pi
import scipy.linalg as LA
from scipy import array,sign

class Entity:
    "Base class for all physical objects"
            
    def __init__(self, name, color, mass, radius,
                 displacement, velocity, acceleration,
                 angular_position, angular_speed, angular_acceleration):
        
        self.name = name    # should be a string
        self.color = color  # should be a tuple, e.g. (255,255,5)
        self.dry_mass = mass    # should be in units of kg
        self.radius = radius    # should be in units of m
        
        self.displacement = displacement    # should be in units of m
        self.velocity = velocity            # should be in units of m/s
        self.acceleration = acceleration    # should be in units of m/s/s 
        
        self.angular_position = angular_position    # units: radians 
        self.angular_speed = angular_speed            # units: radians/s
        self.angular_acceleration = angular_acceleration    # units: radians/s/s
    
    def mass(self):
        return self.dry_mass
    
    def moment_of_inertia(self):
        "Returns the entity's moment of inertia, which is that of a sphere"
        return (2 * self.mass() * self.radius**2) / 5
    
    def accelerate(self, force, angle):
        """
        Called when the entity is accelerated by a force
        force: a cartesian force vector
        angle: the angle on the entity that the force is applied onto.
        An angle of zero would mean the force is applied on the front, while
        An angle of pi/2 would mean the force is applied on the left
        ("front" is where the entity is pointing, i.e. self.angular_position)
        """
        #angle += self.angular_position
        # F_theta is the angle of the vector F from the x axis
        ## for example, a force vector pointing directly up will have
        ## F_theta = pi/2
        # angle is the angle from the x axis the force is applied to the entity
        ## for example, a rock hitting the right side of the hab will have
        ## angle = 0
        ## and the engines firing from the bottom of the hab will have
        ## angle = 3pi/2
        F_theta = atan2(force[1].asNumber(), force[0].asNumber())
        
        # a = F / m
        ## where
        # a is linear acceleration, m is mass of entity
        # F is the force that is used in making linear acceleration
        F_cen = force * abs(cos(angle - F_theta))
        self.acceleration += F_cen / self.mass()
        #if LA.norm(F_cen.asNumber()) != 0:
            #print(F_cen)
        
        # w = T / I
        ## where
        # w is angular acceleration in rad/s/s
        # T is torque in J/rad
        # I is moment of inertia in kg*m^2
        #angle -= self.angular_position
        T = N * LA.norm(force.asNumber()) \
            * self.radius * sin(angle - F_theta)
        self.angular_acceleration += T / self.moment_of_inertia()
        #if T != N*m * 0:
            #print(T)
        
    def move(self, time):
        "Updates velocities, positions, and rotations for entity"
        
        self.velocity += self.acceleration * time
        self.acceleration = m/s/s * array((0,0))
        self.displacement += self.velocity * time

        self.angular_speed += self.angular_acceleration * time
        self.angular_acceleration = 0 * rad/s/s
        self.angular_position += self.angular_speed * time
    
    def dict_repr(self):
        "Returns a dictionary representation of the Entity"
        
        blob = collections.OrderedDict([
        
         ("name", self.name),
         ("color", self.color),  
         ("mass", self.mass().asNumber()),
         ("radius", self.radius.asNumber()),
         
         ("displacement", self.displacement.asNumber().tolist()),
         ("velocity", self.velocity.asNumber().tolist()),
         ("acceleration", self.acceleration.asNumber().tolist()),
         
         ("angular_position", self.angular_position.asNumber()),
         ("angular_speed", self.angular_speed.asNumber()),
         ("angular_acceleration", self.angular_acceleration.asNumber())
        
        ])
        
        return blob
         
class Engine:
    def __init__(self, fuel, rated_fuel_flow, I_sp, engine_positions):
        self.fuel = fuel
        self.rated_fuel_flow = rated_fuel_flow
        self.I_sp = I_sp
        self.engine_positions = engine_positions
        self.usage = 0
    
    def thrust(self, time):
        if self.fuel > (self.rated_fuel_flow * abs(self.usage)) * time:
            fuel_usage = self.rated_fuel_flow * self.usage
            self.fuel -= fuel_usage*sign(self.usage) * time
        else:
            fuel_usage = self.fuel / time
            self.fuel = 0 * kg
        return self.I_sp * fuel_usage

       
class Habitat(Entity):
    "A special class for the habitat"

    def __init__(self, name, color, mass, radius,
                 displacement, velocity, acceleration,
                 angular_position, angular_speed, angular_acceleration,
                 fuel, rcs_fuel):
        Entity.__init__(self, name, color, mass, radius,
                 displacement, velocity, acceleration,
                 angular_position, angular_speed, angular_acceleration)
        
        self.main_engines = Engine(fuel, 100 * kg/s, 5000 * m/s, [pi])
        self.rcs = \
            Engine(rcs_fuel, 5 * kg/s, 3000 * m/s, [0, pi/2, pi, 3*pi/2])
        self.rcs.usage = 1
    
    def mass(self):
        return self.dry_mass + self.rcs.fuel + self.main_engines.fuel
        
    def move(self, time):
        "kind of a place holder function atm"
        
        thrust = self.main_engines.thrust(time)
        thrust_vector = \
            N * array((cos(self.angular_position)*thrust.asNumber(),
                       sin(self.angular_position)*thrust.asNumber()))
        for angle in self.main_engines.engine_positions:
            self.accelerate(
                thrust_vector/len(self.main_engines.engine_positions),
                angle + self.angular_position)
        
        
        Entity.move(self, time)
