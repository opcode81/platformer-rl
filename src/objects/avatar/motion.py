import numpy
from debug import log
import pygame

class SillyOldMotion(object):
    def __init__(self, avatar):
        self.avatar = avatar
        self.grav = 9 #2.9
        self.maxVel = 70
        self.velScale = .1
        self.accScale = .35
        self.accDefault = 3
        self.groundAcc = 8.4
        self.airAcc = 5

        self.left = self.right = self.jump = self.onGround = self.onWall = False
        self.vel = numpy.array([0.0,0.0])
        self.acc = numpy.array([0.0, self.grav])
    
    def offset(self, x, y):
        offs = numpy.array([x,y])
        self.pos += offs
        self.rect.center = numpy.array(self.rect.center) + offs
    
    def update(self, game):
        self.pos = self.avatar.pos.copy()
        self.rect = self.avatar.rect.copy()

        # update position
        self.pos += self.velScale * self.vel 
        self.processPlatformInteraction()
        
        # update velocity
        self.vel += self.accScale * self.acc
        if abs(self.vel[0]) > self.maxVel and self.acc[0]*self.vel[0] > 0:
            self.acc[0] = 0
        
        # update accelerations based on move actions
        if not (self.left or self.right):
            if (self.onGround):
                self.acc[0] *= -0.2
            else:
                self.acc[0] *= -0.12
        else:
            self.acc[0] = self.groundAcc if self.onGround else self.airAcc
            if self.left: self.acc[0] *= -1
        if self.jump:
            log("jump")
            if self.onGround is True or self.onWall is True:
                self.vel[1] = -100
                self.onGround, self.onWall = False, False
            self.jump = False
        
        return self.pos

    def processPlatformInteraction(self):
        game = self.avatar.game
        a = self
        for p in filter(lambda p: self.rect.colliderect(p.rect), game.level.platforms):
            if p.visible:
                if p.rect.contains(a.rect): break
                if a.rect.bottom > p.rect.top > a.rect.top or a.rect.right > p.rect.left > a.rect.left or a.rect.left < p.rect.right < a.rect.right:
                    a.onGround = True
                if a.rect.top < p.rect.bottom < a.rect.bottom:
                    pass
                while pygame.sprite.collide_rect(a,p):
                    if a.rect.bottom > p.rect.top > a.rect.top:
                        a.offset(0,-1)
                        if a.vel[1] != -100: a.vel[1] = 0
                    if a.rect.right > p.rect.left > a.rect.left and not a.rect.centery < p.rect.top:
                        a.offset(-1,0)
                        a.vel[0] *= -0.7
                    if a.rect.left < p.rect.right < a.rect.right and not a.rect.centery < p.rect.top:
                        a.offset(1,0)
                        a.vel[0] *= -0.7
                    if a.rect.top < p.rect.bottom < a.rect.bottom:
                        a.offset(0,1)
                        a.vel[1] = 0

    def moveLeft(self, status):
        self.left = status
    
    def moveRight(self, status):
        self.right = status
    
    def makeJump(self, status):
        self.jump = status
        
    def run(self, status):
        pass


