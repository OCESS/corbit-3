__version__ = "3.0.0"
import sys
import pygame
from pygame.locals import *
from unum.units import m,s,Hz
from scipy import array
import Pyro4

print("Corbit PILOT " + __version__)
fps = 60 * Hz


class Camera:
    
    def __init__(self, displacement, velocity, acceleration, zoom_level):
        self.displacement = displacement
        self.velocity = velocity
        self.acceleration = acceleration
        self.zoom_level = zoom_level
    
    def pan(self, amount):
        "Pan the camera by a vector amount"
        self.acceleration += amount
    
    def move(self, time):
        "Called every tick, keeps the camera moving"
        self.velocity += self.acceleration * time
        self.acceleration = 0 * m/s/s
        self.displacement += self.velocity * time
    
    def zoom(self, amount):
        "Zooms the camera in and out. Call this instead of modifying zoom_level"
        if amount < 0:
            self.zoom_level /= 1 - amount
        else:
            self.zoom_level *= 1 + amount
    
    locked = True
    speed = 100


Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.clear()
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
uri = "PYRO:telem@localhost:59722"  # Where to find the telemetry data
telem = Pyro4.Proxy(uri)

screen_size = (681, 745)
pygame.init()
clock = pygame.time.Clock()
display_flags = RESIZABLE
screen = pygame.display.set_mode(screen_size, display_flags)
pygame.display.set_caption("Corbit " + __version__)

pygame.key.set_repeat(True)

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
def update_camera():
    camera.displacement = center.displacement
    camera.velocity = center.velocity
    camera.acceleration = center.acceleration
camera = Camera(center.displacement, center.velocity, center.acceleration, 1)

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
            if event.key == K_RIGHT:
                camera.pan(m/s/s * array((camera.speed, 0)))
            if event.key == K_UP:
                camera.pan(m/s/s * array((0, -camera.speed)))
            if event.key == K_DOWN:
                camera.pan(m/s/s * array((0, camera.speed)))
            if event.unicode == "\t":
                camera.locked = not camera.locked
            if event.unicode == "-":
                camera.zoom(-0.1)
            if event.unicode == "+":
                camera.zoom(0.1)
            
    
    entities = telem.entities()
    if camera.locked:
        update_camera()
    camera.move(1/fps)
    
    
    for entity in entities:
        pygame.draw.circle(screen, entity.color,
         [int(
          camera.zoom_level *
          (entity.displacement - camera.displacement).asNumber()[0]
          + screen_size[0]/2),
         int(
          camera.zoom_level *
          (entity.displacement - camera.displacement).asNumber()[1]
          + screen_size[1]/2)],
         int(entity.radius.asNumber() * camera.zoom_level))

    pygame.display.update()
    screen.fill((0, 0, 0))
