import sys
import pickle
from typing import Iterator

import numpy as np

from .objects import *
from . import levelformat
from pygame import sprite
from .renderer import LayeredRenderer

sys.modules["levelformat"] = levelformat  # for backward compatibility with pickled files


class Grid:
    """
    Represents a grid-based level layout defined through a text file
    """
    def __init__(self, path: str, game, cellDim: float = 40):
        with open(path, "r") as f:
            lines = [l.rstrip() for l in f.readlines()]
        ydim = len(lines)
        xdim = max(*[len(l) for l in lines])
        grid = np.empty((xdim, ydim), dtype=np.object)
        playerInitialPos = None
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                grid[x, y] = char
                if char == "P":
                    playerInitialPos = (x, y)
        self.grid = grid
        self.playerInitialGridPos = playerInitialPos
        self.cellDim = cellDim
        self.game = game

    def cellRect(self, x, y) -> Rect:
        return Rect(x * self.cellDim, y * self.cellDim, self.cellDim, self.cellDim)

    def iterGameObjects(self) -> Iterator[GameObject]:
        for x in range(self.grid.shape[0]):
            for y in range(self.grid.shape[1]):
                c = self.grid[x, y]
                if c == "P":
                    continue
                elif c == "X":
                    yield Platform({"wrect": self.cellRect(x, y), "visible": True}, self.game)
                elif c == "E":
                    yield Exit({"wrect": self.cellRect(x, y)}, self.game, size=(self.cellDim, self.cellDim))

    def playerInitialPos(self) :
        cellRect = self.cellRect(*self.playerInitialGridPos)
        return cellRect.center


class Level(LayeredRenderer):
    def __init__(self, levelFile: str, game):
        LayeredRenderer.__init__(self)

        self.groups = {}
        self.platforms = self.addGroup(Platform)
        self.exits = self.addGroup(Exit)
        self.portals = self.addGroup(Portal)
        
        if levelFile[-2:] == ".p": # old level format
            levelFormat = pickle.load(open(levelFile, 'rb'))
            self.playerInitialPos = levelFormat.player.rect.center
            self.add(*[Platform(p, game) for p in levelFormat.platforms])
            self.add(Exit(levelFormat.exit, game))
            self.add(*[Portal(p, game) for p in levelFormat.buttons])
        elif levelFile.endswith(".grid"):
            grid = Grid(levelFile, game)
            self.playerInitialPos = grid.playerInitialPos()
            for o in grid.iterGameObjects():
                self.add(o)
        else:
            d = pickle.load(open(levelFile, "rb"))
            for o in d["objects"]:
                gameObject = GameObject.fromSaveFormat(o, game)
                self.add(gameObject)
            self.playerInitialPos = d["playerInitialPos"]
    
    def addGroup(self, cls):
        group = sprite.Group()
        self.groups[cls] = group
        return group
    
    def reset(self):    
        for group in (self.platforms, self.portals):
            for sprite in group.sprites():
                sprite.reset()
        #self.exit.reset()
    
    def add(self, *objects):
        LayeredRenderer.add(self, *objects)
            
        for object in objects:
            haveGroup = False
            for cls, group in self.groups.items():
                if isinstance(object, cls):
                    group.add(object)
                    haveGroup = True
            if not haveGroup: raise Exception("no group for " + str(object))
    
    def saveFormat(self):
        return {
            "objects": [o.saveFormat() for o in self.sprites()],
            "playerInitialPos": self.playerInitialPos
        }
        