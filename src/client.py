__version__ = "3.0.0"
import sys, pygame
from pygame.locals import *
from socket import *
import pickle
from entity import *
from unum.units import *
import Pyro4

class version_mismatch(Exception):
    def __init__(self, value):
        self.value = "My version: " + value
    def __str__(self):
        return repr(self.value)


uri = "PYRO:entities@localhost:31415"   # Where to find the server's data

print("Corbit " + __version__)


server = Pyro4.Proxy(uri)

print(server.fps())

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((640,480))
pygame.display.set_caption("Corbit " + __version__)

print("let's roll")
while True:
    
    clock.tick(server.fps)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
    
    
        

    for entity in server.entities:
        pygame.draw.circle(screen, (255,0,0),
                           entity.displacement.asNumber().astype(int),
                           entity.radius.asNumber())

    pygame.display.update()
    screen.fill((0,0,0))

sock.shutdown(SHUT_RDWR)
sock.close()