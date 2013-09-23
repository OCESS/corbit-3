__version__ = "3.0.0"
import sys, pygame
from pygame.locals import *
from socket import *
import pickle
from entity import *
from unum.units import *


HOST = 'localhost'    # The remote host
PORT = 31415          # The same port as used by the server
fps = 60

print("Corbit " + __version__)


sock = socket(AF_INET, SOCK_STREAM)
sock.connect((HOST, PORT))

recvd = (b"")
while True:
    data = sock.recv(4096)
    if not data: break
    recvd += data

sock.close()
    
entities = pickle.loads(recvd)
print(entities[0].name)



pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((640,480))
pygame.display.set_caption("Corbit " + __version__)

while True:
    
    clock.tick(fps)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
    
    for entity in entities:
        
        print(entity.velocity)
        print(entity.acceleration)
        print(s/fps)
        entity.move(s/fps)
        

    for entity in entities:
        pygame.draw.circle(screen, (255,0,0),
                           entity.displacement.asNumber().astype(int),
                           entity.radius.asNumber())

    pygame.display.update()
    screen.fill((0,0,0))
