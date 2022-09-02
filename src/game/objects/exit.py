from typing import Optional, Tuple

import os
import pygame
from game.objects import GameObject


class Exit(GameObject):
    image = None
    
    def __init__(self, d, game, size: Optional[Tuple[float, float]] = None):
        if not Exit.image:
            imgpath = os.path.join("assets", "images", "exit.png")
            img = pygame.image.load(imgpath).convert_alpha()
            if size is not None:
                img = pygame.transform.scale(img, size)
            Exit.image = img

        self.image = Exit.image
        self.rect = self.image.get_rect()

        if type(d) != dict: # old construction
            GameObject.__init__(self, {"wrect": d.rect}, game)
        else:
            GameObject.__init__(self, d, game)
    
    def reset(self):
        pass
