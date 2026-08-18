import math
import json
import random
import pygame
from os import listdir
import datetime
from os import path
from os.path import isfile, join

from OpenGL_accelerate.wrapper import pyArgConverter
from arcade import print_timings
from pyglm.glm import trunc


def textureAtlas(texture, x0, y0, x1, y1, resize=False, size=1):
    newTexture = pygame.image.load(texture)
    if resize:
        newnew = newTexture.subsurface((x0, y0, x1, y1))
        rect = newnew.get_rect()
        a = pygame.transform.scale(newnew, (rect[2]*size, rect[3]*size))
        return a

    else:
        return newTexture.subsurface((x0, y0, x1, y1))


def textureLoader(texture, sizeX=1, sizeY=1):
    newTexture = pygame.image.load(texture)
    return pygame.transform.scale(newTexture, [sizeX, sizeY])

class Game:
    def __init__(self, w, h, fps=60):
        self.settings = Settings(w, h, fps)
        self.fpsCap = fps

        self.clock = pygame.time.Clock()
        self.running = True
        self.screen = pygame.display.set_mode((w, h))
        pygame.FULLSCREEN = True
        self.relativeSize = self.settings.w / 100
        self.map = Map(None, None, None)
        self.objectManager = ObjectManager(self.screen, self.relativeSize, self.settings, None)
        self.entitymanager = EntityManager(self.screen, self.relativeSize, self.settings, None)
        self.player = Player(w/2, h/2, None, 64,
                             textureAtlas("assets/templaet.png", 0,0,32,32,
                                               True, 2*self.relativeSize/10))
        self.bloodOnScreen = 0
        self.paused = False
        self.map.player = self.player
        self.objectManager.map = self.map
        self.entitymanager.map = self.map
        self.player.objectManager = self.entitymanager
        self.map.objectManager = self.objectManager
        self.map.objectManager = self.entitymanager

        if path.isfile("settings.json"):
            self.settings.parse()
            if w is not None and h is not None:
                self.settings.w, self.settings.h = w, h
        else:
            self.settings.save()

        pygame.mixer.init()
        self.map.switchRoom()

        self.update()

    def updateScreenSize(self, nw=0, nh=0):
        self.screen = pygame.display.set_mode((nw, nh)) if nw==0 and nh==0 else\
            pygame.display.set_mode((self.settings.w, self.settings.h))

    def gameTick(self):
        if self.paused: return
        self.player.update()

    def ingameGui(self):
        bg1 =pygame.Surface((20*self.relativeSize, 10*self.relativeSize))
        bg1.set_alpha(100)
        healthIcon = textureLoader("assets/health.png", 10*self.relativeSize, 10*self.relativeSize)
        self.screen.blit(bg1,(0,self.settings.h-10*self.relativeSize))
        self.screen.blit(healthIcon,(0,self.settings.h-10*self.relativeSize))
        pygame.draw.rect(self.screen, "#ffffff",(10.5*self.relativeSize, self.settings.h-4*self.relativeSize,
                                                 self.relativeSize*7, self.relativeSize/3.5))
        self.renderText(str(self.player.health), 10*self.relativeSize, self.settings.h-10*self.relativeSize,
                        int(5*self.relativeSize), font="assets/zekton_rg.ttf", systemFont=False)
        self.renderText(str(self.player.maxHealth), 11*self.relativeSize, self.settings.h-3.5*self.relativeSize,
                        int(3*self.relativeSize), font="assets/zekton_rg.ttf", systemFont=False)

        if self.player.health <= self.player.maxHealth / 2 and self.player.health > self.player.maxHealth/4:
            bgHurt = textureLoader("assets/damaged.png", self.settings.w, self.settings.h).convert_alpha()
            self.screen.blit(bgHurt, (0, 0))
        if self.player.health <= self.player.maxHealth/4:
            if self.bloodOnScreen < 255:
                self.bloodOnScreen += 1
            bgHurtRealBad = textureLoader("assets/damagedoverlay3NoLag.png",self.settings.w, self.settings.h).convert_alpha()
            self.screen.blit(bgHurtRealBad, (0, 0))
        if self.bloodOnScreen > 0 and self.player.health > self.player.maxHealth/4:
            self.bloodOnScreen -= 1
            bgBlood = textureLoader("assets/damagedoverlay2.png", self.settings.w,
                                          self.settings.h).convert_alpha()
            bgBlood.set_alpha(self.bloodOnScreen)
            self.screen.blit(bgBlood, (0, 0))

        if self.settings.showFps:
            self.renderText(str(math.floor(self.clock.get_fps())), 1, 1)
    def update(self):

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            self.screen.fill((0,0,0))
            self.gameTick()

            self.keyboardInput()
            for tile in self.map.floorTiles:
                tile.draw()
            for object in self.map.objects:
                object.draw()


            self.player.draw()

            self.ingameGui()

            self.clock.tick(self.fpsCap)
            pygame.display.flip()

    def keyboardInput(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]: self.running = False
        if keys[pygame.K_f]: self.player.heal(1)
        if keys[pygame.K_g]: self.player.hurt(self.player, 100,  0, float(random.randint(-100,100))/100, float(random.randint(-100,100))/100)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.player.xd = -self.player.moveSpeed*self.relativeSize/10
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.player.xd = self.player.moveSpeed*self.relativeSize/10
        if keys[pygame.K_UP] or keys[pygame.K_w]: self.player.yd = -self.player.moveSpeed*self.relativeSize/10
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.player.yd = self.player.moveSpeed*self.relativeSize/10

    def renderText(self, string, x, y, size=30, font='Arial', color=(255, 255, 255), alias=True, systemFont=True):
        pygame.font.init()
        if systemFont:
            my_font = pygame.font.SysFont(font, size)
        else:
            my_font = pygame.font.Font(font, size)
        text_surface = my_font.render(string, alias, color)
        self.screen.blit(text_surface, (x, y))


