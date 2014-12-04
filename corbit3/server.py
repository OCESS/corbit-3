#!/bin/python3

__version__ = "3.0.0"
import corbit
from corbit.network import network
from corbit.physics import physics
from corbit.objects import objects
import scipy
import unum.units
import atexit
import time
import itertools
import math
import socket
import threading
import copy

print("Corbit SERVER " + __version__)

entities = []   # This object stores a list of all entities

time_acc_index = 0
time_acceleration = [1, 5, 10, 50, 100, 1000, 10000, 100000]
def time_per_tick():
    return time_acceleration[time_acc_index] / (60*unum.units.Hz)

G = 6.6720E-11 * unum.units.N*unum.units.m**2/unum.units.kg**2
PORT = 3141
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
            print("Malformed command, should have exactly one '|':",command)
        elif function == "fire_verniers":
            if len(argument.split(",")) != 2:
                print("Malformed argument, should have exactly one ',':",command)
            else:
                name, amount = argument.split(",")[0], float(argument.split(",")[1])
                corbit.oneshot_vernier_thrusters(
                    corbit.find_entity(name, entities), amount, time_per_tick())
        elif function == "change_engines":
            if len(argument.split(",")) != 2:
                print("Malformed argument, should have exactly one ',':",command)
            else:
                name, amount = argument.split(",")[0], float(argument.split(",")[1])
                corbit.find_entity(name, entities).main_engines.usage += amount

        elif function == "fire_rcs":
            if len(argument.split(",")) != 2:
                print("Malformed argument, should have exactly one ',':",command)
            else:
                name, direction = argument.split(",")[0], float(argument.split(",")[1])
                target = corbit.find_entity(name, entities)
                rcs_thrust = target.rcs.thrust(time_per_tick())
                theta = direction + target.angular_position
                rcs_thrust_vector = unum.units.N * scipy.array((math.cos(theta) * rcs_thrust.asNumber(),
                                                                math.sin(theta) * rcs_thrust.asNumber()))
                for angle in target.rcs.engine_positions:
                    target.accelerate(rcs_thrust_vector/len(target.rcs.engine_positions), angle)
        elif function == "accelerate_time":
            if len(argument.split(",")) != 1:
                print("Malformed argument, should have exactly no ',':",command)
            else:
                amount = int(argument)
                accelerate_time(amount)
        elif function == "open":
            if len(argument.split(",")) != 1:
                print("Malformed argument, should have exactly no ',':",command)
            else:
                filename = argument
                with open(filename, "r") as loadfile:
                    entities = corbit.data.load(loadfile)

with open("saves/OCESS.json", "r") as loadfile:
    entities = objects.load(loadfile)

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind((socket.gethostname(), PORT))
serversocket.listen(5)
pilot_commands = ""
# import socketserver
#
# class PilotingServer(socketserver.ThreadingTCPServer):
#     allow_reuse_address = True
#
# class PilotingServerHandler(socketserver.BaseRequestHandler):
#     def handle(self):
#         global pilot_commands
#         global entities
#         try:
#             pilot_commands = self.request.recv(1024).decode("UTF-8").strip()
#             print("got commands:", pilot_commands)
#             self.request.sendall(corbit.json_serialize(entities).encode("UTF-8"))
#         except Exception as e:
#             print("Exception on piloting connection", e)
#
# piloting_server = PilotingServer((ADDRESS, PORT), PilotingServerHandler)
# piloting_server_thread = threading.Thread(target = piloting_server.serve_forever)
# piloting_server_thread.start()
pilot_commands_lock = threading.Lock()
def piloting_server():
    global pilot_commands
    global pilot_commands_lock
    global entities

    print("listening for pilot connection")
    pilot_socket, addr = serversocket.accept()
    print("Connection from pilot", addr)
    while True:
        # print("loop")
        pilot_commands_lock.acquire()
        pilot_commands = network.recvall(pilot_socket)
        pilot_commands_lock.release()
        # print("got commands:", pilot_commands)
        if not network.sendall(objects.json_serialize(entities), pilot_socket):
            print("relistening for pilot connection")
            pilot_socket, addr = serversocket.accept()
            print("Connection from pilot", addr)

piloting_server_thread = threading.Thread(target = piloting_server)
piloting_server_thread.start()

def exit_handler():
    serversocket.close()
    atexit.register(exit_handler)

ticks_to_simulate = 1
def ticker():
    global ticks_to_simulate
    ticks_to_simulate += 1
    threading.Timer(time_per_tick().asNumber(unum.units.s), ticker).start()

ticker()


while True:

    start_time = time.time()

    #    for A, B in itertools.combinations(entities, 2):
    #        gravity = corbit.gravitational_force(A, B)
    #        theta = angle(A, B)
    #        A.accelerate(gravity, theta)
    #        B.accelerate(-gravity, theta)

    collisions = []
    for A, B in itertools.combinations(entities, 2):
        affected_objects = physics.resolve_collision(A, B, time_per_tick())
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
        pass    # Skip acting on commands for this tick
    if pilot_commands_copy != "":
        print(pilot_commands_copy)
        act_on_piloting_commands(pilot_commands_copy.split(" "))


    ticks_to_simulate -= 1  # ticks_to_simulate is incremented in the ticker() function every tick
    if ticks_to_simulate <= 0:
        # The 0.8 is in there because time.time() isn't accurate, and it's better to overshoot than undershoot
        time.sleep(time_per_tick().asNumber(unum.units.s) - 0.8 * (time.time() - start_time))
        #todo sleep time must be non-negative sometimes fails


print("okay")

exit_handler()
