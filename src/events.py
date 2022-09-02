from collections import defaultdict

class EventHandler(object):
    def __init__(self, game):
        self.bindings = defaultdict(list)
        self.hasBindings = False
        self.game = game
    
    def bind(self, eventType, callback):
        self.bindings[eventType].append(callback)
        if not self.hasBindings:
            self.hasBindings = True
            self.game.addEventHandler(self)
    
    def unbindAll(self):
        self.bindings = defaultdict(list)
        self.game.removeEventHandler(self)

    def handleEvent(self, event):    
        for handler in self.bindings.get(event.type, []):        
            handler(event)
