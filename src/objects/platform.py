import pygame

from objects import GameObject


class Platform(GameObject):
    def __init__(self, d, game):
        if type(d) != dict: # old construction
            GameObject.__init__(self, {"wrect": d.rect}, game)
            self.setSize(d.rect.width, d.rect.height)
            self.default = self.visible = d.visibleDefault
            self.group = d.setBy
            if d.setBy == "":
                self.group = None
        else:
            GameObject.__init__(self, d, game)
            rect = d["wrect"]
            self.setSize(rect.width, rect.height)
            self.default = self.visible = True
            self.group = None
            
    def setSize(self, width, height):
        self.image = pygame.Surface((width, height)).convert()
        self.rect.width = width
        self.rect.height = height
    
    def activate(self):
        self.visible = not self.default

    def deactivate(self):
        self.visible = self.default

    def reset(self):
        pass
