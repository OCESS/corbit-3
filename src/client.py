__version__ = "3.0.0"
import sys, pygame
from entity import Entity
from unum.units import s
import Pyro4

print("Corbit PILOT " + __version__)
fps = 60

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.clear()
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
uri = "PYRO:telem@localhost:31415"   # Where to find the telemetry data
telem = Pyro4.Proxy(uri)

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((640,480))
pygame.display.set_caption("Corbit " + __version__)

telem.save("../res/client.json")
telem.load("../res/client.json")

entities = []

connected = False
while connected == False:
    print("connecting")
    try:
        entities = telem.entities()
        connected = True
    except Pyro4.errors.CommunicationError:
        print("connection failed")
        connected = False


while True:
    
    clock.tick(fps)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
    
    entities = telem.entities()
    
    for entity in entities:
        pygame.draw.circle(screen, entity.color,
                           entity.displacement.asNumber().astype(int),
                           entity.radius.asNumber())

    pygame.display.update()
    screen.fill((0,0,0))
