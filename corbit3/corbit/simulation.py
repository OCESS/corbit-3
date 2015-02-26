# simulation.py

import itertools
import corbit.physics

def simulate_tick(dt, entities):
    for A, B in itertools.combinations(entities, 2):
        gravity = corbit.physics.gravitational_force(A, B)
        theta = corbit.physics.angle(A, B)
        A.accelerate(gravity, theta)
        B.accelerate(-gravity, theta)

    collisions = []
    for A, B in itertools.combinations(entities, 2):
        affected_objects = corbit.physics.resolve_collision(A, B, dt)
        if affected_objects is not None:
            collisions += affected_objects

    for entity in entities:
        already_moved = False
        for name in collisions:
            if entity.name == name:
                already_moved = True

        if not already_moved:
            entity.move(dt)

