__version__ = "3.0.0"
from entity import Entity,Habitat   # Corbit modules
from camera import Camera           # more Corbit modules
import sys      # used to exit the program
import pygame   # used for drawing and a couple other things
from pygame.locals import *     # so I don't have to type out KB_LEFT, etc
from unum.units import m,s,Hz,N # physical units that are used
from scipy import array         # scipy.array is what I represent a vector
                                # quantity with, e.g. velocity, displacement
from math import sin,cos,pi
import Pyro4                    # used to communicate with the server

print("Corbit PILOT " + __version__)
fps = 60 * Hz


Pyro4.config.SERIALIZER = "pickle"  # I chose pickle because I'm only going to
                                    # be running this on secure, isolated
                                    # networks
Pyro4.config.SERIALIZERS_ACCEPTED.clear()
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle") # I'll only be using pickle
uri = "PYRO:telem@localhost:3141"   # Where to find the telemetry data
telem = Pyro4.Proxy(uri)            # this object will be used to communicate
                                    # with the server

# just setting up the display and window here
screen_size = (681, 745)
pygame.init()
clock = pygame.time.Clock()
display_flags = RESIZABLE
screen = pygame.display.set_mode(screen_size, display_flags)
pygame.display.set_caption("Corbit " + __version__)
pygame.key.set_repeat(True)


connected = False
print("connecting")
while connected == False:
    try:
        print("Found objects:\n",telem.entities())
        connected = True
    except Pyro4.errors.CommunicationError:
        connected = False

camera = Camera(1)

telem.load("../res/OCESS.json") # gets the server to load the default save

while True:
    
    clock.tick(fps.asNumber())
    
    for event in pygame.event.get():
        if event.type == QUIT:
            sys.exit()
        if event.type == VIDEORESIZE:
            screen_size = event.dict["size"]
            screen = pygame.display.set_mode(screen_size, display_flags)
            print(screen_size)
        if pygame.key.get_focused() and event.type == KEYDOWN:
            if event.key == K_LEFT:
                camera.pan(m/s/s * array((-camera.speed, 0)))
            elif event.key == K_RIGHT:
                camera.pan(m/s/s * array((camera.speed, 0)))
            elif event.key == K_UP:
                camera.pan(m/s/s * array((0, -camera.speed)))
            elif event.key == K_DOWN:
                camera.pan(m/s/s * array((0, camera.speed)))
            elif event.unicode == "q":
                telem.accelerate("AC", N * array([0,-1e3]), pi)
                telem.accelerate("AC", N * array([0,1e3]), 0)
            elif event.unicode == "e":
                telem.accelerate("AC", N * array([0,1e3]), pi)
                telem.accelerate("AC", N * array([0,-1e3]), 0)
            elif event.unicode == "w":
                telem.accelerate("AC", N * array([0,1e3]), 3*pi/2 + 0.5)
                telem.accelerate("AC", N * array([0,1e3]), 3*pi/2 - 0.5)
            elif event.unicode == "+":
                telem.change_engines("AC", 0.01)
            elif event.unicode == "-":
                telem.change_engines("AC", -0.01)
            elif event.unicode == "\t":
                camera.locked = not camera.locked
            elif event.unicode == "-":
                camera.zoom(-0.1)
            elif event.unicode == "+":
                camera.zoom(0.1)
            
    camera.update()
    camera.move(1/fps)
    
    ## Drawing routines here 
    for entity in telem.entities():
        # calculating the on-screen position
        screen_position = \
         [
          int(
           camera.zoom_level *
           (entity.displacement - camera.displacement).asNumber()[0]
           + screen_size[0]/2),
          int(
           camera.zoom_level *
           (entity.displacement - camera.displacement).asNumber()[1]
           + screen_size[1]/2)
         ]
        # calculating the on-screen radius
        screen_radius = int(entity.radius.asNumber() * camera.zoom_level)
         
        if type(entity) == Entity:
            # entity drawing is the simplest, just a circle
            pygame.draw.circle(screen, entity.color,
                               screen_position, screen_radius)
        elif type(entity) == Habitat:
            # habitat is the entity drawing, but with a line pointing forwards
            pygame.draw.circle(screen, entity.color,
                               screen_position, screen_radius)
            pygame.draw.line(screen, (0,255,0), screen_position,
             [
              int(
               screen_position[0] +
               screen_radius * cos(entity.angular_position)
              ),
              int(
               screen_position[1] +
               screen_radius * sin(entity.angular_position)
              )
             ]
            )


    pygame.display.update()
    screen.fill((0, 0, 0))
