import pygame
import os


class AnimBase(object):
    def scale(self, f):
        self.images = [pygame.transform.scale(img, (img.get_width()*f, img.get_height()*f)) for img in self.images]


class AnimCycle(AnimBase):
    def __init__(self, path, *filenames):
        self.images = []
        for filename in filenames:
            self.images.append(pygame.image.load(os.path.join(path, filename)).convert_alpha())
        self.cycle = 0
        self.step = 0
    
    def get(self):
        img = self.images[self.cycle]
        if self.step % 10 == 0:
            self.cycle = (self.cycle + 1) % len(self.images)
        self.step += 1
        return img


class AnimCycleFlipped(AnimCycle):
    def __init__(self, animCycle):
        self.cycle = self.step = 0
        self.images = [pygame.transform.flip(img, True, False) for img in animCycle.images]


class AnimImage(AnimBase):
    def __init__(self, path, filename):
        self.images = [pygame.image.load(os.path.join(path, filename)).convert_alpha()]
    
    def get(self):
        return self.images[0]


class AnimImageFlipped(AnimImage):
    def __init__(self, animImage):
        self.images = [pygame.transform.flip(animImage.get(), True, False)]

