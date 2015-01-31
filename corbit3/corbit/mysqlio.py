import io
import MySQLdb as msd # msd -> My Sql Db
import json
import scipy
from corbit.objects import Entity, EngineSystem, Habitat
from unum.units import kg, m, s, rad

__author__ = 'vac'


def load_entities(json_object):
    # protip: uncomment all those print lines if you want to find out where
    # a given object has undefined elements. Pretty handy. I spent several hours
    # figuring out what was happening until I put those print statements in,
    # and it turned out my server was sending fields like "angular_speed" instead
    # of "angular speed"
    # I should really make unit tests
    color = json_object["color"]
    #print(name, "color", color)
    mass = kg * json_object["mass"]
    #print(name, "mass", mass)
    radius = m * json_object["radius"]
    #print(name, "radius", radius)
    displacement = m * scipy.array(json_object["displacement"])
    #print(name, "displacement", displacement)
    velocity = m/s * scipy.array(json_object["velocity"])
    #print(name, "velocity", velocity)
    acceleration = m/s/s * scipy.array(json_object["acceleration"])
    #print(name, "acceleration", acceleration)
    angular_position = rad * json_object["angular position"]
    #print(name, "angular position", angular_position)
    angular_speed = rad/s * json_object["angular speed"]
    #print(name, "angular speed", angular_speed)
    angular_acceleration = rad/s/s * json_object["angular acceleration"]
    #print(name, "angular acceleration", angular_acceleration)
    return (color, mass, radius, displacement, velocity, acceleration,
            angular_position, angular_speed, angular_acceleration)


def load_json(input_stream):
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
                color, mass, radius, displacement, velocity, acceleration,\
                angular_position, angular_speed, angular_acceleration = load_entities(entity)
                json_entities.append(Entity(name, color, mass, radius,
                                            displacement, velocity, acceleration,
                                            angular_position, angular_speed,
                                            angular_acceleration))
            except KeyError:
                print("entity " + name + " has undefined elements, skipping...")
                break
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
                color, mass, radius, displacement, velocity, acceleration, \
                    angular_position, angular_speed, angular_acceleration = load_entities(habitat)
                engine_system = EngineSystem(habitat["main fuel"] * kg,
                                          5 * kg/s,
                                          3000 * m/s,
                                          [[3.28, [1,0]],
                                           [3.0, [1, 0]]])
                rcs_system = EngineSystem(habitat["rcs fuel"] * kg,
                                          5 * kg/s,
                                          3000 * m/s,
                                          [[0.0, [-1,0]],
                                           [1.57, [0,-1]],
                                           [3.14, [1,0]],
                                           [4.71, [0,1]]])
                #print(name, "engine system", system)
                json_entities.append(Habitat(name, color, mass, radius,
                                             displacement, velocity, acceleration,
                                             angular_position, angular_speed,
                                             angular_acceleration,
                                             engine_system, rcs_system))
            except KeyError:
                print("habitat " + name + " has undefined elements, skipping...")
                break
    except KeyError:
        print("no habitats found")

    return json_entities


db_cursor = None
db = None
def init_db(entities, db_info):
    global db
    db = msd.connect(*db_info)
    global db_cursor
    db_cursor = db.cursor()
    #TODO: in the future, if you want to implement a "restore previous state" option, like what orbit has right now,
    #you can just not run this function, and then and then load whatever is in
    db_cursor.execute("DROP TABLE IF EXISTS flight")
    db_cursor.execute("""CREATE TABLE flight (
        NAME CHAR(64) NOT NULL,
        MASS DOUBLE NOT NULL,
        RADIUS DOUBLE NOT NULL,
        COLORR INT NOT NULL,
        COLORG INT NOT NULL,
        COLORB INT NOT NULL,
        POSX DOUBLE NOT NULL,
        POSY DOUBLE NOT NULL,
        VX DOUBLE NOT NULL,
        VY DOUBLE NOT NULL,
        ACCX DOUBLE NOT NULL,
        ACCY DOUBLE NOT NULL,
        ANGPOS DOUBLE NOT NULL,
        ANGV DOUBLE NOT NULL,
        ANGACC DOUBLE NOT NULL,
        FUEL DOUBLE,
        RCSFUEL DOUBLE)""")
    db_cursor.execute("DROP TABLE IF EXISTS flightcommands")
    db_cursor.execute("""CREATE TABLE flightcommands (
      COMMAND CHAR(64) NOT NULL,
      TARGET CHAR(64),
      AMOUNT DOUBLE)""")


def commit_to_db(entities):
    for entity in entities:
        header = """INSERT INTO flight(
            NAME,
            MASS,
            RADIUS,
            COLORR,
            COLORG,
            COLORB,
            POSX,
            POSY,
            VX,
            VY,
            ACCX,
            ACCY,
            ANGPOS,
            ANGV,
            ANGACC"""

        fields = """ VALUES(
            '%s',
            %f,
            %f,
            %d,
            %d,
            %d,
            %f,
            %f,
            %f,
            %f,
            %f,
            %f,
            %f,
            %f,
            %f"""

        values = (entity["name"],
                  entity["mass"],
                  entity["radius"],
                  entity["color"][0],
                  entity["color"][1],
                  entity["color"][2],
                  entity["displacement"][0],
                  entity["displacement"][1],
                  entity["velocity"][0],
                  entity["velocity"][1],
                  entity["acceleration"][0],
                  entity["acceleration"][1],
                  entity["angular position"],
                  entity["angular speed"],
                  entity["angular acceleration"])

        if type(entity) is Entity:
            header += ")"
            fields += ")"
        elif type(entity) is Habitat:
            header += ", FUEL, RCSFUEL)"
            fields += ", %f, %f)"
            values += (entity["main fuel"], entity["rcs fuel"],)

        try:
            db_cursor.execute((header + fields) % values)
            db.commit()
        except Exception as excp:
            print(excp, entity["name"])
            db.rollback()



