import math
import json
import random
import pygame
from os import listdir
import datetime
from os.path import isfile, join


def textureAtlas(texture, x0, y0, x1, y1, resize=False, size=1):
    newTexture = pygame.image.load(texture)
    if resize:
        return pygame.transform.scale(newTexture.subsurface((x0, y0, x1, y1)),
                                      ((x1 - x0) * size, (y1 - y0) * size))
    else:
        return newTexture.subsurface((x0, y0, x1, y1))

class Game:
    def __init__(self, w=1920, h=1080, fps=60):
        self.settings = Settings(w, h, fps)
        self.fpsCap = fps

        self.clock = pygame.time.Clock()
        self.running = True
        self.screen = pygame.display.set_mode((w, h))
        self.relativeSize = self.settings.w / 100

        self.map = Map(None, None, None)
        self.objectManager = ObjectManager(self.screen, self.relativeSize, self.settings, None)
        self.entitymanager = EntityManager(self.screen, self.relativeSize, self.settings, None)
        self.player = Player(w/2, h/2, None, 64,
                             textureAtlas("assets/templaet.png", 0,0,32,32,
                                               True, 2*self.relativeSize/10))

        self.paused = False
        self.map.player = self.player
        self.objectManager.map = self.map
        self.entitymanager.map = self.map
        self.player.objectManager = self.entitymanager
        self.map.objectManager = self.objectManager
        self.map.objectManager = self.entitymanager
        print(self.objectManager)
        self.map.objects.append(GameObject(10, 40, self.objectManager, 32*4,
                                           textureAtlas("assets/templaet.png", 0, 0, 32, 32, True, 4*self.relativeSize/10)))

        self.map.switchRoom()
        self.update()

    def updateScreenSize(self, nw=0, nh=0):
        self.screen = pygame.display.set_mode((nw, nh)) if nw==0 and nh==0 else\
            pygame.display.set_mode((self.settings.w, self.settings.h))

    def gameTick(self):
        if self.paused: return
        self.player.update()

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

            if self.settings.showFps:
                self.renderText(str(math.floor(self.clock.get_fps())), 1, 1)
            self.clock.tick(self.fpsCap)
            pygame.display.flip()

    def keyboardInput(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]: self.running = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.player.xd = -self.player.moveSpeed*self.relativeSize/10
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.player.xd = self.player.moveSpeed*self.relativeSize/10
        if keys[pygame.K_UP] or keys[pygame.K_w]: self.player.yd = -self.player.moveSpeed*self.relativeSize/10
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.player.yd = self.player.moveSpeed*self.relativeSize/10

    def renderText(self, string, x, y, size=30, font='Arial', color=(255, 255, 255), alias=True):
        pygame.font.init()
        my_font = pygame.font.SysFont(font, size)
        text_surface = my_font.render(string, alias, color)
        self.screen.blit(text_surface, (x, y))




class Settings:
    def __init__(self, w, h, fps):
        self.showFps = False
        self.fpsCap = fps
        self.w = w
        self.h = h
        self.sound = True
        self.copyrightedMusic = True
        self.soundVolume = 100
        self.musicVolume = 100
        self.showAABB = False

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
        self.seed = 1
        rng = random.Random(self.seed)
        for i in range(10):
            print(rng.randint(0, 9), end="")
        self.createFloor(0,0,32,32)

    def createFloor(self, x0, y0, x1, y1):
        for i in range(9):
            for j in range(12):
                size = math.floor(32 * (2 * self.objectManager.relativeSize / 10))
                self.floorTiles.append(GameObject((j * size), i * size, self.objectManager, size,
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
        self.solid = True
        self.usable = False

    def setHitbox(self, x, y):
        self.hitbox = (x*self.objectManager.relativeSize/10,y*self.objectManager.relativeSize/10)

    def setStates(self, solid=True, usable=False, hardness=1, explosionResistance=0):
        if not self.indestructible:
            self.hardness = hardness
            self.explosionResistance = explosionResistance
        self.solid = solid
        self.usable = usable

    def draw(self):
        self.objectManager.screen.blit(self.texture, (self.x, self.y))
        self.hitbox = (self.size*self.objectManager.relativeSize/10,self.size*self.objectManager.relativeSize/10)
        if self.objectManager.settings.showAABB:
            pygame.draw.rect(self.objectManager.screen, (255, 255, 255),
                             (self.x, self.y, self.hitbox[0], self.hitbox[1]), 1)

class Entity(GameObject):
    def __init__(self, x, y, entityManager, size, texture):
        super().__init__(x,y,entityManager,size,texture,False)
        self.health = 100
        self.isDead = False
        self.damageResistance = 10
        self.armor = 100
        self.debuffs = []
        self.buffs = []
        self.canBeDamaged = True
        self.hurtTime = 0
        self.moveSpeed = 1.5
        self.xd = 0
        self.yd = 0
        self.infectionLevel = 0
        self.bald = False
        self.drop = []

    def hurt(self,attacker,damage,cooldown,xd,yd):
        if self.hurtTime > 0: return
        newDamage = (damage * (self.damageResistance/100 - 1) + ((attacker.xd+attacker.yd)/2)/10)
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

Game()