class MeatBoyMotion(object):
    def __init__(self, avatar):
        self.avatar = avatar        
        
        self.velScale = 0.1
        self.accScale = 0.35
        
        self.grav = 12.0
        
        self.maxHorVel = 50.0
        self.maxHorRunVel = 90.0
        self.groundAcc = 40
        self.airHorAcc = 20.0 # horizontal acceleration while in air
        
        self.jumpSpeed = 100
        self.jumpAcc = self.jumpSpeed / 2.5
        
        self.groundFrictionCoeff = 0.5
        self.wallFriction = 7

        self.left = self.right = self.jump = self.startJump = self.running = False
        self.onGround = self.onWall = self.onLeftWall = self.onRightWall = False
        self.vel = numpy.array([0.0, 0.0])
        self.acc = numpy.array([0.0, 0.0])
        self.accGrav = numpy.array([0.0, self.grav])
        self.accFriction = numpy.array([0.0, 0.0])
    
    def offset(self, x, y):
        self.pos += numpy.array([x,y])
        self.rect.center = self.pos.copy()
        
    def discretise(self, pos):
        return numpy.round(pos)
    
    def update(self, game):
        log.push(False)
        
        self.pos = self.avatar.pos.copy()
        self.rect = self.avatar.rect.copy()

        #log("motion update, initial pos = %s" % str(self.pos))

        # update velocity
        self.vel += self.accScale * (self.acc + self.accGrav + self.accFriction)

        # update position
        offset = self.velScale * self.vel
        self.pos += offset
        self.rect.center = self.discretise(self.pos)
        
        log("after velocity update, pos =", str(self.rect.midbottom), self.pos, offset)

        # process platform interaction, determining onGround
        self.processPlatformInteraction()
        log("after platform interaction, pos =", str(self.rect.midbottom))
        
        log("onGround: %s, onWall: %s, left: %s, right: %s, pos: %s" % (self.onGround, self.onWall, self.left, self.right, self.rect.midbottom))
        
        log.push(indent=2)
        log("vel: %s, acc: %s" % (self.vel, self.acc))
        
        # update velocity and acceleration based on move actions
       
        if not self.jump:
            self.acc[1] = 0.0
        
        maxHorVel = self.maxHorVel if not self.running else self.maxHorRunVel
       
        if self.onGround:
            #self.accFriction[0] = -numpy.sign(self.vel[0]) * 10
            self.accFriction[0] = -self.vel[0] * self.groundFrictionCoeff
            self.accFriction[1] = 0.0
            
            if self.left or self.right:
                self.acc[0] = self.oriented(self.groundAcc)
            else:
                self.acc[0] = 0.0
            self.vel[1] = 0
            
            if self.startJump:
                log("jump")
                self.acc[1] = -self.jumpAcc
                self.onGround = False
                
        elif self.onWall:
            self.acc[0] = 0
            
            self.accFriction[0] = 0.0
            self.accFriction[1] = -numpy.sign(self.vel[1]) * self.wallFriction
            
            if self.startJump:
                if self.onLeftWall:
                    #self.acc[0] = self.groundAcc
                    #self.acc[1] = -self.jumpAcc
                    self.acc[1] = 0
                    self.vel[0] = maxHorVel
                    self.vel[1] = -self.jumpSpeed
                else:                    
                    #self.acc[0] = -self.groundAcc
                    #self.acc[1] = -self.jumpAcc
                    self.acc[1] = 0
                    self.vel[0] = -maxHorVel
                    self.vel[1] = -self.jumpSpeed
            
        else: # in air (jumping)
            self.accFriction = numpy.zeros(2)
            if not (self.left or self.right):
                self.acc[0] = 0
            else:
                self.acc[0] = self.oriented(self.airHorAcc)
                
        log("vel: %s, acc: %s" % (self.vel, self.acc))
        
        if abs(self.vel[0]) > maxHorVel:
            self.vel[0] = maxHorVel * numpy.sign(self.vel[0])
        
        if self.vel[1] < -self.jumpSpeed:
            self.vel[1] = -self.jumpSpeed
            self.acc[1] = 0.0
        
        self.startJump = False

        log.pop(2)
        
        return self.discretise(self.pos)

    def oriented(self, x):
        return x if self.right else -x
            

    def processPlatformInteraction(self):
        log.push(True)
        
        game = self.avatar.game
        self.onGround = False
        
        for p in filter(lambda p: self.rect.colliderect(p.wrect), game.level.platforms):
            if p.visible:
                
                if p.wrect.contains(self.rect): # platform contains avatar completely                    
                    continue
                
                platformRect = p.wrect
                
                horMovement = abs(self.vel[0]) > abs(self.vel[1])
                vertMovement = not horMovement
                
                downShift = platformRect.bottom - self.rect.top if self.rect.bottom > platformRect.bottom > self.rect.top else 0
                upShift = self.rect.bottom - platformRect.top if self.rect.bottom > platformRect.top > self.rect.top else 0
                leftShift = self.rect.right - platformRect.left if self.rect.right > platformRect.left > self.rect.left else 0
                rightShift = platformRect.right - self.rect.left if self.rect.left < platformRect.right < self.rect.right else 0
                
                # never shift in movement direction
                if self.vel[1] > 0: downShift = 0
                elif self.vel[1] < 0: upShift = 0
                if self.vel[0] > 0: rightShift = 0
                elif self.vel[0] < 0: leftShift = 0
                
                log("collide", downShift, leftShift, rightShift, upShift, "with vel", self.vel)
                
                vertShift = upShift + downShift > 0
                horShift = leftShift + rightShift > 0
                
                minShift = min(filter(lambda x: x > 0, [leftShift, rightShift, upShift, downShift])) if vertShift or horShift else 1000
                
                log.push(indent=2)
                if downShift == minShift: #downShift > 0 and (vertMovement or not horShift):
                    log("shifting down")
                    self.offset(0, downShift)                    
                    self.vel[1] = self.acc[1] = 0                    
                elif leftShift == minShift: #leftShift > 0 and (horMovement or not vertShift):
                    log("shifting left")
                    self.offset(-leftShift, 0)                    
                    #self.vel[1] = 0
                    self.vel[0] = self.acc[0] = 0
                elif rightShift == minShift: #rightShift > 0 and (horMovement or not vertShift):
                    log("shifting right")
                    self.offset(rightShift, 0)                    
                    #self.vel[1] = 0
                    self.vel[0] = self.acc[0] = 0
                elif upShift == minShift: #upShift > 0 and (vertMovement or not horShift):
                    log("shifting up")
                    self.offset(0, -upShift)                    
                    self.vel[1] = self.acc[1] = 0
                else:
                    log("not shifting")
                log.pop()
                
        # determine if there are supporting platforms
        r = self.rect.move(0, 1)
        supportingPlatforms = list(filter(lambda p: r.colliderect(p.wrect), game.level.platforms))
        if len(supportingPlatforms) > 0:
            self.onGround = True
            #log("  on supporting plane with top = %s" % supportingPlatforms[0].wrect.top)
        
        # determine wall clinging
        self.onLeftWall = self.onRightWall = False
        if not self.onGround:
            r = self.rect.move(-1, 0)
            if len(list(filter(lambda p: r.colliderect(p.wrect), game.level.platforms))) > 0:
                self.onLeftWall = True
            else:
                r = self.rect.move(1, 0)
                if len(list(filter(lambda p: r.colliderect(p.wrect), game.level.platforms))) > 0:
                    self.onRightWall = True
        self.onWall = self.onRightWall or self.onLeftWall
        
        log.pop()

    def moveLeft(self, status):
        self.left = status
    
    def moveRight(self, status):
        self.right = status
    
    def makeJump(self, status):
        self.jump = status
        if status:
            self.startJump = True
    
    def run(self, status):
        self.running = status
