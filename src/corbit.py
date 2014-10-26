from unum.units import rad, m, s, kg, N

import io
from math import atan2, cos, sin, pi, sqrt
import scipy
import scipy.linalg as LA
from scipy import array, sign
from copy import deepcopy
import collections
import json

# This file simply contains a lot of the commonly-used functions, or
# functions that would just clutter up the server.py and client.py files.
# For example, corbit.Entity is in this namespace, so is corbit.load(stream)

def sendall(msg, sock):
    """Sends an entire string delimited in Corbit format (i.e. with ';')
    :param msg: a string to be sent
    :param sock: the socket object on which to be sent
    :return: True if successful, False otherwise
    """
    try:
        sock.sendall((msg + ";").encode("UTF-8"))
    except BrokenPipeError:
        print("Tried sending")
        print(msg)
        print("but connection broke!")
        return False
    return True


def recvall(sock):
    """Receives an entire string delimited according to Corbit (i.e. with a ';')
    :param sock: socket object on which to receive from
    :return: the received string
    """
    end_marker = ";".encode("UTF-8")
    total_data = b""
    while True:
        chunk = sock.recv(8192)
        if end_marker in chunk:
            total_data += chunk[:chunk.find(end_marker)]  # Add everything up to but not including the end marker
            break
        total_data += chunk
        if len(total_data) > 1:
            # Check if end_marker was split
            last_pair = bytes([chunk[-2], chunk[-1]])  # last_pair is a byte string of the last two bytes in chunk
            if end_marker in last_pair:
                total_data[-2] = last_pair[:last_pair.find(end_marker) - 1]
        if chunk == b"":
            break
    return total_data.decode("UTF-8")


