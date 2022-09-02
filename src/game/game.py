import os
import sys

import pygame
from pygame import sprite
from pygame.locals import K_ESCAPE

from . import config
from .camera import ChasingCamera
from .debug import log
from .events import EventHandler
from .level import Level
from .objects import ControlledAvatar, Ghost
from .remote_control import RemoteActionEventGenerator, RemoteAction
from .renderer import GameRenderer


class Game(EventHandler):
    width = 800
    height = 600
    FRAME_RATE = 60
    SCORE_EXIT = 100
    SCORE_PER_SECOND = -1
    SCORE_TICK = SCORE_PER_SECOND/FRAME_RATE
    SCORE_DEATH = -1000

    def __init__(self, levelFilename=None, enableRendering=True):
        log(f"Initialising game (level={levelFilename})")
        EventHandler.__init__(self, self)
        
        pygame.init()
        self.enableRendering = enableRendering
        self.renderer = None
        self.timer = pygame.time.Clock()
        self.screen = pygame.display.set_mode((Game.width, Game.height))
        pygame.display.set_caption("Tempus Temporis [prototype]")
        self.width, self.height = self.screen.get_size()

        path = config.levelsPath
        self.states = set()

        files = os.listdir(path)
        files.sort()

        level = None
        for inFile in files:
            if inFile == levelFilename:
                level = Level(os.path.join(path, inFile), self)

        if level is None:
            print(f"No level selected; the following filenames were found: {files}")
            sys.exit(1)

        self.startLevel(level)

    def update(self):
        # advance time
        self.time += 1
        self.score += self.SCORE_TICK

        self.camera.update(self)
        self.renderer.update(self)

    def draw(self):
        if self.enableRendering:
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

        self.score = 0
        self.time = 0
        
        self.camera = ChasingCamera(self)
    
    def travelBackInTime(self):
        # add ghost
        ghost = Ghost(self.avatar)
        self.renderer.add(ghost)        
        
        # replace avatar
        self.avatar.kill()        
        self.avatar = ControlledAvatar(self.level.playerInitialPos, self)
        self.avatars.add(self.avatar)
        self.renderer.add(self.avatar) # TODO should this be necessary?
        
        self.time = 0

    def playerDies(self):
        log("player has died")
        self.resetLevel()

    def playerExitsLevel(self):
        self.score += self.SCORE_EXIT
        self.gameOver = True
        
    def resetLevel(self):
        self.startLevel(self.level)
    
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
            self.timer.tick(self.FRAME_RATE)
        log(f"the game is over, score={self.score}")

    def mainLoopRemoteControlledTest(self):
        self.gameOver = False
        frame = 0
        actionGen = RemoteActionEventGenerator()
        while not self.gameOver:
            if frame <= 10:
                action = RemoteAction.RIGHT
            elif frame <= 20:
                action = RemoteAction.RIGHT_UP
            else:
                action = RemoteAction.RIGHT
            events = actionGen.actionToEvents(action)
            for e in events:
                pygame.event.post(e)
            self.processDataStreams()
            self.update()
            self.draw()
            self.timer.tick(self.FRAME_RATE)
            frame += 1
        log(f"the game is over, score={self.score}")