class Settings:
    def __init__(self, w, h, fps):
        self.showFps = False
        self.fpsCap = fps
        self.w = w
        self.h = h
        self.sound = True
        self.music = True
        self.soundVolume = 100
        self.musicVolume = 100
        self.showAABB = False

    def playSound(self, sound, volume):
        if self.sound:
            playableSound = pygame.mixer.Sound(sound)
            playableSound.set_volume(self.soundVolume/100 * volume/100)

    def save(self):
        settingsFile = json.dumps({
            "showAABB":self.showAABB,
            "showFps":self.showFps,
            "width":self.w,
            "height":self.h,
            "sound":self.sound,
            "soundVolume":self.soundVolume,
            "music":self.music,
            "musicVolume":self.musicVolume
        })
        with open(f"settings.json","w+", encoding="utf-8") as save:
            print(settingsFile, file=save)
    def parse(self):
        with open(f"settings.json","r", encoding="utf-8") as read:
            settingsFile = json.load(read)
            try:
                self.showAABB = settingsFile["showAABB"]
                self.showFps = settingsFile["showFps"]
                self.w = settingsFile["width"]
                self.h = settingsFile["height"]
                self.sound = settingsFile["sound"]
                self.soundVolume = settingsFile["soundVolume"]
                self.music = settingsFile["music"]
                self.musicVolume = settingsFile["musicVolume"]
            except BaseException as e:
                print(e)
            read.close()

class Manager:
    def __init__(self, settings):
        self.settings = settings

class ObjectManager(Manager):
    def __init__(self, screen, relativeSize, settings, gameMap):
        super().__init__(settings)
        self.screen = screen
        self.map = gameMap
        self.relativeSize = relativeSize

class EntityManager(ObjectManager):
    def __init__(self, screen, relativeSize, settings, gameMap):
        super().__init__(screen, relativeSize, settings, gameMap)
        self.attributes = {
        }

