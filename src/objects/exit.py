from levelformat import Exit as e
import os
import pygame
from objects import GameObject
import numpy

class Exit(GameObject):
    image = None
    
    def __init__(self, d, game):
        if not Exit.image:
            imgpath = os.path.join("assets", "images", "exit.png")
            Exit.image = pygame.image.load(imgpath).convert_alpha()

        self.image = Exit.image
        self.rect = self.image.get_rect()

        if type(d) != dict: # old construction
            GameObject.__init__(self, {"wrect": d.rect}, game)
        else:
            GameObject.__init__(self, d, game)
    
    def reset(self):
        pass