class Camera:
    "Used to store the zoom level and position of the display's camera. Change this to change the viewpoint"

    def __init__(self, zoom_level, center=None):
        self.center = center
        if self.center == None:
            self.locked = False
        else:
            self.locked = True

        self.displacement = m * array([0, 0])
        self.velocity = m / s * array([0, 0])
        self.acceleration = m / s / s * array([0, 0])

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
    """Given a JSON string or a JSON stream of entities, parses into binary objects and returns
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

                displacement = m * array(entity["displacement"])
                velocity = m / s * array(entity["velocity"])
                acceleration = m / s / s * array(entity["acceleration"])

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

                displacement = m * array(habitat["displacement"])
                velocity = m / s * array(habitat["velocity"])
                acceleration = m / s / s * array(habitat["acceleration"])

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
        F_theta = atan2(force[1].asNumber(), force[0].asNumber())

        # a = F / m
        # # where
        # a is linear acceleration, m is mass of entity
        # F is the force that is used in making linear acceleration
        F_cen = force * abs(cos(angle - F_theta))
        self.acceleration += F_cen / self.mass()
        # if LA.norm(F_cen.asNumber()) != 0:
        # print(F_cen)

        # w = T / I
        # # where
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
        """Updates velocities, positions, and rotations for entity
        :param time: the dt for the frame
        """

        self.velocity += self.acceleration * time
        self.acceleration = m / s / s * array((0, 0))
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
            self.fuel -= fuel_usage * sign(self.usage) * time
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

        self.main_engines = Engine(fuel, 100 * kg / s, 5000 * m / s, [pi])
        self.rcs = \
            Engine(rcs_fuel, 5 * kg / s, 3000 * m / s, [0, pi / 2, pi, 3 * pi / 2])
        self.rcs.usage = 1

    def mass(self):
        return self.dry_mass + self.rcs.fuel + self.main_engines.fuel

    def move(self, time):
        "Accelerates habitat from main engine thrust, then moves the habitat normally"

        thrust = self.main_engines.thrust(time)
        thrust_vector = \
            N * array((cos(self.angular_position) * thrust.asNumber(N),
                       sin(self.angular_position) * thrust.asNumber(N)))
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
        print(amount * entity.rcs.thrust(time) * array(
            (-sin(entity.angular_position + angle), cos(entity.angular_position + angle)))
              / len(entity.rcs.engine_positions), angle + entity.angular_position)
        entity.accelerate(amount * entity.rcs.thrust(time) * array(
            (-sin(entity.angular_position + angle), cos(entity.angular_position + angle)))
                          / len(entity.rcs.engine_positions), angle + entity.angular_position)


def distance(A, B):
    return m * LA.norm((A.displacement - B.displacement).asNumber(m))


def altitude(A, B):
    return distance(A, B) - A.radius - B.radius


def angle(A, B):
    return atan2((B.displacement[1] - A.displacement[1]),
                 (B.displacement[0] - A.displacement[0]))


def gravitational_force(A, B):
    unit_distance = array([cos(angle(A, B)), sin(angle(A, B))])
    return G * A.mass() * B.mass() / distance(A, B) ** 2 * unit_distance


def resolve_collision(A, B, time):
    """Detects and acts upon any collisions in the specified time interval between two entities
    :param A: First entity
    :param B: Second entity
    :param time: time interval over which to check if any collisions occur
    :return: None if no collision will occur in the timeframe, the two collided entities if there is a collision
    """
    # general overview of this function:
    # 1. find if the objects will collide in the given time
    # 2. if yes, calculate collision:
    # 2.1 represent velocities as normal velocity and tangential velocity
    # 2.2 do a 1D collision using the normal veloctiy
    # 2.3 add the normal and tangential velocities to get the new velocity

    scipy.seterr(divide="raise", invalid="raise")

    # for this function I make one of the objects the frame of reference
    # which means my calculations are much simplified
    displacement = A.displacement - B.displacement
    velocity = A.velocity - B.velocity
    acceleration = A.acceleration - B.acceleration
    radius_sum = A.radius + B.radius

    # this code finds when the the two entities will collide. See
    # http://www.gvu.gatech.edu/people/official/jarek/graphics/material/collisionsDeshpandeKharsikarPrabhu.pdf
    # for how I got the algorithm
    a = m ** 2 / s ** 2 * LA.norm(velocity.asNumber(m / s)) ** 2
    b = m ** 2 / s * 2 * scipy.dot(displacement.asNumber(m), velocity.asNumber(m / s))
    c = m ** 2 * LA.norm(displacement.asNumber(m)) ** 2 - radius_sum ** 2

    try:
        t_to_impact = \
            (-b - m ** 2 / s * sqrt((b ** 2 - 4 * a * c).asNumber(m ** 4 / s ** 2))) / (2 * a)
    except:
        return

    if not scipy.isfinite(t_to_impact.asNumber(s)):
        return

    if t_to_impact > time or t_to_impact < 0 * s:
        return

    # at this point, we know there is a collision
    print("Collision:", A.name, "and", B.name, "in", t_to_impact)

    # for this section, basically turn the vectors into normal velocity and tangential velocity,
    # then do a 1D collision calculation, using the normal velocities
    # since a ' (prime symbol) wouldn't work, I've replaced it with a _ in variable names

    n = displacement  # normal vector
    un = n / (m * LA.norm(n.asNumber(m)))  # normal unit vector
    unt = deepcopy(un)  # normal tangent vector
    unt[0], unt[1] = \
        -unt[1], unt[0]

    # A's centripetal velocity
    vAn = m / s * scipy.dot(un.asNumber(), A.velocity.asNumber(m / s))
    # A's tangential velocity
    vAt = m / s * scipy.dot(unt.asNumber(), A.velocity.asNumber(m / s))

    # B's centripetal velocity
    vBn = m / s * scipy.dot(un.asNumber(), B.velocity.asNumber(m / s))
    # B's tangential velocity
    vBt = m / s * scipy.dot(unt.asNumber(), B.velocity.asNumber(m / s))

    # tangent velocities are unchanged, nothing happens to them
    vAt_ = vAt
    vBt_ = vBt

    # centripetal velocities are calculated with a simple 1D collision formula
    R = 0.1

    vAn_ = \
        (A.mass() * vAn + B.mass() * vBn + R * B.mass() * (B.velocity - A.velocity)) / \
        (A.mass() + B.mass())

    vBn_ = \
        (A.mass() * vAn + B.mass() * vBn + R * A.mass() * (A.velocity - B.velocity)) / \
        (A.mass() + B.mass())

    # convert scalar normal and tangent velocities to vector quantities
    VAn = vAn_ * un
    VAt = vAt_ * unt

    VBn = vBn_ * un
    VBt = vBt_ * unt

    # move until the point of impact
    A.move(t_to_impact)
    B.move(t_to_impact)

    # add em up to get v'
    A.velocity = VAn + VAt
    B.velocity = VBn + VBt

    # move for the rest of the frame
    A.move(time - t_to_impact)
    B.move(time - t_to_impact)

    return [A.name, B.name]