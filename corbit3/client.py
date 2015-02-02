#! /usr/bin/env python3

__version__ = "3.0.0"
import corbit.physics
import corbit.objects
import corbit.network
import corbit.mysqlio
import sys  # used to exit the program
import pygame  # used for drawing and a couple other things
import pygame.locals as gui  # for things like KB_LEFT
import unum
import unum.units as un
import scipy
import numpy.linalg as LA
import math

import pygame.gfxdraw
print("Corbit PILOT " + __version__)
fps = 60 * un.Hz
entities = []  # this list will store all the entities
ADDRESS = "localhost"
print("alright come over her")
corbit.mysqlio.connect_to_db((ADDRESS, "root", "3.1415pi", "corbit"))
print("hey what are u doing")


# just setting up the display and window here
screen_size = (681, 745)
pygame.init()
clock = pygame.time.Clock()
display_flags = gui.RESIZABLE
pygame.HWSURFACE = pygame.DOUBLEBUF = True  # wait for the screen to refresh before flipping the screen
screen = pygame.display.set_mode(screen_size, display_flags)
pygame.display.set_caption("Corbit " + __version__)
pygame.key.set_repeat(800, 25)

camera = corbit.objects.Camera(0.0001, corbit.objects.center)
screen_size = screen.get_size()
screen = pygame.display.set_mode(screen_size, display_flags)
#TODO: I'm trying to set the default format string, but I haven't found the right variable to change yet
unum.Unum.VALUE_FORMAT = "%8.2f"



def draw(display):
    for entity in entities:
        # calculating the on-screen position
        screen_position =  [int(
                camera.zoom_level *
                (entity.displacement - camera.displacement).asNumber()[0]
                + screen_size[0] / 2),
                int(
                 camera.zoom_level * (entity.displacement - camera.displacement).asNumber()[1]
                 + screen_size[1] / 2)]
        # calculating the on-screen radius
        screen_radius = int(entity.radius.asNumber() * camera.zoom_level)

        #circle_distance = [0, 0]
        #circle_distance[0] = abs(screen_position[0] - screen_size[0])
        #circle_distance[1] = abs(screen_position[1] - screen_size[1])

        #if circle_distance[0] > (screen_size[0]/2 + screen_radius):
        #    if entity.name == "Earth":
        #        print("poof")
        #    continue
        #if circle_distance[1] > (screen_size[1]/2 + screen_radius):
        #    if entity.name == "Earth":
        #        print("poof")
        #    continue

        #corner_distance_sq = (circle_distance[0] - screen_size[0]/2)**2 +\
        #(circle_distance[1] - screen_size[1]/2)**2

        #if (circle_distance[0] > screen_size[0]/2) or\
        #        (circle_distance[1] > screen_size[1]/2) or\
        #        (corner_distance_sq > screen_radius**2):
        #    pass

        if type(entity) == corbit.objects.Entity:
            # entity drawing is the simplest, just a circle
            #print("circle drawing", entity.name, screen_position, screen_radius)
            pygame.draw.circle(screen, entity.color, screen_position, screen_radius)
        elif type(entity) == corbit.objects.Habitat:
            # habitat is the entity drawing, but with a line pointing forwards
            #print("circle drawing", entity.name, screen_position, screen_radius)
            pygame.draw.circle(screen, entity.color, screen_position, screen_radius)
            pygame.draw.aaline(screen, (0, 255, 0), screen_position,
                               [int(screen_position[0] + screen_radius * math.cos(entity.angular_position)),
                                int(screen_position[1] + screen_radius * math.sin(entity.angular_position))])

    # test big circle drawing
    #pygame.draw.circle(screen, (0, 255, 0), (int(-1e7+500), 0), int(1e7))
    #pygame.gfxdraw.line(screen, 0, 0, 500, 700, (255, 0, 0))

    # flip the screen upside down, so that y values increase upwards like on a cartesian plane
    screen.blit(pygame.transform.flip(screen, False, True), (0, 0))

    # This is where the magic HUD drawing hapen
    # TODO: can never hurt to add more
    def print_text(text, line_number, padding, display):
        gap = [10, 10]
        font = pygame.font.SysFont("monospace", 15)
        display.blit(font.render(text[0], 1, (100, 100, 100)), # field name
                     (gap[0], gap[1] * 2 * line_number))
        display.blit(font.render(text[1], 1, (200, 200, 200)), # field value
                     (gap[0] + padding*10, gap[1] * 2 * line_number)) # padding*10 ensures a constant distance
                                                                      # between the field name and the field value
        return line_number + 1

    lines_to_draw = \
    [("Altitude:",
      corbit.physics.altitude(corbit.objects.find_entity(corbit.objects.control, entities),
                              corbit.objects.find_entity(corbit.objects.reference, entities)).__str__()),
     ("Speed:",
      corbit.physics.speed(corbit.objects.find_entity(corbit.objects.control, entities),
                           corbit.objects.find_entity(corbit.objects.reference, entities)).__str__()),
     ("Acceleration:",
      (un.m/un.s/un.s *
       LA.norm((corbit.objects.find_entity(corbit.objects.control, entities).acceleration -
                corbit.physics.gravitational_force(corbit.objects.find_entity(corbit.objects.control, entities),
                                                   corbit.objects.find_entity(corbit.objects.reference, entities))
                /corbit.objects.find_entity(corbit.objects.control, entities).mass_fun()).asNumber(un.m/un.s/un.s))).__str__()),
     ("Rotation:",
      corbit.objects.find_entity(corbit.objects.control, entities).angular_speed.__str__()),
     ("Torque:",
      corbit.objects.find_entity(corbit.objects.control, entities).angular_acceleration.__str__()),
     ("",""),
     ("Orbital Speed:",
      corbit.physics.Vorbit(corbit.objects.find_entity(corbit.objects.control, entities),
                            corbit.objects.find_entity(corbit.objects.reference, entities)).__str__()),
     ("Periapsis:",
      corbit.physics.periapsis(corbit.objects.find_entity(corbit.objects.control, entities),
                               corbit.objects.find_entity(corbit.objects.reference, entities)).__str__()),
     ("Apoapsis:",
      corbit.physics.apoapsis(corbit.objects.find_entity(corbit.objects.control, entities),
                               corbit.objects.find_entity(corbit.objects.reference, entities)).__str__()),
     ("",""),
     ("Fuel:",
      corbit.objects.find_entity(corbit.objects.control, entities).engine_system.fuel.__str__()),
     ("Zoom:",
      camera.zoom_level.__str__())
    ]

    line_number = 0
    field_padding = 2 + max([len(i[0]) for i in lines_to_draw])

    for text in lines_to_draw:
        line_number = print_text(text, line_number, field_padding, display)

