from typing import Tuple

import pygame
import sys, os
import renderer
from collections import defaultdict
from pygame.locals import *
from objects import DynamicObject, GameObject
import numpy
from debug import log
from .motion import *
from .anim import *


class Timeline(object):
    def __init__(self):
        self.history = defaultdict(list)
    
    def addState(self, time, state):
        self.history[time] = tuple(state)


class Avatar(DynamicObject):
    def __init__(self, d, game):
        if type(d) != dict:
            rect = pygame.Rect(0,0,10,10) # dummy
            rect.center = d
            DynamicObject.__init__(self, {"wrect": rect}, game)            
            self.pos = numpy.array(d, dtype=numpy.float64)
        else:
            DynamicObject.__init__(self, d, game)
            
        self.useAnimations = False
        self.anim = {}
        animPath = os.path.join("assets", "anim")
        self.anim["walkLeft"] = AnimCycle(animPath, "left1.png", "left2.png", "left3.png")
        self.anim["walkRight"] = AnimCycleFlipped(self.anim["walkLeft"])
        self.anim["leftWall"] = AnimImage(animPath, "leftwall.png")
        self.anim["rightWall"] = AnimImageFlipped(self.anim["leftWall"])
        self.anim["idle"] = AnimImage(animPath, "idle.png")
        #for a in self.anim.values():
        #    a.scale(0.6)
        
        surface = pygame.Surface((30,30))
        surface.fill((0,50,100))
        self.image = surface.convert_alpha()
        #self.image = pygame.image.load(os.path.join("assets", "anim", "left1.png")).convert_alpha()        
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        self.initialpos = self.rect.center = self.pos
        self.timeline = Timeline()
        self.state.pos = self.pos        
        
        self.counter = 0

    def setLocation(self, pos: Tuple[float, float]):
        self.pos = numpy.array(pos, dtype=numpy.float64)
        
    def reset(self):
        self.pos = self.initialpos
        self.rect.center = self.pos
    
    def update(self, game):
        self.pos = self.state.pos
        super(Avatar, self).update(game)


class ControlledAvatar(Avatar):
    def __init__(self, d, game):
        super(ControlledAvatar, self).__init__(d, game)
        
        #self.motion = SillyOldMotion(self)
        self.motion = MeatBoyMotion(self)  
        
        self.bind(pygame.KEYDOWN, self.onKeyDown)
        self.bind(pygame.KEYUP, self.onKeyUp)
        
    def triggerMotion(self, event, status):
        if event.key in (K_w, K_UP, K_PERIOD):
            self.motion.makeJump(status)
        elif event.key in (K_a, K_LEFT):
            self.motion.moveLeft(status)
        elif event.key in (K_d, K_RIGHT):
            self.motion.moveRight(status)
        elif event.key in (K_RSHIFT, K_LSHIFT, K_COMMA):
            self.motion.run(status)

    def onKeyDown(self, event):
        game = self.game
        self.triggerMotion(event, True)
        if event.key == K_SPACE:               
            if len(self.collide(game.level.portals)) > 0:
                game.travelBackInTime()
    
    def onKeyUp(self, event):
        self.triggerMotion(event, False)
        
    def update(self, game):
        # check for death
        if self.motion.vel[1] > 250:
            log("player has died")
            game.resetLevel() # TODO replace with event?
            return
        
        # update position
        self.pos = self.state.pos = self.motion.update(game)
        
        if self.useAnimations:
            if self.motion.onLeftWall:
                self.image = self.anim["leftWall"].get()
            elif self.motion.onRightWall:
                self.image = self.anim["rightWall"].get()
            elif self.motion.onGround:
                if self.motion.vel[0] < -0.4:
                    self.image = self.anim["walkLeft"].get()
                elif self.motion.vel[0] > 0.4:
                    self.image = self.anim["walkRight"].get()
                else:
                    self.image = self.anim["idle"].get()
            else:
                if self.motion.vel[0] < -0.4:
                    self.image = self.anim["walkLeft"].images[0]                
                elif self.motion.vel[0] > 0.4:
                    self.image = self.anim["walkRight"].images[0]
                else:
                    self.image = self.anim["idle"].get()
            self.rect = self.image.get_rect()
      
        # update timeline
        self.timeline.addState(self.game.time, self.pos)
        
        super(ControlledAvatar, self).update(game)
        
        self.counter += 1


class Ghost(GameObject):    
    def __init__(self, player):
        super().__init__(player.__dict__, player.game)
        surface = pygame.Surface((30,30))
        surface.fill((0,50,100))
        surface.set_alpha(100)
        self.image = surface.convert_alpha()
        self.rect = self.image.get_rect()
        self.history = dict(player.timeline.history)
    
    def update(self, game):
        time = game.time
        if time in self.history:
            self.pos = self.history[time]
        GameObject.update(self, game)
        
        
