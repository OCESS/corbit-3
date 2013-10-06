__version__ = "3.0.0"
import sys, pygame
from pygame.locals import *
from socket import *
import pickle
from entity import *
from unum.units import *
import Pyro4

print("Corbit PILOT " + __version__)
fps = 60

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.clear()
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
uri = "PYRO:telem@localhost:31415"   # Where to find the telemetry data

entities = []
telem = Pyro4.Proxy(uri)
entities = telem.entities()

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((640,480))
pygame.display.set_caption("Corbit " + __version__)

print("let's roll")
while True:
    
    clock.tick(fps)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
    
    entities = telem.entities()    
    
    for entity in entities:
        pygame.draw.circle(screen, (255,0,0),
                           entity.displacement.asNumber().astype(int),
                           entity.radius.asNumber())

    pygame.display.update()
    screen.fill((0,0,0))