class Map:
    def __init__(self, player, objectManager, entityManager):
        self.objects = []
        self.entities = []
        self.floorTiles = []
        self.player = player
        self.deathCount = 0
        self.killCount = 0
        self.seed = 0
        self.roomLayer = 0
        self.roomsLeftTillNextLayer = 0
        self.objectManager = objectManager
        self.entityManager = entityManager

    def save(self):
        saveFile = json.dumps({
            "objects": self.objects,
            "entities": self.entities,
            "player": self.player,
            "deathCount": self.deathCount,
            "killCount": self.killCount,
            "seed": self.seed,
            "roomLayer": self.roomLayer,
            "roomsLeft": self.roomsLeftTillNextLayer
        })
        today = datetime.datetime.now()
        with open(f"saves/save{today.year}.{today.month}.{today.day}.{today.hour}.{today.minute}.json","x", encoding="utf-8") as save:
            print(saveFile, file=save)

    def switchRoom(self):
        self.seed = random.randint(-10000, 10000)
        rng = random.Random(self.seed)
        self.createFloor(0,0,32,32)
        wallsAmount = rng.randint(1, 7)
        print(wallsAmount)
        for i in range(wallsAmount):
            self.createWall(rng, 128, 0, 32, 32)

    def createWall(self, rng, x0,y0,x1,y1):
        size = 32 * (2 * self.objectManager.relativeSize / 10)
        centeringX = math.floor((self.objectManager.settings.w - size*14)/2)
        centeringY = math.floor((self.objectManager.settings.h - size*9)/2)
        expansion = rng.randint(1, 3)
        for i in range(expansion):
            replacement = rng.randint(1, 5)
            self.objects.append(
                GameObject(centeringX + rng.randint(1, 10) * size + i*size, centeringY + rng.randint(0, 7) * size,
                           self.objectManager, 64,
                           textureAtlas("assets/terrain.png", x0, y0, x1, y1,
                                        True, 2 * self.objectManager.relativeSize / 9.9)
                           ))

    def createFloor(self, x0, y0, x1, y1):
        size = math.floor(32 * (2 * self.objectManager.relativeSize / 10))
        centeringX = math.floor((self.objectManager.settings.w - size*14)/2)
        centeringY = math.floor((self.objectManager.settings.h - size*9)/2)
        for i in range(9):
            for j in range(14):
                self.floorTiles.append(GameObject(centeringX+(j * size), centeringY+ i * size, self.objectManager, size,
                                                  textureAtlas("assets/terrain.png", x0, y0, x1, y1,
                                                               True, 2 * self.objectManager.relativeSize / 10)))

class AABB:
    def __init__(self):
        pass

    def overlap(self, objectA, objectB):
        return (objectA.x + objectA.hitbox[0] > objectB.x and
                    objectA.x < objectB.x + objectB.hitbox[0] and
                    objectA.y < objectB.y + objectB.hitbox[1] and
                    objectA.y + objectA.hitbox[1] > objectB.y)

    def xClip(self, objectA, objectB, xa):
        if xa > 0:
            if (objectA.x + xa + objectA.hitbox[0] > objectB.x and
                    objectA.x + xa < objectB.x + objectB.hitbox[0] and
                    objectA.y < objectB.y + objectB.hitbox[1] and
                    objectA.y + objectA.hitbox[1] > objectB.y):
                return objectB.x - (objectA.x + objectA.hitbox[0])
        elif xa < 0:
            if (objectA.x + xa < objectB.x + objectB.hitbox[0] and
                    objectA.x + xa + objectA.hitbox[0] > objectB.x and
                    objectA.y < objectB.y + objectB.hitbox[1] and
                    objectA.y + objectA.hitbox[1] > objectB.y):
                return (objectB.x + objectB.hitbox[0]) - objectA.x
        return xa

    def yClip(self, objectA, objectB, ya):
        if ya > 0:
            if (objectA.y + ya + objectA.hitbox[1] > objectB.y and
                    objectA.y + ya < objectB.y + objectB.hitbox[1] and
                    objectA.x < objectB.x + objectB.hitbox[0] and
                    objectA.x + objectA.hitbox[0] > objectB.x):
                return objectB.y - (objectA.y + objectA.hitbox[1])
        elif ya < 0:
            if (objectA.y + ya < objectB.y + objectB.hitbox[1] and
                    objectA.y + ya + objectA.hitbox[1] > objectB.y and
                    objectA.x < objectB.x + objectB.hitbox[0] and
                    objectA.x + objectA.hitbox[0] > objectB.x):
                return (objectB.y + objectB.hitbox[1]) - objectA.y
        return ya

