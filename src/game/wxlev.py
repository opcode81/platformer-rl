import wx
import os
import thread
import traceback
import sys
import numpy
from debug import log
import levelformat as lf
import pickle

# deferred pygame imports
global pygame
global level
global renderer
global objects


class SDLPanel(wx.Panel):
    def __init__(self,parent,ID,tplSize):
        global pygame, level, renderer, objects
        wx.Panel.__init__(self, parent, ID, size=tplSize)
        self.Fit()
        
        # initialize pygame-related stuff
        os.environ['SDL_WINDOWID'] = str(self.GetHandle())
        os.environ['SDL_VIDEODRIVER'] = 'windib'       
        import pygame # this has to happen after setting the environment variables.
        import level
        pygame.display.init()
        screen = pygame.display.set_mode(tplSize)
        
        # initialize level viewer
        self.screen = screen
        self.levelViewer = LevelViewer(screen, tplSize)
        self.levelViewer.setLevel(level.Level(os.path.join("assets", "levels", "0.p"), self.levelViewer))
        #self.levelViewer.setLevel(level.Level(os.path.join("assets", "levels", "test.lvl"), self.levelViewer))
        
        # start pygame thread
        thread.start_new_thread(self.levelViewer.mainLoop, ())

    def __del__(self):
        self.levelViewer.running = False


class Camera(object):
    def __init__(self, pos, game):
        self.translate = numpy.array([-game.width/2, -game.height/2])
        self.pos = pos + self.translate
        
    def update(self, game):        
        return self.pos
        
    def offset(self, o):
        self.pos += o
        

class LevelViewer(object):
    def __init__(self, screen, size):
        self.screen = screen
        self.width, self.height = size
        self.running = False

    def setLevel(self, level):
        self.renderer = renderer.GameRenderer(self)
        self.level = level
        self.camera = Camera(self.level.playerInitialPos, self)        
        self.renderer.add(self.level)
        self.avatars = pygame.sprite.Group()
        
        self.scroll = False
        self.selectedObject = None
        self.activeTool = None

    def update(self):
        self.camera.update(self)
        self.renderer.update(self)

    def draw(self):
        self.renderer.draw()
        
    def mainLoop(self):
        self.running = True
        try:
            while self.running:
                for event in pygame.event.get():
                    #log(event)
                    
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        if event.button == 3:
                            self.onRightMouseButtonDown(x, y)                        
                        elif event.button == 1:
                            self.onLeftMouseButtonDown(x, y)
                            
                    if event.type == pygame.MOUSEBUTTONUP:                        
                        if event.button == 3:
                            self.onRightMouseButtonUp()
                        elif event.button == 1:
                            self.onLeftMouseButtonUp()
                                
                    if event.type == pygame.MOUSEMOTION:
                        self.onMouseMove(*(event.pos + event.rel))
                    
                self.update()
                self.draw()
            
        except:
            e, v, tb = sys.exc_info()
            print v
            traceback.print_tb(tb)
    
    def onRightMouseButtonDown(self, x, y):
        self.scroll = True
    
    def onLeftMouseButtonDown(self, x, y):
        if self.activeTool is None: # select object
            matches = filter(lambda o: o.rect.collidepoint((x,y)), self.level.sprites())
            if len(matches) > 0:
                self.selectedObject = matches[0]
                log("selected", self.selectedObject)
                
        elif self.activeTool == "platform": # create platform
            pos = numpy.array([x,y]) + self.camera.pos                                
            self.selectedObject = platform = objects.Platform(lf.Platform(pos[0], pos[1], 10, 10), self)
            self.level.add(platform)
    
    def onRightMouseButtonUp(self):
        self.scroll = False
    
    def onLeftMouseButtonUp(self):
        self.activeTool = None
        self.selectedObject = None
    
    def onMouseMove(self, x, y, dx, dy):
        if self.scroll:                     
            self.camera.offset(numpy.array([-dx, -dy]))
            
        elif self.activeTool is None: # move selected object
            if self.selectedObject is not None:
                self.selectedObject.offset(dx, dy)
                
        elif self.selectedObject is not None: 
            if self.activeTool == "platform": # enlarge platform, setting bottom right corner
                topLeft = numpy.array([self.selectedObject.rect.left, self.selectedObject.rect.top])
                pos = numpy.array([x,y])
                dim = pos - topLeft
                if dim[0] > 0 and dim[1] > 0:
                    self.selectedObject.setSize(dim[0], dim[1])
                    self.selectedObject.rect.topleft = topLeft
                    self.selectedObject.pos = numpy.array(self.selectedObject.rect.center) + self.camera.pos


class LevelEditor(wx.Frame):
    def __init__(self, parent, ID, strTitle, tplSize):
        wx.Frame.__init__(self, parent, ID, strTitle, size=tplSize)
        self.pnlSDL = SDLPanel(self, -1, tplSize)
        
        # Menu Bar        
        self.frame_menubar = wx.MenuBar()
        self.SetMenuBar(self.frame_menubar)
        # - file Menu
        self.file_menu = wx.Menu()
        self.file_menu.Append(1, "&Open", "Open from file..")
        self.file_menu.Append(2, "&Save", "Open a file..")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(3, "&Close", "Quit")
        self.Bind(wx.EVT_MENU, self.onOpen, id=1)
        self.Bind(wx.EVT_MENU, self.onSave, id=2)
        self.Bind(wx.EVT_MENU, self.onExit, id=3)
        self.frame_menubar.Append(self.file_menu, "File")

        toolbar = wx.Panel(self, -1)
        self.toolbar = toolbar
        platform = wx.Button(toolbar, label="Platform")
        self.Bind(wx.EVT_BUTTON, self.onPlatform, platform)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.pnlSDL, 1, flag=wx.EXPAND)
        sizer.Add(toolbar, flag=wx.EXPAND | wx.BOTTOM | wx.TOP, border=0)
        self.SetSizer(sizer)
        
        self.viewer = self.pnlSDL.levelViewer

    def onPlatform(self, event):
        self.viewer.activeTool = "platform"

    def onOpen(self, event):
        dlg = wx.FileDialog(self, "Choose a file", os.path.join("..", "assets", "levels"), "", "*.lvl", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = os.path.join(dlg.GetDirectory(), dlg.GetFilename())                        
            dlg.Destroy()
            
            # load level
            self.viewer.setLevel(level.Level(path, self.viewer))
    
    def onSave(self, event):
        dlg = wx.FileDialog(self, "Choose a file", os.path.join("..", "assets", "levels"), "", "*.lvl", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = os.path.join(dlg.GetDirectory(), dlg.GetFilename())                        
            dlg.Destroy()
            
            # save level
            f = file(path, "wb")
            pickle.dump(self.viewer.level.saveFormat(), f)
            f.close()

    def onExit(self, event):
        pass


if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = LevelEditor(None, wx.ID_ANY, "pyTT Level Editor", (800,600))
    frame.Show()
    app.MainLoop()