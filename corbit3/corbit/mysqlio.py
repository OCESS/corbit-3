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
    mass = json_object["mass"]
    #print(name, "mass", mass)
    radius = json_object["radius"]
    #print(name, "radius", radius)
    displacement = json_object["displacement"]
    #print(name, "displacement", displacement)
    velocity = json_object["velocity"]
    #print(name, "velocity", velocity)
    acceleration = json_object["acceleration"]
    #print(name, "acceleration", acceleration)
    angular_position = json_object["angular position"]
    #print(name, "angular position", angular_position)
    angular_speed = json_object["angular speed"]
    #print(name, "angular speed", angular_speed)
    angular_acceleration = json_object["angular acceleration"]
    #print(name, "angular acceleration", angular_acceleration)
    return (color, mass, radius, displacement, velocity, acceleration,
            angular_position, angular_speed, angular_acceleration)

def load_json(input_stream):
    """Given a JSON string or a JSON stream of entities, parses into binary and returns
    :param input_stream: string or stream of Corbit format to parse
    :return: a list of entities
    """
    entity_guid = 0
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
                json_entities.append(
                    Entity(name, mass, radius, color, displacement, velocity, acceleration, angular_position,
                           angular_speed, angular_acceleration))
                entity_guid += 1
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
                main_fuel = habitat["main fuel"]
                rcs_fuel = habitat["rcs fuel"]
                json_entities.append(
                    Habitat(name, mass, radius, color, displacement, velocity, acceleration, angular_position,
                            angular_speed, angular_acceleration, main_fuel, rcs_fuel))
                entity_guid += 1
            except KeyError:
                print("habitat " + name + " has undefined elements, skipping...")
                break
    except KeyError:
        print("no habitats found")

    return json_entities


db_cursor = None
db = None
def flush_db(entities, db_info):
    global db
    global db_cursor
    try:
        print(db_info)
        db = msd.connect(*db_info)
        db_cursor = db.cursor()
    except:
        db = msd.connect(*(db_info[:-1]))
        db_cursor = db.cursor()
        db_cursor.execute("CREATE DATABASE corbit")
        db_cursor.execute("USE corbit")
    # TODO: in the future, if you want to implement a "restore previous state" option, like what orbit has right now,
    # you can just not run this function, and then and then load whatever is in
    db_cursor.execute("DROP TABLE IF EXISTS flight")
    db_cursor.execute("""CREATE TABLE flight (
        TYPE CHAR(64) NOT NULL, NAME CHAR(64) NOT NULL, MASS DOUBLE NOT NULL, RADIUS DOUBLE NOT NULL,
        COLORR INT NOT NULL, COLORG INT NOT NULL, COLORB INT NOT NULL,
        POSX DOUBLE NOT NULL, POSY DOUBLE NOT NULL, VX DOUBLE NOT NULL, VY DOUBLE NOT NULL,
        ACCX DOUBLE NOT NULL, ACCY DOUBLE NOT NULL,
        ANGPOS DOUBLE NOT NULL, ANGV DOUBLE NOT NULL, ANGACC DOUBLE NOT NULL,
        FUEL DOUBLE, RCSFUEL DOUBLE)""")
    db_cursor.execute("DROP TABLE IF EXISTS flightcommands")
    db_cursor.execute("""CREATE TABLE flightcommands ( COMMAND CHAR(64) NOT NULL, TARGET CHAR(64), AMOUNT DOUBLE)""")
    db.commit()

def connect_to_db(db_info):
    global db
    db = msd.connect(*db_info)
    global db_cursor
    db_cursor = db.cursor()


def push_entities(entities):
    list_of_values = []
    sql_code = """INSERT INTO flight(
            TYPE, NAME, MASS, RADIUS, COLORR, COLORG, COLORB, POSX, POSY, VX, VY, ACCX, ACCY, ANGPOS, ANGV, ANGACC, FUEL, RCSFUEL)
            VALUES"""
    for entity in entities:
        fields = """ (
            '%s', '%s', %f,   %f,     %d,     %d,     %d,     %f,   %f,   %f, %f, %f,   %f,   %f,     %f,   %f,     %f,   %f),"""

        values = (entity.name,
                  entity.mass_fun().asNumber(kg),
                  entity.radius.asNumber(m),
                  entity.color[0],
                  entity.color[1],
                  entity.color[2],
                  entity.displacement[0].asNumber(m),
                  entity.displacement[1].asNumber(m),
                  entity.velocity[0].asNumber(m/s),
                  entity.velocity[1].asNumber(m/s),
                  entity.acceleration[0].asNumber(m/s/s),
                  entity.acceleration[1].asNumber(m/s/s),
                  entity.angular_position.asNumber(rad),
                  entity.angular_speed.asNumber(rad/s),
                  entity.angular_acceleration.asNumber(rad/s/s))
        if type(entity) is Entity:
            values = ("entity",) + values
            values += (0,0,)
        else:
            values = ("habitat",) + values
            values += (entity.engine_system.fuel.asNumber(kg), entity.rcs_system.fuel.asNumber(kg),)
        sql_code += fields % values
    try:
        sql_code = sql_code[:-1] # removes the last ","
        db_cursor.execute("TRUNCATE TABLE flight")
        db_cursor.execute(sql_code)
        db.commit()
    except Exception as excp:
        print(sql_code)
        print("HELP", excp, entity.name)
        db.rollback()

def get_entities():
    db_cursor.execute("SELECT * FROM flight")
    sql_object = db_cursor.fetchall()
    db.commit()
    retrieved_entities = []
    for entity in sql_object:
        # sorry for not being able to access fields in a clearer manner, but here's a conversion list
        # that is true, but everything just comes in the order that the columns are in:
        # TYPE, NAME, MASS, RADIUS, COLORR, COLORG, COLORB, POSX, POSY, VX, VY, ACCX, ACCY, ANGPOS, ANGV, ANGACC,
        # (FUEL, RCSFUEL)
        if entity[0] == "entity":
            retrieved_entities.append(
                Entity(entity[1], entity[2], entity[3], (entity[4], entity[5], entity[6]), [entity[7], entity[8]],
                       [entity[9], entity[10]], [entity[11], entity[12]], entity[13], entity[14], entity[15]))
        elif entity[0] == "habitat":
            retrieved_entities.append(
                Habitat(entity[1], entity[2], entity[3], (entity[4], entity[5], entity[6]), [entity[7], entity[8]],
                        [entity[9], entity[10]], [entity[11], entity[12]], entity[13], entity[14], entity[15],
                        entity[16], entity[17]))
    return retrieved_entities

def push_commands(list_of_commands):
    for comm in list_of_commands:
        values = "VALUES('%s'"
        try:
            if type(comm[1]) is str:
                values += ", %s"
            if type(comm[2]) is float:
                values += ", %f"
        except IndexError:
            pass
        values += ")"
        db_cursor.execute("INSERT INTO flightcommands(COMMAND, TARGET, AMOUNT) " + values)
        db.commit()

def pop_commands():
    commands = []
    try:
        db_cursor.execute("SELECT * FROM pilotcommands")
        commands = db_cursor.fetchall()
        db_cursor.execute("TRUNCATE TABLE pilotcommands")
        db.commit()
    except:
        db.rollback()
    return commands
