import sys
import pickle
from typing import Iterator

import numpy as np

from .objects import *
from . import levelformat
from pygame import sprite
from .renderer import LayeredRenderer

sys.modules["levelformat"] = levelformat  # for backward compatibility with pickled files


class Level(LayeredRenderer):
    def __init__(self, playerInitialPos: Tuple[float, float]):
        LayeredRenderer.__init__(self)

        self.groups = {}
        self.platforms = self.addGroup(Platform)
        self.exits = self.addGroup(Exit)
        self.portals = self.addGroup(Portal)
        self.playerInitialPos = playerInitialPos
        
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


class LevelFromPickleV1(Level):
    """
    Legacy level representation
    """
    def __init__(self, path, game):
        with open(path, "rb") as f:
            levelFormat = pickle.load(f)
        playerInitialPos = levelFormat.player.rect.center
        super().__init__(playerInitialPos)
        self.add(*[Platform(p, game) for p in levelFormat.platforms])
        self.add(Exit(levelFormat.exit, game))
        self.add(*[Portal(p, game) for p in levelFormat.buttons])


class LevelFromPickleV2(Level):
    """
    Level created by wx level editor
    """
    def __init__(self, path, game):
        with open(path, "rb") as f:
            d = pickle.load(f)
        d: dict
        super().__init__(d["playerInitialPos"])
        for o in d["objects"]:
            gameObject = GameObject.fromSaveFormat(o, game)
            self.add(gameObject)


class Grid:
    """
    Represents a grid-based level layout defined through a text file
    """
    def __init__(self, path: str, game, cellDim: float = 40):
        with open(path, "r") as f:
            lines = [l.rstrip() for l in f.readlines()]
        ydim = len(lines)
        xdim = max(*[len(l) for l in lines])
        grid = np.empty((ydim, xdim), dtype=np.object)
        grid.fill(" ")
        playerInitialPos = None
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                grid[y, x] = char
                if char == "P":
                    playerInitialPos = (x, y)
        self.grid = grid
        self.padding = 100
        paddedGrid = np.empty((ydim + 2 * self.padding, xdim + 2 * self.padding), dtype=np.object)
        paddedGrid.fill(" ")
        paddedGrid[self.padding:self.padding+ydim, self.padding:self.padding+xdim] = grid
        self.paddedGrid = paddedGrid
        self.playerInitialGridPos = playerInitialPos
        self.cellDim = cellDim
        self.game = game

    def cellRect(self, x, y) -> Rect:
        return Rect(x * self.cellDim, y * self.cellDim, self.cellDim, self.cellDim)

    def gridCellForPos(self, pos: np.ndarray) -> np.ndarray:
        arr = pos // self.cellDim
        return arr.astype(np.int)

    def posRelativeToCellCentre(self, pos: Tuple[float, float], cell: Tuple[int, int]) -> Tuple[float, float]:
        cellCentrePos = self.cellRect(*cell).center
        return pos[0] - cellCentrePos[0], pos[1] - cellCentrePos[1]

    def iterGameObjects(self) -> Iterator[GameObject]:
        for y in range(self.grid.shape[0]):
            for x in range(self.grid.shape[1]):
                c = self.grid[y, x]
                if c == "P":
                    continue
                elif c == "X":
                    yield Platform({"wrect": self.cellRect(x, y), "visible": True}, self.game)
                elif c == "E":
                    yield Exit({"wrect": self.cellRect(x, y)}, self.game, size=(self.cellDim, self.cellDim))

    def surroundingGrid(self, cell: Tuple[int, int], xminus, xplus, yminus, yplus) -> np.ndarray:
        x, y = cell
        xdim = 1 + xplus + xminus
        ydim = 1 + yplus + yminus
        x0 = x - xminus + self.padding
        y0 = y - yminus + self.padding
        x1 = x0 + xdim
        y1 = y0 + ydim
        return self.paddedGrid[y0:y1, x0:x1]

    def playerInitialPos(self) :
        cellRect = self.cellRect(*self.playerInitialGridPos)
        return cellRect.center


class GridLevel(Level):
    """
    Level from grid-based text file
    """
    def __init__(self, path, game):
        self.grid = Grid(path, game)
        super().__init__(self.grid.playerInitialPos())
        for o in self.grid.iterGameObjects():
            self.add(o)


def loadLevel(path: str, game) -> Level:
    if path[-2:] == ".p":
        return LevelFromPickleV1(path, game)
    elif path.endswith(".grid"):
        return GridLevel(path, game)
    else:
        return LevelFromPickleV2(path, game)
