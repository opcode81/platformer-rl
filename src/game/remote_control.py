from enum import Enum
from typing import Sequence, Iterable

import pygame


class VirtualKeyboard:
    def __init__(self):
        self.keysPressed = set()
        self.keysPressedPreviously = set()

    def update(self, keysPressed: Iterable[int]) -> list:
        """
        :param keysPressed: the keys to be pressed in the new time step
        :return: the list of events
        """
        self.keysPressedPreviously = self.keysPressed
        self.keysPressed = set(keysPressed)
        keysPressed = self.keysPressed - self.keysPressedPreviously
        keysReleased = self.keysPressedPreviously - self.keysPressed
        events = []
        for k in keysPressed:
            events.append(pygame.event.Event(pygame.KEYDOWN, dict(key=k)))
        for k in keysReleased:
            events.append(pygame.event.Event(pygame.KEYUP, dict(key=k)))
        return events


class RemoteAction(Enum):
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    LEFT_UP = "left_up"
    RIGHT_UP = "right_up"

    def getKeys(self):
        return {
            RemoteAction.LEFT: [pygame.K_LEFT],
            RemoteAction.RIGHT: [pygame.K_RIGHT],
            RemoteAction.UP: [pygame.K_UP],
            RemoteAction.LEFT_UP: [pygame.K_LEFT, pygame.K_UP],
            RemoteAction.RIGHT_UP: [pygame.K_RIGHT, pygame.K_UP],
        }[self]


class RemoteActionEventGenerator:
    def __init__(self):
        self.kb = VirtualKeyboard()

    def actionToEvents(self, action: RemoteAction) -> list:
        return self.kb.update(action.getKeys())
