#! /usr/bin/env python3

__version__ = "3.0.0"
import corbit.network
import corbit.physics
import corbit.objects
import corbit.mysqlio
import scipy
import unum.units as un
import time
import itertools
import math
import socket
import threading
import copy

print("Corbit SERVER " + __version__)

entities = []  # This object stores a list of all entities and children of entities.
G = 6.6720E-11 * un.N * un.m ** 2 / un.kg ** 2
ADDRESS = "localhost"
time_acc_index = 0
ticks_per_second = 30 * un.Hz # also see: time_per_tick()
time_acceleration = [1, 5, 10, 50, 100, 1000, 10000, 100000] # used in time_per_tick()

with open("saves/OCESS.json", "r") as loadfile:
    entities = corbit.mysqlio.load_json(loadfile)
corbit.mysqlio.flush_db(entities, (ADDRESS, "root", "3.1415pi", "corbit"))


def time_per_tick():
    return time_acceleration[time_acc_index] / ticks_per_second


def accelerate_time(amount):
    "Increases how much time is simulated per tick of the server program"
    global time_acc_index
    global time_acceleration

    if time_acc_index + amount < 0:
        return
    try:
        print("New timestep:", str(time_acceleration[time_acc_index + amount]))
    except IndexError:
        return

    time_acc_index += amount


def act_on_piloting_commands(commands):
    global entities

    for command in commands:
        function, target, amount = command
        if function == "fire verniers":
            corbit.objects.oneshot_vernier_thrusters(
                corbit.objects.find_entity(name, entities), amount, time_per_tick())
        elif function == "change_engines":
            corbit.objects.find_entity(name, entities).main_engines.usage += amount
        elif function == "fire_rcs":
            direction = amount
            target_entity = corbit.objects.find_entity(target, entities)
            rcs_thrust = target.rcs.thrust(time_per_tick())
            theta = direction + target.angular_position
            rcs_thrust_vector = un.N * scipy.array((math.cos(theta) * rcs_thrust.asNumber(),
                                                    math.sin(theta) * rcs_thrust.asNumber()))
            for angle in target.rcs.engine_positions:
                target.accelerate(rcs_thrust_vector / len(target.rcs.engine_positions), angle)
        elif function == "accelerate_time":
                accelerate_time(int(amount))
        elif function == "open":
                filename = target
                with open(filename, "r") as loadfile:
                    entities = corbit.mysqlio.load_json(loadfile)

ticks_to_simulate = 1
def ticker():
    global ticks_to_simulate
    ticks_to_simulate += 1
    threading.Timer(time_per_tick().asNumber(un.s), ticker).start()

ticker()

while True:
    if ticks_to_simulate <= 0:
        act_on_piloting_commands(corbit.mysqlio.pop_commands())
    else:
        start_time = time.time()

        corbit.mysqlio.push_entities(entities)

        for A, B in itertools.combinations(entities, 2):
            gravity = corbit.physics.gravitational_force(A, B)
            theta = corbit.physics.angle(A, B)
            A.accelerate(gravity, theta)
            B.accelerate(-gravity, theta)

        collisions = []
        for A, B in itertools.combinations(entities, 2):
            affected_objects = corbit.physics.resolve_collision(A, B, time_per_tick())
            if affected_objects is not None:
                collisions += affected_objects

        for entity in entities:
            already_moved = False
            for name in collisions:
                if entity.name == name:
                    already_moved = True

            if not already_moved:
                entity.move(time_per_tick())

        ticks_to_simulate -= 1  # ticks_to_simulate is incremented in the ticker() function every tick
        if ticks_to_simulate <= 0:
            time.sleep(max(time_per_tick().asNumber(un.s) - (time.time() - start_time),
                           0))
