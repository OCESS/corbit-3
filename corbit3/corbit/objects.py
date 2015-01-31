import math
import json

import scipy
from scipy import linalg as LA

from unum.units import rad, m, s, kg, N


center = "Habitat"
control = "Habitat"
reference = "Earth"

class Camera:
    """Used to store the zoom level and position of the display's camera. Change this to change the viewpoint"""

    def __init__(self, zoom_level, center=None):
        self.center = center
        if self.center == None:
            self.locked = False
        else:
            self.locked = True

        self.displacement = m * scipy.array([0, 0])
        self.velocity = m / s * scipy.array([0, 0])
        self.acceleration = m / s / s * scipy.array([0, 0])

        self.zoom_level = zoom_level

    # should the camera follow the centred object
    locked = True
    # default speed, but this gets overwritten if it's locked to an object
    speed = 1e2

    def update(self, entity):
        """Updates the camera's position to match that of the center"""
        if self.locked:
            self.displacement = entity.displacement
            self.velocity = entity.velocity
            self.acceleration = entity.acceleration

    def pan(self, amount):
        """Pan the camera by a vector amount"""
        self.acceleration += amount * self.speed

    def move(self, time):
        """Called every tick, keeps the camera moving"""
        self.velocity += self.acceleration * time
        self.acceleration = 0 * m / s / s
        self.displacement += self.velocity * time

    def zoom(self, amount):
        """Zooms the camera in and out. Call this instead of modifying zoom_level"""
        if amount < 0:
            self.zoom_level /= 1 - amount
        else:
            self.zoom_level *= 1 + amount


class Entity:
    """Base class for all physical objects"""

    def __init__(self, name, color, mass, radius,
                 displacement, velocity, acceleration,
                 angular_position, angular_speed, angular_acceleration):
        self.name = name  # should be a string
        self.color = color  # should be a tuple, e.g. (255,255,5)
        self.dry_mass = mass  # should be in units of kg
        self.radius = radius  # should be in units of m

        self.displacement = displacement  # should be in units of m
        self.velocity = velocity  # should be in units of m/s
        self.acceleration = acceleration  # should be in units of m/s/s

        self.angular_position = angular_position  # units: radians
        self.angular_speed = angular_speed  # units: radians/s
        self.angular_acceleration = angular_acceleration  # units: radians/s/s

    def mass(self):
        """Getter function for mass, will be overriden in Entity-derived classes"""
        return self.dry_mass

    def moment_of_inertia(self):
        """Returns the entity's moment of inertia, which is that of a sphere"""
        return (2 * self.mass() * self.radius ** 2) / 5

    def accelerate(self, force, angle):
        """
        Called when the entity is accelerated by a force
        :param force: a cartesian force vector
        :param angle: the angle on the entity that the force is applied onto.
        An angle of zero would mean the force is applied on the front, while
        An angle of pi/2 would mean the force is applied on the left
        ("front" is where the entity is pointing, i.e. self.angular_position)
        """
        # angle += self.angular_position
        # F_theta is the angle of the vector F from the x axis
        # # for example, a force vector pointing directly up will have
        # # F_theta = pi/2
        # angle is the angle from the x axis the force is applied to the entity
        # # for example, a rock hitting the right side of the hab will have
        # # angle = 0
        # # and the engines firing from the bottom of the hab will have
        # # angle = 3pi/2
        F_theta = math.atan2(force[1].asNumber(), force[0].asNumber())

        # a = F / m
        # # where
        # a is linear acceleration, m is mass of entity
        # F is the force that is used in making linear acceleration
        F_cen = force * abs(math.cos(angle - F_theta))
        self.acceleration += F_cen / self.mass()
        # if LA.norm(F_cen.asNumber()) != 0:
        # print(F_cen)

        # w = T / I
        # # where
        # w is angular acceleration in rad/s/s
        # T is torque in J/rad
        # I is moment of inertia in kg*m^2
        # angle -= self.angular_position
        T = N * scipy.linalg.norm(force.asNumber()) \
            * self.radius * math.sin(angle - F_theta)
        self.angular_acceleration += T / self.moment_of_inertia()
        #if T != N*m * 0:
        #print(T)

    def move(self, time):
        """Updates velocities, positions, and rotations for entity
        :param time: the dt for the frame
        """

        self.velocity += self.acceleration * time
        self.acceleration = m / s / s * scipy.array((0, 0))
        self.displacement += self.velocity * time

        self.angular_speed += self.angular_acceleration * time
        self.angular_acceleration = 0 * rad / s / s
        self.angular_position += self.angular_speed * time

    def dict_repr(self):
        """Returns a dictionary representation of the Entity, with all the data needed to
        reconstruct it again"""

        return {
            "name": self.name,
            "color": self.color,
            "mass": self.mass().asNumber(),
            "radius": self.radius.asNumber(),
            "displacement": self.displacement.asNumber().tolist(),
            "velocity": self.velocity.asNumber().tolist(),
            "acceleration": self.acceleration.asNumber().tolist(),
            "angular position": self.angular_position.asNumber(),
            "angular speed": self.angular_speed.asNumber(),
            "angular acceleration": self.angular_acceleration.asNumber()}


