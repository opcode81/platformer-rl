from game.objects import GameObject
import pygame
import os
import numpy

class Portal(GameObject):
    images = {}
    
    def __init__(self, d, game):        
        
        if not Portal.images:
            inactiveImgPath = os.path.join("assets", "images", "portalInactive.png")
            activeImgPath = os.path.join("assets", "images", "portalActive.png")
            Portal.images['inactive'] = pygame.image.load(inactiveImgPath).convert_alpha()
            Portal.images['active'] = pygame.image.load(activeImgPath).convert_alpha()
        
        self.image = Portal.images['inactive']
        
        self.activated = False
        
        if type(d) != dict: # old construction
            GameObject.__init__(self, {"wrect": d.rect}, game)
            self.group = d.sets
            self.rect = self.image.get_rect()            
            self.pos = numpy.array(d.rect.midbottom)
            self.pos[1] -= self.rect.height / 2
            self.rect.center = self.pos
        else:
            GameObject.__init__(self, d, game)
        
    def update(self, game):
        if len(self.collide(game.avatars)) > 0:
            self.activate()
        else:
            self.deactivate()
            
        GameObject.update(self, game)
        
    def activate(self):
        self.activated = True
        self.image = Portal.images['active']

    def deactivate(self):
        self.activated = False
        self.image = Portal.images['inactive']
    
    def reset(self):
        pass
