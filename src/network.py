import socket
import sys
import threading
import pickle
import wx
import asyncore
import time as t
from game import Game
from Queue import Queue
from debug import log
from renderer import SpriteGroup
from objects.avatar import *
import traceback

class AccessProxy(object):
    def __init__(self, statement):
        self.statement = statement
        self.data = []
    
    def __getattr__(self, attr):
        self.statement += ".%s" % attr
        return self
    
    def __call__(self, *args):
        self.statement += "("
        if len(args) > 0:
            self.statement += "*data[%d]" % len(self.data)
            self.data.append(args)
        self.statement += ")"
        return self

    def __getitem__(self, key):
        self.statement += "["
        self.statement += "data[%d]" % len(self.data)
        self.data.append(key)
        self.statement += "]"
        return self

    def __str__(self):
        return self.statement


class GameProxy(object):
    def __init__(self):
        self.proxies = []
        self.current = None
    
    def __getattr__(self, attr):
        if self.current is not None:
            self.proxies.append(self.current)
        self.current = AccessProxy("game")
        return self.current.__getattr__(attr)

    def statements(self):
        if self.current is not None:
            self.proxies.append(self.current)
            self.current = None
        return [(p.statement, p.data) for p in self.proxies]


class NetGame(Game):
    def __init__(self, dispatcher, i):
        log("initialising network game")
        self.dispatcher = dispatcher
        self.i = i
        self.networkEvents = Queue()
        super(NetGame, self).__init__()

    def handleNetworkEvent(self, e):
        self.networkEvents.put(e)
    
    def processDataStreams(self):
        super(NetGame, self).processDataStreams()
        
        while not self.networkEvents.empty():
            e = self.networkEvents.get()            
            if not type(e) == dict:
                continue
            game = self
            if e["event"] == "gameData":
                for (statement, data) in e["statements"]:
                    log("network statement:", statement)
                    exec(statement)
    
    def createAvatars(self):        
        self.avatars = SpriteGroup()
        for i in xrange(2):
            if i == self.i:
                avatar = self.avatar = ControlledAvatar(self.level.playerInitialPos, self)
            else:
                avatar = Avatar(self.level.playerInitialPos, self)
            self.avatars.add(avatar)
    
    def update(self):
        super(NetGame, self).update()
        # send out remote statements
        proxy = GameProxy()
        proxy.avatars.sprites()[self.i].setState(self.avatar.getState())
        data = {
            "event": "gameData",
            "statements": proxy.statements()
        }
        self.dispatcher.dispatch(data)


class GameServer(asyncore.dispatcher):
    def __init__(self, port):
        asyncore.dispatcher.__init__(self)
        # start listening for connections
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        host = ""
        self.bind((host, port))
        self.connections = []
        self.listen(1)
        # create actual game
        self.game = NetGame(self, 0)
    
    def handle_accept(self):        
        pair = self.accept()
        if pair is None:
            return
        log("incoming connection from %s" % str(pair[1]))
        conn = DispatcherConnection(pair[0], self)
        self.connections.append(conn)
        #conn.sendData("hello %s" % str(pair[1]))

    def dispatch(self, d, exclude=None):
        #print "dispatching %s to %d client(s)" % (str(d), len(self.connections) if exclude is None else len(self.connections)-1)
        for c in self.connections:
            if c != exclude:
                c.sendData(d)
    
    def removeConnection(self, conn):
        if not conn in self.connections:
            log("tried to remove non-present connection")
        self.connections.remove(conn)
        if len(self.connections) == 0:
            raise Exception("no more clients")

class DispatcherConnection(asyncore.dispatcher_with_send):
    def __init__(self, connection, server):
        asyncore.dispatcher_with_send.__init__(self, connection)
        self.syncserver = server

    def writable(self):
        return bool(self.out_buffer)

    def handle_write(self):
        self.initiate_send()

    def handle_read(self):
        d = self.recv(64000)
        if d == "": # connection closed from other end          
            return
        d = pickle.loads(d)
        #print "received: %s " % d
        # forward event to other clients
        #self.syncserver.dispatch(d, exclude=self)
        # handle in own player
        self.syncserver.game.handleNetworkEvent(d)            

    def remove(self):
        log("client connection dropped")
        self.syncserver.removeConnection(self)

    def handle_close(self):
        self.remove()
        self.close()

    def sendData(self, d):
        self.send(pickle.dumps(d))


class GameClient(asyncore.dispatcher):  
    def __init__(self, server, port):
        self.game = NetGame(self, 1)
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)      
        self.connect((server, port))
        # create actual player
        
    def handle_read(self):
        d = self.recv(64000)
        if d == "": # server connection lost
            log("connection lost")
            return        
        d = pickle.loads(d)
        #print "received: %s " % d
        self.game.handleNetworkEvent(d)
    
    def dispatch(self, d):
        #print "sending %s" % str(d)
        self.send(pickle.dumps(d))


def networkLoop():
    while True:
        asyncore.poll(0.01)


if __name__=='__main__':        
    networkThread = threading.Thread(target=networkLoop)
    networkThread.daemon = True
    networkThread.start()
    
    argv = sys.argv[1:]
    file = None
    if len(argv) in (2, ) and argv[0] == "serve":
        port = int(argv[1])
        log("serving on port %d" % port)
        server = GameServer(port)
        game = server.game
    elif len(argv) in (3, ) and argv[0] == "connect":
        server = argv[1]
        port = int(argv[2])
        log("connecting to %s:%d" % (server, port))
        client = GameClient(server, port)
        game = client.game
    else:
        appName = "network.py"
        print "\nTTNetGame\n\n"
        print "usage:"
        print "   server:  %s serve <port> [file]" % appName
        print "   client:  %s connect <server> <port> [file]" % appName
        sys.exit(1)
    
    try:
        game.mainLoop()
    except:
        e, v, tb = sys.exc_info()
        print v
        traceback.print_tb(tb)

