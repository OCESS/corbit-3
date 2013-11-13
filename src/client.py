__version__ = "3.0.0"
import sys, pygame
from unum.units import m,s
from scipy import array
import Pyro4

print("Corbit PILOT " + __version__)
fps = 60
screen_size = [1200, 700]


class Camera:
    
    def __init__(self, displacement, velocity, acceleration, zoom):
        self.displacement = displacement
        self.velocity = velocity
        self.acceleration = acceleration
        self.zoom = zoom
    
    def pan(self, amount):
        "Pan the camera by a vector amount"
        self.acceleration += amount
    
    def move(self, time):
        "Called every tick, keeps the camera moving"
        self.velocity += self.acceleration * time
        self.acceleration = 0 * m/s/s
        self.displacement += self.velocity * time



Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.clear()
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
uri = "PYRO:telem@localhost:31415"   # Where to find the telemetry data
telem = Pyro4.Proxy(uri)

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((screen_size[0],screen_size[1]))
pygame.display.set_caption("Corbit " + __version__)

entities = []

def find_entity(name):
    for entity in entities:
        if entity.name == name:
            return entity

connected = False
while connected == False:
    print("connecting")
    try:
        entities = telem.entities()
        connected = True
    except Pyro4.errors.CommunicationError:
        print("connection failed")
        connected = False

telem.save("../res/client.json")
telem.load("../res/client.json")
telem.load("../res/OCESS.json")

center = entities[0]
camera = Camera(center.displacement, center.velocity, center.acceleration, 1)
camera.pan(m/s/s * array([5,1]))

while True:
    
    clock.tick(fps)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
    
    entities = telem.entities()
    
    for entity in entities:
        pygame.draw.circle(screen, entity.color,
                           [int((entity.displacement - camera.displacement).asNumber()[0]
                            + screen_size[0]/2),
                            int((entity.displacement - camera.displacement).asNumber()[1]
                            + screen_size[1]/2)],
                           int(entity.radius.asNumber() * camera.zoom))

    pygame.display.update()
    screen.fill((0,0,0))
