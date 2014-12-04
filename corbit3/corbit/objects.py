from unum.units import rad, m, s, kg, N
import scipy
import math
import json
import io
import collections

class Camera:
    "Used to store the zoom level and position of the display's camera. Change this to change the viewpoint"

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

    locked = True
    speed = 1e2

    def update(self, entity):
        "Updates the camera's position to match that of the center"
        if self.locked:
            self.displacement = entity.displacement
            self.velocity = entity.velocity
            self.acceleration = entity.acceleration

    def pan(self, amount):
        "Pan the camera by a vector amount"
        self.acceleration += amount * self.speed

    def move(self, time):
        "Called every tick, keeps the camera moving"
        self.velocity += self.acceleration * time
        self.acceleration = 0 * m / s / s
        self.displacement += self.velocity * time

    def zoom(self, amount):
        "Zooms the camera in and out. Call this instead of modifying zoom_level"
        if amount < 0:
            self.zoom_level /= 1 - amount
        else:
            self.zoom_level *= 1 + amount


class Entity:
    "Base class for all physical objects"

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
        "Getter function for mass, will be overriden in Entity-derived classes"
        return self.dry_mass

    def moment_of_inertia(self):
        "Returns the entity's moment of inertia, which is that of a sphere"
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
        "Returns an ordered dictionary representation of the Entity"

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
    "Engine class, represents things like main habitat engines, habitat RCS systems, etc."

    def __init__(self, fuel, rated_fuel_flow, I_sp, engine_positions):
        self.fuel = fuel
        self.rated_fuel_flow = rated_fuel_flow
        self.I_sp = I_sp
        self.engine_positions = engine_positions
        self.usage = 0

    def thrust(self, time):
        """Determines the thrust an engine gives out over a time interval
        :param time: time interval over which engine is thrusting, in s
        :return: total thrust, in N
        """
        if self.fuel > (self.rated_fuel_flow * abs(self.usage)) * time:
            fuel_usage = self.rated_fuel_flow * self.usage
            self.fuel -= abs(fuel_usage) * time
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

        self.main_engines = Engine(fuel, 100 * kg / s, 5000 * m / s, [math.pi])
        self.rcs = \
            Engine(rcs_fuel, 5 * kg / s, 3000 * m / s, [0, math.pi / 2, math.pi, 3 * math.pi / 2])
        self.rcs.usage = 1

    def mass(self):
        return self.dry_mass + self.rcs.fuel + self.main_engines.fuel

    def move(self, time):
        "Accelerates habitat from main engine thrust, then moves the habitat normally"

        thrust = self.main_engines.thrust(time)
        thrust_vector = \
            N * scipy.array((math.cos(self.angular_position) * thrust.asNumber(N),
                             math.sin(self.angular_position) * thrust.asNumber(N)))
        for angle in self.main_engines.engine_positions:
            self.accelerate(
                thrust_vector / len(self.main_engines.engine_positions),
                angle + self.angular_position)

        Entity.move(self, time)

    def dict_repr(self):
        blob = Entity.dict_repr(self)
        blob.update(collections.OrderedDict([
            ("fuel", self.main_engines.fuel.asNumber()),
            ("rcs_fuel", self.rcs.fuel.asNumber())
        ]))
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


def save(output_stream, entities):
    """Dumps a list of entities into a JSON string in the a given stream
    :param output_stream: the stream to dump to, e.g. can be a filestream
    :param entities: the list of entities to dump
    :return: None
    """
    json_data = {}
    json_data["entities"] = []

    for entity in entities:
        json_data["entities"].append(entity.dict_repr())

    json.dump(json_data, output_stream,
              indent=4, sort_keys=False, separators=(",", ": "))


def json_serialize(entities):
    """Serializes a list of entities into a JSON string
    :param entities: the list of entities to serialize
    :return: the JSON string representation of the entities
    """
    json_data = {}
    json_data["entities"] = []
    json_data["habitats"] = []

    for entity in entities:
        if type(entity) is Habitat:
            json_data["habitats"].append(entity.dict_repr())
        elif type(entity) is Entity:
            json_data["entities"].append(entity.dict_repr())
        else:
            print("found something in entities list that isn't a recognized entity or derivative work,", entity.name)

    return json.dumps(json_data, separators=(",", ":"))


def load(input_stream):
    """Given a JSON string or a JSON stream of entities, parses into binary and returns
    :param input_stream: string or stream of Corbit format to parse
    :return: a list of entities
    """
    if isinstance(input_stream, str):  # Converts strings to streams just like that
        input_stream = io.StringIO(input_stream)
    json_root = json.load(input_stream)
    json_entities = []

    try:
        data = json_root["entities"]
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

                displacement = m * scipy.array(entity["displacement"])
                velocity = m / s * scipy.array(entity["velocity"])
                acceleration = m / s / s * scipy.array(entity["acceleration"])

                angular_position = rad * entity["angular_position"]
                angular_speed = rad / s * entity["angular_speed"]
                angular_acceleration = rad / s / s * entity["angular_acceleration"]

            except KeyError:
                print("entity " + name + " has undefined elements, skipping...")
                break

            json_entities.append(Entity(name, color, mass, radius,
                                                       displacement, velocity, acceleration,
                                                       angular_position, angular_speed,
                                                       angular_acceleration))
    except KeyError:
        print("no entities found")

    try:
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

                displacement = m * scipy.array(habitat["displacement"])
                velocity = m / s * scipy.array(habitat["velocity"])
                acceleration = m / s / s * scipy.array(habitat["acceleration"])

                angular_position = rad * habitat["angular_position"]
                angular_speed = rad / s * habitat["angular_speed"]
                angular_acceleration = rad / s / s * habitat["angular_acceleration"]

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

    except KeyError:
        print("no habitats found")
    return json_entities


