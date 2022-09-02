import pygame
from pygame.locals import K_ESCAPE
from pygame import sprite
import sys, os
from objects import ControlledAvatar, Ghost
from level import Level
from camera import ChasingCamera
from renderer import GameRenderer
from collections import defaultdict
from events import EventHandler
from debug import log
import config


class TTGame(EventHandler):
    width = 800
    height = 600

    def __init__(self):
        log("initialising game")
        EventHandler.__init__(self, self)
        
        pygame.init()
        self.timer = pygame.time.Clock()
        self.screen = pygame.display.set_mode((TTGame.width, TTGame.height))
        pygame.display.set_caption("Tempus Temporis [prototype]")
        self.width, self.height = self.screen.get_size()

        path = config.levelsPath
        self.levels = []
        self.states = set()
        files = os.listdir(path)
        files.sort()
        for inFile in files:
            self.levels.append(Level(os.path.join(path,inFile), self))

        self.startLevel(self.levels[0])

    def update(self):
        # advance time
        self.time += 1

        self.camera.update(self)
        self.renderer.update(self)

    def draw(self):
        self.renderer.draw()

    def createAvatars(self):        
        self.avatar = ControlledAvatar(self.level.playerInitialPos, self)
        self.avatars = sprite.Group(self.avatar)

    def startLevel(self, level):
        log("starting level")
        self.eventHandlers = []        
        
        self.level = level
        self.level.reset()
        
        self.createAvatars()

        self.renderer = GameRenderer(self)
        self.renderer.add(self.level)
        self.renderer.add(self.avatars)
       
        self.time = 0
        
        self.camera = ChasingCamera(self)
    
    def travelBackInTime(self):
        # add ghost
        ghost = Ghost(self.avatar)
        self.renderer.add(ghost)        
        
        # replace avatar
        self.avatar.kill()        
        self.avatar = Avatar(self.level.playerInitialPos, self)
        self.avatars.add(self.avatar)
        self.renderer.add(self.avatar) # TODO should this be necessary?
        
        self.time = 0
        
    def resetLevel(self):
        #self.time = 0
        #self.level.reset()
        #for player in self.players.sprites():
        #    player.reset()
        
        self.startLevel(self.level)
    
    def nextLevel(self):
        self.resetLevel() # TODO
    
    def addEventHandler(self, eventHandler):
        self.eventHandlers.append(eventHandler)
    
    def removeEventHandler(self, eventHandler):
        self.eventHandlers.remove(eventHandler)
    
    def processDataStreams(self):
        for event in pygame.event.get():
            #print event
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == K_ESCAPE):
                self.gameOver = True
                break
            for eh in self.eventHandlers:
                eh.handleEvent(event)

    def mainLoop(self):
        self.gameOver = False
        while not self.gameOver:            
            self.processDataStreams()              
            self.update()
            self.draw()
            self.timer.tick(70)
            
        log("the game is over")
    

if __name__ == '__main__':
    if not os.path.exists("assets"): os.chdir("..")
    game = TTGame()
    game.mainLoop()
