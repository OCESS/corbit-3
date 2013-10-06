__version__ = "3.0.0"
import sys, pygame
from pygame.locals import *
from socket import *
import pickle
from entity import *
from unum.units import *
import Pyro4
from telemetry import Telemetry

Pyro4.SERIALIZER = pickle 


uri = "PYRO:telem@localhost:31415"   # Where to find the server's data

print("Corbit " + __version__)

#telemetry = Telemetry()
telem = Pyro4.Proxy(uri)

print(telem)
print(telem.fps())
fps = telem.fps()

print (telem.entities[0].name)

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((640,480))
pygame.display.set_caption("Corbit " + __version__)

print("let's roll")
while True:
    
    clock.tick(fps)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
    
    
        

    for entity in telem.entities:
        pygame.draw.circle(screen, (255,0,0),
                           entity.displacement.asNumber().astype(int),
                           entity.radius.asNumber())

    pygame.display.update()
    screen.fill((0,0,0))
