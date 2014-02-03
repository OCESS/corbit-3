from unum.units import m,s
from entity import Entity
from scipy import array

class Camera:
    "Used to store the zoom level and position of the display's camera"
    
    def __init__(self, zoom_level, center=None):
        self.center = center
        if self.center == None:
            self.locked = False
        else:
            self.locked = True
        
        self.displacement = m * array([0,0]) 
        self.velocity = m/s * array([0,0])
        self.acceleration = m/s/s * array([0,0])
        
        self.zoom_level = zoom_level
    
    locked = True
    speed = 1e2

    def update(self, entity):
        "Updates the camera's position to match that of the center"
        if self.locked:
            self.displacement = entity.displacement
            self.velocity = entity.velocity
            self.acceleration = entity.acceleration
    
    def pan(self, amount):
        "Pan the camera by a vector amount"
        self.acceleration += amount * self.speed
    
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