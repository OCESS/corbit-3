#! /usr/bin/env python3


__version__ = "3.0.0"
import corbit.physics
import corbit.objects
import corbit.network
import sys  # used to exit the program
import pygame  # used for drawing and a couple other things
import pygame.locals as gui  # for things like KB_LEFT
import unum
import unum.units as un
import scipy
import numpy.linalg as LA
import math
import socket  # used to communicate with the server
import time

print("Corbit PILOT " + __version__)
fps = 60 * un.Hz
entities = []  # this list will store all the entities
PORT = 3415

# just setting up the display and window here
screen_size = (681, 745)
pygame.init()
clock = pygame.time.Clock()
display_flags = gui.RESIZABLE
pygame.HWSURFACE = pygame.DOUBLEBUF = True  # wait for the screen to refresh before flipping the screen
screen = pygame.display.set_mode(screen_size, display_flags)
pygame.display.set_caption("Corbit " + __version__)
pygame.key.set_repeat(800, 25)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(8)
connection_established = False
while not connection_established is None:
    print("Connecting to server...")
    try:
        connection_established = sock.connect((socket.gethostname(), PORT))
    except (ConnectionRefusedError, ConnectionAbortedError) as e:
        print(e)
        print("Could not connect to server, retrying...")
        time.sleep(1)

camera = corbit.objects.Camera(1, "AC")
screen_size = screen.get_size()
unum.Unum.VALUE_FORMAT = "%8.2f"

def draw(display):
    for entity in entities:
        # calculating the on-screen position
        screen_position = \
            [int(
                camera.zoom_level *
                (entity.displacement - camera.displacement).asNumber()[0]
                + screen_size[0] / 2),
             int(
                 camera.zoom_level * (entity.displacement - camera.displacement).asNumber()[1]
                 + screen_size[1] / 2)]
        # calculating the on-screen radius
        screen_radius = int(entity.radius.asNumber() * camera.zoom_level)

        if type(entity) == corbit.objects.Entity:
            # entity drawing is the simplest, just a circle
            pygame.draw.circle(screen, entity.color, screen_position, screen_radius)
        elif type(entity) == corbit.objects.Habitat:
            # habitat is the entity drawing, but with a line pointing forwards
            pygame.draw.circle(screen, entity.color,
                               screen_position, screen_radius)
            pygame.draw.aaline(screen, (0, 255, 0), screen_position,
                               [int(screen_position[0] + screen_radius * math.cos(entity.angular_position)),
                                int(screen_position[1] + screen_radius * math.sin(entity.angular_position))])

    # flip the screen upside down, so that y values increase upwards like on a cartesian plane
    screen.blit(pygame.transform.flip(screen, False, True), (0, 0))

    # This is where the magic HUD drawing hapen
    def print_text(text, line_number, display):
        gap = [10, 10]
        font = pygame.font.SysFont("monospace", 15)
        display.blit(font.render(text, 1, (200, 200, 200)),
                     (gap[0], gap[1] * 2 *line_number))
        return line_number + 1

    lines_to_draw = ["Altitude: " + corbit.physics.altitude(corbit.objects.find_entity("AC", entities),
                                                            corbit.objects.find_entity("AC A", entities)).__str__(),
                     "Speed: " + corbit.physics.speed(corbit.objects.find_entity("AC", entities),
                                                      corbit.objects.find_entity("AC A", entities)).__str__(),
                     "Acceleration: " + (un.m/un.s/un.s * LA.norm((corbit.objects.find_entity("AC", entities).acceleration -
                                         corbit.physics.gravitational_force(corbit.objects.find_entity("AC", entities),
                                                                            corbit.objects.find_entity("AC A", entities))
                                         /corbit.objects.find_entity("AC", entities).mass()).asNumber(un.m/un.s/un.s))).__str__(),
                     "Rotation: " + corbit.objects.find_entity("AC", entities).angular_speed.__str__(),
                     "         (" + corbit.objects.find_entity("AC", entities).angular_acceleratior.__str__() + ")"]
    # TODO: write apo peri etc. code in physics
    line_number = 1
    for text in lines_to_draw:
        line_number = print_text(text, line_number, display)


while True:

    commands_to_send = ""

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
            elif event.unicode == "d":
                commands_to_send += "fire_verniers|AC,1 "
            elif event.unicode == "w":
                commands_to_send += "change_engines|AC,0.01 "
            elif event.unicode == "s":
                commands_to_send += "change_engines|AC,-0.01 "
            elif event.unicode == "W":
                commands_to_send += "fire_rcs|AC,0 "
            elif event.unicode == "A":
                commands_to_send += "fire_rcs|AC," + str(math.pi / 2) + " "
            elif event.unicode == "S":
                commands_to_send += "fire_rcs|AC," + str(math.pi) + " "
            elif event.unicode == "D":
                commands_to_send += "fire_rcs|AC," + str(-math.pi / 2) + " "
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

    if commands_to_send: print(commands_to_send)
    corbit.network.sendall(commands_to_send.strip(), sock)

    entities = corbit.objects.load(corbit.network.recvall(sock))

    camera.move(1/fps)
    camera.update(corbit.objects.find_entity(camera.center, entities))

    draw(screen)
    pygame.display.flip()
    screen.fill((0, 0, 0))

    # time.sleep(1/fps.asNumber(Hz))
    # time.sleep(1/fps.asNumber(Hz) - time_spent_on_last_frame)

sock.close()
