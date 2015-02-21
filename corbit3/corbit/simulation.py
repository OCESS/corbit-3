# simulation.py

import itertools


def simulate_tick(dt, entities):
    for A, B in itertools.combinations(entities, 2):
        gravity = 5
        theta = 5
        A.accelerate(gravity, theta)
        B.accelerate(-gravity, theta)

    collisions = []
    for A, B in itertools.combinations(entities, 2):
        affected_objects = []
        if affected_objects is not None:
            collisions += affected_objects

    for entity in entities:
        already_moved = False
        for name in collisions:
            if entity.name == name:
                already_moved = True

        if not already_moved:
            entity.move(dt)