while True:
    while not entities:
        entities = corbit.mysqlio.get_entities()

    # commands_to_send is a : list of (COMMAND, TARGET, AMOUNT) 3-tuples
    # of type                         (string,  string, float)
    # whenever a command is appended, that command is written to the corbit.flightcommands table
    # where the server checks for a command and acts on it
    commands_to_send = []

    for event in pygame.event.get():
        if event.type == gui.QUIT:
            sys.exit()

        if event.type == gui.VIDEORESIZE:
            screen_size = event.dict["size"]
            print(event.dict["size"])
            screen = pygame.display.set_mode(screen_size, display_flags)
            print(screen_size)

        if pygame.key.get_focused() and event.type == gui.KEYDOWN:
            if event.unicode == "\t":
                camera.locked = not camera.locked
                print("locked=", camera.locked)
            elif event.key == gui.K_LEFT:
                camera.pan(un.m / un.s / un.s * scipy.array((-1, 0)))
            elif event.key == gui.K_RIGHT:
                camera.pan(un.m / un.s / un.s * scipy.array((1, 0)))
            elif event.key == gui.K_UP:
                camera.pan(un.m / un.s / un.s * scipy.array((0, 1)))
            elif event.key == gui.K_DOWN:
                camera.pan(un.m / un.s / un.s * scipy.array((0, -1)))
            elif event.unicode == "a":
                commands_to_send += "fire_verniers|AC,-1 "
                commands_to_send.append(("fire verniers", "AC", -1))
            elif event.unicode == "d":
                commands_to_send.append(("fire_verniers", "AC", 1))
            elif event.unicode == "w":
                commands_to_send.append(("change_engines", "AC", 0.01))
            elif event.unicode == "s":
                commands_to_send.append(("change_engines", "AC", -0.01))
            elif event.unicode == "W":
                commands_to_send.append(("fire_rcs", "AC", 0))
            elif event.unicode == "A":
                commands_to_send.append(("fire_rcs", "AC", str(math.pi / 2)))
            elif event.unicode == "S":
                commands_to_send.append(("fire_rcs", "AC", str(math.pi)))
            elif event.unicode == "D":
                commands_to_send.append(("fire_rcs", "AC", str(-math.pi / 2)))
            elif event.unicode == "-":
                camera.zoom(-0.1)
            elif event.unicode == "+":
                camera.zoom(0.1)
            elif event.unicode == ".":
                commands_to_send.append(("accelerate_time", 1,))
            elif event.unicode == ",":
                commands_to_send.append(("accelerate_time", -1,))
            elif event.unicode == "r":
                commands_to_send.append(("open", "saves/OCESS.json",))

    if commands_to_send:
        print(commands_to_send)
        corbit.mysqlio.push_commands(commands_to_send)

    camera.move(1/fps)
    #print(corbit.objects.find_entity("Sun", entities))
    print(camera.center)
    camera.update(corbit.objects.find_entity(camera.center, entities))

    draw(screen)
    pygame.display.flip()
    screen.fill((0, 0, 0))

    # time.sleep(1/fps.asNumber(Hz))
    # time.sleep(1/fps.asNumber(Hz) - time_spent_on_last_frame)