#WIP
class Attribute:
    def __init__(self, statAffection, maxLevel, mutating=False):
        self.name = ""
        self.value = 0
        self.statAffection = statAffection
        self.maxLevel = maxLevel
        self.mutating = mutating
#

class GameObject:
    def __init__(self, x, y, objectManager, size, texture, indestructible=True):
        self.x = x
        self.y = y
        self.size = size
        self.objectManager = objectManager
        self.texture = texture
        self.hitbox = (size,size)
        self.indestructible = indestructible
        self.hardness = 0
        self.explosionResistance = 0

    def setHitbox(self, x, y):
        self.hitbox = (x*self.objectManager.relativeSize/10,y*self.objectManager.relativeSize/10)

    def setStates(self, hardness=1, explosionResistance=0):
        if not self.indestructible:
            self.hardness = hardness
            self.explosionResistance = explosionResistance

    def draw(self):
        self.objectManager.screen.blit(self.texture, (self.x, self.y))
        self.hitbox = (self.size*self.objectManager.relativeSize/10,self.size*self.objectManager.relativeSize/10)
        if self.objectManager.settings.showAABB:
            pygame.draw.rect(self.objectManager.screen, (255, 255, 255),
                             (self.x, self.y, self.hitbox[0], self.hitbox[1]), 1)
class ItemContainerObject(GameObject):
    def __init__(self, x, y, objectManager, size, texture):
        super().__init__(x, y, objectManager, size, texture, False)
        self.items = []



class Entity(GameObject):
    def __init__(self, x, y, entityManager, size, texture):
        super().__init__(x,y,entityManager,size,texture,False)
        self.health = 100
        self.maxHealth = 100
        self.isDead = False
        self.damageResistance = 10
        self.armor = 100
        self.debuffs = []
        self.buffs = []
        self.canBeDamaged = True
        self.hurtTime = 0
        self.moveSpeed = 1.75
        self.xd = 0
        self.yd = 0
        self.infectionLevel = 0
        self.bald = False
        self.drop = []

    def hurt(self,attacker,damage,cooldown,xd,yd):
        if self.hurtTime > 0: return
        newDamage = (damage * (self.damageResistance/100) + math.fabs(((attacker.xd+attacker.yd)/2)/10))

        if self.armor > 0:  newDamage *= (self.armor*0.1)/100
        if newDamage > self.health:
            self.health = 0
            self.isDead = True
            self.xd += xd*2
            self.yd += yd*2
        else:

            self.hurtTime = cooldown
            self.health -= newDamage
            self.xd += xd
            self.yd += yd

    def heal(self,amount):
        if self.health + amount > self.maxHealth:
            self.health = self.maxHealth
        else:
            self.health += amount

    def update(self):
        self.xd *= 0.91
        self.yd *= 0.91
        self.move(self.xd, self.yd)

    def move(self,xa,ya):
        xa_org = xa
        ya_org = ya

        for mapObject in self.objectManager.map.objects:
            xa = AABB().xClip(self, mapObject, xa)
        self.x += xa
        for mapObject in self.objectManager.map.objects:
            ya = AABB().yClip(self, mapObject, ya)
        self.y += ya

        if xa_org != xa:
            self.xd = 0.0
        if ya_org != ya:
            self.yd = 0.0

class Player(Entity):
    def __init__(self, x, y, entityManager, size, texture):
        super().__init__(x,y,entityManager,size,texture)

Game(1920,1080)