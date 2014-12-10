#!/bin/python3
#todo: twisted appropriate for this?

__version__ = "3.0.0"
import corbit.network
import corbit.physics
import corbit.objects
import scipy
import unum.units as un
import time
import itertools
import math
import socket
import threading
import copy

print("Corbit SERVER " + __version__)

entities = []  # This object stores a list of all entities

time_acc_index = 0
time_acceleration = [1, 5, 10, 50, 100, 1000, 10000, 100000]


def time_per_tick():
    return time_acceleration[time_acc_index] / (60 * un.Hz)


G = 6.6720E-11 * un.N * un.m ** 2 / un.kg ** 2
PORT = 3415
ADDRESS = "localhost"


def accelerate_time(amount):
    "Increases how much time is simulated per tick of the server program"
    global time_acc_index
    global time_acceleration

    if time_acc_index + amount < 0:
        return
    try:
        time_acceleration[time_acc_index + amount]
        print(time_acc_index + amount)
    except IndexError:
        return

    time_acc_index += amount


def act_on_piloting_commands(commands):
    global entities

    for command in pilot_commands_copy.split(" "):
        function, argument = command.split("|")[0], command.split("|")[1]
        if len(command.split("|")) != 2:
            print("Malformed command, should have exactly one '|':", command)
        elif function == "fire_verniers":
            if len(argument.split(",")) != 2:
                print("Malformed argument, should have exactly one ',':", command)
            else:
                name, amount = argument.split(",")[0], float(argument.split(",")[1])
                corbit.objects.oneshot_vernier_thrusters(
                    corbit.objects.find_entity(name, entities), amount, time_per_tick())
        elif function == "change_engines":
            if len(argument.split(",")) != 2:
                print("Malformed argument, should have exactly one ',':", command)
            else:
                name, amount = argument.split(",")[0], float(argument.split(",")[1])
                corbit.objects.find_entity(name, entities).main_engines.usage += amount

        elif function == "fire_rcs":
            if len(argument.split(",")) != 2:
                print("Malformed argument, should have exactly one ',':", command)
            else:
                name, direction = argument.split(",")[0], float(argument.split(",")[1])
                target = corbit.objects.find_entity(name, entities)
                rcs_thrust = target.rcs.thrust(time_per_tick())
                theta = direction + target.angular_position
                rcs_thrust_vector = un.N * scipy.array((math.cos(theta) * rcs_thrust.asNumber(),
                                                        math.sin(theta) * rcs_thrust.asNumber()))
                for angle in target.rcs.engine_positions:
                    target.accelerate(rcs_thrust_vector / len(target.rcs.engine_positions), angle)
        elif function == "accelerate_time":
            if len(argument.split(",")) != 1:
                print("Malformed argument, should have exactly no ',':", command)
            else:
                amount = int(argument)
                accelerate_time(amount)
        elif function == "open":
            if len(argument.split(",")) != 1:
                print("Malformed argument, should have exactly no ',':", command)
            else:
                filename = argument
                with open(filename, "r") as loadfile:
                    entities = corbit.objects.load(loadfile)


with open("saves/OCESS.json", "r") as loadfile:
    entities = corbit.objects.load(loadfile)

pilot_commands = ""
pilot_commands_lock = threading.Lock()


def piloting_server():
    global pilot_commands
    global pilot_commands_lock
    global entities
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((socket.gethostname(), PORT))
    serversocket.listen(5)

    print("listening for pilot connection")
    pilot_socket, addr = serversocket.accept()
    print("Connection from pilot", addr)
    while True:
        # print("loop")
        pilot_commands_lock.acquire()
        pilot_commands = corbit.network.recvall(pilot_socket)
        pilot_commands_lock.release()
        print("got commands:", pilot_commands)
        if not corbit.network.sendall(corbit.objects.json_serialize(entities), pilot_socket):
            print("relistening for pilot connection")
            serversocket.close()
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serversocket.bind((socket.gethostname(), PORT))
            serversocket.listen(5)
            pilot_socket, addr = serversocket.accept()
            print("Connection from pilot", addr)
        else:
            pass


piloting_server_thread = threading.Thread(target=piloting_server)
piloting_server_thread.start()

ticks_to_simulate = 1


def ticker():
    global ticks_to_simulate
    ticks_to_simulate += 1
    threading.Timer(time_per_tick().asNumber(un.s), ticker).start()
ticker()

while True:
    start_time = time.time()

    # for A, B in itertools.combinations(entities, 2):
    # gravity = corbit.physics.gravitational_force(A, B)
    #        theta = angle(A, B)
    #        A.accelerate(gravity, theta)
    #        B.accelerate(-gravity, theta)

    collisions = []
    for A, B in itertools.combinations(entities, 2):
        affected_objects = corbit.physics.resolve_collision(A, B, time_per_tick())
        if affected_objects != None:
            collisions += affected_objects

    for entity in entities:
        already_moved = False
        for name in collisions:
            if entity.name == name:
                already_moved = True

        if not already_moved:
            entity.move(time_per_tick())

    # Only wait until this tick is almost done and there is nothing left to do
    pilot_commands_copy = ""
    if pilot_commands_lock.acquire():
        pilot_commands_copy = copy.copy(pilot_commands)
        pilot_commands_lock.release()
    else:
        pass  # Skip acting on commands for this tick
    if pilot_commands_copy != "":
        print(pilot_commands_copy)
        act_on_piloting_commands(pilot_commands_copy.split(" "))

    ticks_to_simulate -= 1  # ticks_to_simulate is incremented in the ticker() function every tick
    if ticks_to_simulate <= 0:
        time.sleep(max(time_per_tick().asNumber(un.s) - (time.time() - start_time),
                       0))