class EngineSystem:
    """EngineSystem class, represents things like main habitat engines, habitat RCS systems, etc."""

    def __init__(self, fuel, rated_fuel_flow, I_sp, engine_placements):
        # when I do something like fuel.asNumber(kg) * kg, I'm forcing the units to kg and checking that they
        # are indeed kg in the first place
        self.fuel = fuel.asNumber(kg) * kg    # how much fuel left in the tank
        self.rated_fuel_flow = rated_fuel_flow.asNumber(kg/s) * kg/s  # how fast fuel goes out at 100% engines
        self.I_sp = I_sp.asNumber(m/s) * m/s    # specific impulse i.e. how much thrust you get per kg of fuel

        # a list of pairs of form (angle, vector)
        for angle, vector in engine_placements:
            angle = angle % 2*math.pi           # standard angles are nice
            vector = vector / LA.norm(vector)   # unit vectors only please

        self.engine_placements = engine_placements
        # where 'angle' is where on the entity's surface the engine is placed and
        # 'vector' is in which the engine has its thrust vector
        # for example, [(3.1415, scipy.array((1, 0))] is a single engine, on the bottom, that fires away
        #           __
        #         /    \
        #    <<<<|      |     pchooo the rocket is going off to the right -> -> -> ->
        #         \ __ /
        #
        # TODO: make sure this is actually what is displayed
        # note: the size of the array does not multiply the thrust.
        # when thrusting, we divide the thrust over ALL engines in an EngineSystem

        self.throttle = 0   # self-explanatory, 0: 0%, 0.5: 50%, and 1: 100%

    def thrust(self, time):
        """Determines the thrust a single engine gives out over a time interval
        :param time: time interval over which engine is thrusting, in s
        :return: total thrust, in N
        """
        fuel_usage = self.rated_fuel_flow * self.throttle
        fuel_used = abs(fuel_usage) * time

        if self.fuel > fuel_used:
            self.fuel -= abs(fuel_usage) * time
        else:
            fuel_usage = self.fuel / time
            self.fuel = 0 * kg

        return self.I_sp * fuel_usage / len(self.engine_placements)

    def dict_repr(self):
        """Returns a dictionary with all the values that are needed to construct this again
        contained within the dict"""
        #TODO: don't use this, I'm moving to MySQL at which point I need only save my fuel
        #to the JSON file, since Isp and fuel flow will be hardcoded
        """return {"fuel": self.fuel.asNumber(kg),
                "rated fuel flow": self.rated_fuel_flow.asNumber(kg/s),
                "specific impulse": self.I_sp.asNumber(m/s),
                "placements": self.engine_placements}"""


class Habitat(Entity):
    """A special class for the habitat"""

    def __init__(self, name, color, mass, radius,
                 displacement, velocity, acceleration,
                 angular_position, angular_speed, angular_acceleration,
                 engine_system, rcs_system):
        Entity.__init__(self, name, color, mass, radius,
                        displacement, velocity, acceleration,
                        angular_position, angular_speed, angular_acceleration)
        self.engine_system = engine_system
        self.rcs_system = rcs_system

    def mass(self):
        fuel_mass = self.engine_system.fuel + self.rcs_system.fuel
        return self.dry_mass + fuel_mass

    def move(self, time):
        """Accelerates habitat from main engine thrust, then moves the habitat normally"""
        #todo: move this code into a server loop

#         thrust = self.main_engines.thrust(time)
#         thrust_vector = \
#             N * scipy.array((math.cos(self.angular_position) * thrust.asNumber(N),
#                              math.sin(self.angular_position) * thrust.asNumber(N)))
#         for angle in self.main_engines.engine_positions:
#             self.accelerate(
#                 thrust_vector / len(self.main_engines.engine_positions),
#                angle + self.angular_position)

        Entity.move(self, time)

    def dict_repr(self):
        blob = Entity.dict_repr(self)
        blob["main fuel"] = self.engine_system.fuel
        blob["rcs fuel"] = self.rcs_system.fuel
        return blob


def oneshot_vernier_thrusters(entity, amount, time):
    """Produces immediate thrust from vernier thrusters of given entity
    :param entity: target entity
    :param amount: ratio of vernier thruster rated thrust to thrust by
    :param time: time over which to thrust
    """
    for angle in entity.rcs.engine_positions:
        print(amount * entity.rcs.thrust(time) * scipy.array(
            (-math.sin(entity.angular_position + angle), math.cos(entity.angular_position + angle)))
              / len(entity.rcs.engine_positions), angle + entity.angular_position)
        entity.accelerate(amount * entity.rcs.thrust(time) * scipy.array(
            (-math.sin(entity.angular_position + angle), math.cos(entity.angular_position + angle)))
                          / len(entity.rcs.engine_positions), angle + entity.angular_position)


def find_entity(name, entities):
    """Accesses the first entity specified by name
    :param name: string of the target object's name
    :param entities: the list of entites in which to search in
    :return: an Entity asked for
    """
    for entity in entities:
        if entity.name == name:
            return entity


def json_serialize(entities, output_stream=None, pretty=False, json_sort_keys=False):
    """Serializes a list of entities into a JSON string
    :param entities: the list of entities to serialize
    :return: the JSON string representation of the entities
    """
    json_separators = (",", ":")
    json_indent = None
    if pretty:
        json_separators = (",", ": ")
        json_indent = 4

    json_data = {"entities": [],
                 "habitats": []}

    for entity in entities:
        if type(entity) is Habitat:
            json_data["habitats"].append(entity.dict_repr())
        elif type(entity) is Entity:
            json_data["entities"].append(entity.dict_repr())
        else:
            print("found something in entities list that isn't a recognized entity or derivative work,", entity.name)

    if not json_data["habitats"]:
        del json_data["habitats"]
    if not json_data["entities"]:
        del json_data["entities"]

    if output_stream is None:
        return json.dumps(json_data, indent=json_indent, sort_keys=json_sort_keys, separators=json_separators)
    else:
        return json.dump(json_data, output_stream,
                         indent=json_indent, sort_keys=json_sort_keys, separators=json_separators)





