#!/bin/python3

__version__ = "3.0.0"
from corbit.physics import physics
from corbit.objects import objects
from corbit.network import network
import sys      # used to exit the program
import pygame   # used for drawing and a couple other things
import pygame.locals as gui # so I don't have to type out KB_LEFT, etc
import unum.units
import scipy
import math
import socket                   # used to communicate with the server
import time

print("Corbit PILOT " + __version__)
fps = 60 * unum.units.Hz
entities = []                   # this list will store all the entities
PORT = 3141

# just setting up the display and window here
screen_size = (681, 745)
pygame.init()
clock = pygame.time.Clock()
display_flags = gui.RESIZABLE
screen = pygame.display.set_mode(screen_size, display_flags)
pygame.display.set_caption("Corbit " + __version__)
pygame.key.set_repeat(800,25)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(8)
connection_established = False
while not connection_established is None:
    print("Connecting to server...")
    print(connection_established)
    try:
        connection_established = sock.connect((socket.gethostname(), PORT))
    except (ConnectionRefusedError, ConnectionAbortedError) as e:
        print(e)
        print("Could not connect to server, retrying...")
        time.sleep(1)

camera = objects.Camera(1, "AC")

def print_text(text, font, gap, line_number, display):
    try:
        round(text, 1)
    except TypeError:
        pass
    label = font.render(text, 1, (200,200,200))
    display.blit(label, (gap[0], gap[1] * line_number))
    return line_number + 1

def draw(display):
    line_number = 1
    gap = [10,10]
    pygame.draw.circle(display, (150,150,150), (10,10), 10)
    display_font = pygame.font.SysFont("monospace", 15)

    alt = physics.altitude(objects.find_entity("AC", entities),
                           objects.find_entity("AC A", entities)).asNumber(unum.units.m)
    alt_text = str(physics.altitude(
        objects.find_entity("AC", entities),
        objects.find_entity("AC A", entities)))
    line_number = print_text(alt_text, display_font, gap, line_number, display)


while True:

    commands_to_send = ""

    for event in pygame.event.get():
        if event.type == gui.QUIT:
            sys.exit()
            if event.type == gui.VIDEORESIZE:
                screen_size = event.dict["size"]
                screen = pygame.display.set_mode(screen_size, display_flags)
                print(screen_size)
                if pygame.key.get_focused() and event.type == gui.KEYDOWN:
                    if event.unicode == "\t":
                        camera.locked = not camera.locked
                        print("locked=",camera.locked)
                    elif event.key == gui.K_LEFT:
                        camera.pan(unum.units.m/unum.units.s/unum.units.s * scipy.array((-1, 0)))
                    elif event.key == gui.K_RIGHT:
                        camera.pan(unum.units.m/unum.units.s/unum.units.s * scipy.array((1, 0)))
                    elif event.key == gui.K_UP:
                        camera.pan(unum.units.m/unum.units.s/unum.units.s * scipy.array((0, 1)))
                    elif event.key == gui.K_DOWN:
                        camera.pan(unum.units.m/unum.units.s/unum.units.s * scipy.array((0, -1)))

                    elif event.unicode == "a":
                        commands_to_send += "fire_verniers|AC,-1 "
                    elif event.unicode == "d":
                        commands_to_send += "fire_verniers|AC,1 "
                    elif event.unicode == "w":
                        commands_to_send += "change_engines|AC,0.01 "
                    elif event.unicode == "s":
                        commands_to_send += "change_engines|AC,-0.01 "

                    elif event.unicode == "W":
                        commands_to_send += "fire_rcs|AC,0 "
                    elif event.unicode == "A":
                        commands_to_send += "fire_rcs|AC," + str(math.pi/2) + " "
                    elif event.unicode == "S":
                        commands_to_send += "fire_rcs|AC," + str(math.pi) + " "
                    elif event.unicode == "D":
                        commands_to_send += "fire_rcs|AC," + str(-math.pi/2) + " "

                    elif event.unicode == "-":
                        camera.zoom(-0.1)
                    elif event.unicode == "+":
                        camera.zoom(0.1)

                    elif event.unicode == ".":
                        commands_to_send += "accelerate_time|1 "
                    elif event.unicode == ",":
                        commands_to_send += "accelerate_time|-1 "

                    elif event.unicode == "r":
                        commands_to_send += "open|saves/OCESS.json "

    print(commands_to_send)
    print(sock)
    network.sendall(commands_to_send.strip(), sock)

    entities = objects.load(network.recvall(sock))

    camera.move(1/fps)
    camera.update(objects.find_entity(camera.center, entities))

    ## Drawing routines here
    for entity in entities:
        # calculating the on-screen position
        screen_position = \
            [int(
                camera.zoom_level *
                (entity.displacement - camera.displacement).asNumber()[0]
                + screen_size[0]/2),
                int(
                    camera.zoom_level * (entity.displacement - camera.displacement).asNumber()[1]
                    + screen_size[1]/2) ]
        # calculating the on-screen radius
        screen_radius = int(entity.radius.asNumber() * camera.zoom_level)

        if type(entity) == objects.Entity:
            # entity drawing is the simplest, just a circle
            pygame.draw.circle(screen, entity.color, screen_position, screen_radius)
        elif type(entity) == objects.Habitat:
            # habitat is the entity drawing, but with a line pointing forwards
            pygame.draw.circle(screen, entity.color,
                               screen_position, screen_radius)
            pygame.draw.aaline(screen, (0, 255, 0), screen_position,
                               [int(screen_position[0] + screen_radius * math.cos(entity.angular_position)),
                                int(screen_position[1] + screen_radius * math.sin(entity.angular_position))])


    # flip the screen upside down, so that y values increase upwards
    screen.blit(pygame.transform.flip(screen, False, True), (0, 0))
    draw(screen)
    pygame.display.flip()
    screen.fill((0, 0, 0))

    #time.sleep(1/fps.asNumber(Hz))
    # time.sleep(1/fps.asNumber(Hz) - time_spent_on_last_frame)
    sock.close()