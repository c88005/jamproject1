import math
import json
import random
import pygame
import datetime
from os import path


def textureAtlas(texture, x0, y0, x1, y1, resize=False, size=1):
    newTexture = pygame.image.load(texture)
    if resize:
        newnew = newTexture.subsurface((x0, y0, x1, y1))
        rect = newnew.get_rect()
        a = pygame.transform.scale(newnew, (rect[2]*size, rect[3]*size))
        return a

    else:
        return newTexture.subsurface((x0, y0, x1, y1))


def rotateAtCenter(image, angle, x, y):
    rotated_image = pygame.transform.rotate(image, angle)

    return rotated_image

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
        self.relativeSize = self.settings.w / 100
        self.map = Map(None, None, None)
        self.objectManager = ObjectManager(self.screen, self.relativeSize, self.settings, None)
        self.entityManager = EntityManager(self.screen, self.relativeSize, self.settings, None)
        self.player = Player(w/2, h/2, None, 63,
                             textureAtlas("assets/player.png", 0,0,32,32,
                                               True, 3*self.relativeSize/10))
        self.menu = True
        self.settingsOpen = False
        self.bloodOnScreen = 0
        self.paused = False
        self.map.player = self.player
        self.objectManager.map = self.map
        self.entityManager.map = self.map
        self.player.objectManager = self.entityManager
        self.map.objectManager = self.objectManager
        self.map.objectManager = self.entityManager
        self.items = Items(self.map, self.objectManager)
        self.map.items = self.items
        self.objectManager.items = self.items
        self.entityManager.items = self.items

        self.version = "23.08.26 2:18AM"

        if path.isfile("settings.json"):
            self.settings.parse()
            if w is not None and h is not None:
                self.settings.w, self.settings.h = w, h
        else:
            self.settings.save()
        self.snowflakesMenu = []
        self.guiTextures = GuiTextures(self.settings, self.relativeSize)
        self.menuButtons = [[0, self.settings.w/2 - self.relativeSize*12, self.relativeSize*25, self.relativeSize*24, self.relativeSize*8, False],
                            [1, self.settings.w/2 - self.relativeSize*12, self.relativeSize*35, self.relativeSize*24, self.relativeSize*8, False]]

        self.settingsButtons = [
            [0, self.relativeSize * 12, self.relativeSize * 5, self.relativeSize * 2,self.relativeSize * 2, False],
            [1, self.relativeSize * 13, self.relativeSize * 8, self.relativeSize * 2,self.relativeSize * 2, False],
            [2, self.relativeSize * 13, self.relativeSize * 11, self.relativeSize * 2, self.relativeSize * 2, False],
            [3, self.relativeSize * 24, self.relativeSize * 14, self.relativeSize * 2, self.relativeSize * 2, False],
            [4, self.relativeSize * 8, self.relativeSize * 17, self.relativeSize * 2, self.relativeSize * 2, False],
            [5, self.relativeSize * 8, self.relativeSize * 20, self.relativeSize * 2, self.relativeSize * 2, False],
            [6, self.relativeSize * 1, self.relativeSize * 23, self.relativeSize * 16, self.relativeSize * 2, False],
            [7, self.relativeSize * 1, self.relativeSize * 26, self.relativeSize * 16, self.relativeSize * 2, False]]
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)

        self.update()

    def updateScreenSize(self, nw=0, nh=0):
        self.screen = pygame.display.set_mode((nw, nh)) if nw==0 and nh==0 else\
            pygame.display.set_mode((self.settings.w, self.settings.h))

    def gameTick(self):
        if self.paused: return
        self.player.update()
        for entity in self.map.entities:
            entity.update()

    def sendToGame(self):
        self.map.switchRoom()

    def menuDraw(self):
        if random.randint(0, 20) == 20:
            self.snowflakesMenu.append([random.randint(0, self.settings.w), random.randint(0, self.settings.h), 5])
        for flake in self.snowflakesMenu:
            if flake[2] <= 0:
                self.snowflakesMenu.remove(flake)
            else:
                flake[2] -= 1/self.clock.get_fps() if self.clock.get_fps() != 0 else 1/60
            pygame.draw.circle(self.screen, "#FFFFFF", (flake[0], flake[1]), self.relativeSize/2)
            flake[0] += random.randint(-100, 100000)/100000
            flake[1] += random.randint(-1000, 1000)/1000

        self.screen.blit(self.guiTextures.logo, (self.settings.w /2 - self.guiTextures.logo.get_rect()[2]/2, self.relativeSize*5))

        pygame.draw.rect(self.screen, "#FFFFFF", (self.settings.w/2 - self.relativeSize*12, self.relativeSize*25, self.relativeSize*24, self.relativeSize*8), 2)
        pygame.draw.rect(self.screen, "#FFFFFF",
                         (self.settings.w / 2 - self.relativeSize * 12, self.relativeSize * 35, self.relativeSize * 24,
                          self.relativeSize * 8), 2)
        playButtonText = self.ghostText("Play",int(5*self.relativeSize), font="assets/zekton_rg.ttf", systemFont=False)
        settingsButtonText = self.ghostText("Settings",int(5*self.relativeSize), font="assets/zekton_rg.ttf", systemFont=False)
        self.renderExistingText(playButtonText, self.settings.w/2 - playButtonText.get_rect()[2]/2, self.relativeSize*26)
        self.renderExistingText(settingsButtonText, self.settings.w/2 - settingsButtonText.get_rect()[2]/2, self.relativeSize*36)

        if self.settingsOpen:
            self.renderText("Show FPS", self.relativeSize,
                            self.relativeSize * 5,int(2*self.relativeSize), font="assets/zekton_rg.ttf", systemFont=False,
                           )
            pygame.draw.rect(self.screen, "#FFFFFF",
                             (self.relativeSize*12, self.relativeSize * 5,
                              self.relativeSize * 2, self.relativeSize * 2), 0 if self.settings.showFps else 2)

            self.renderText("Show AABB", self.relativeSize,
                            self.relativeSize * 8, int(2 * self.relativeSize), font="assets/zekton_rg.ttf",
                            systemFont=False,
                            )
            pygame.draw.rect(self.screen, "#FFFFFF",
                             (self.relativeSize * 13, self.relativeSize * 8,
                              self.relativeSize * 2, self.relativeSize * 2), 0 if self.settings.showAABB else 2)
            self.renderText("Show Blood", self.relativeSize,
                            self.relativeSize * 11, int(2 * self.relativeSize), font="assets/zekton_rg.ttf",
                            systemFont=False,
                            )
            pygame.draw.rect(self.screen, "#FFFFFF",
                             (self.relativeSize * 13, self.relativeSize * 11,
                              self.relativeSize * 2, self.relativeSize * 2), 0 if self.settings.showBlood else 2)
            self.renderText("Show Low Health Blood", self.relativeSize,
                            self.relativeSize * 14, int(2 * self.relativeSize), font="assets/zekton_rg.ttf",
                            systemFont=False,
                            )
            pygame.draw.rect(self.screen, "#FFFFFF",
                             (self.relativeSize * 24, self.relativeSize * 14,
                              self.relativeSize * 2, self.relativeSize * 2), 0 if self.settings.showBloodOnScreen else 2)

            self.renderText("Sound", self.relativeSize,
                            self.relativeSize * 17, int(2 * self.relativeSize), font="assets/zekton_rg.ttf",
                            systemFont=False,
                            )
            pygame.draw.rect(self.screen, "#FFFFFF",
                             (self.relativeSize * 8, self.relativeSize * 17,
                              self.relativeSize * 2, self.relativeSize * 2),
                             0 if self.settings.sound else 2)
            self.renderText("Music", self.relativeSize,
                            self.relativeSize * 20, int(2 * self.relativeSize), font="assets/zekton_rg.ttf",
                            systemFont=False,
                            )
            pygame.draw.rect(self.screen, "#FFFFFF",
                             (self.relativeSize * 8, self.relativeSize * 20,
                              self.relativeSize * 2, self.relativeSize * 2),
                             0 if self.settings.music else 2)
            self.renderText("Sound Volume:"+str(self.settings.soundVolume), self.relativeSize,
                            self.relativeSize * 23, int(2 * self.relativeSize), font="assets/zekton_rg.ttf",
                            systemFont=False,
                            )
            self.renderText("Music Volume:" + str(self.settings.musicVolume), self.relativeSize,
                            self.relativeSize * 26, int(2 * self.relativeSize), font="assets/zekton_rg.ttf",
                            systemFont=False,
                            )

    def ingameGui(self, tc):
        bg1 = tc.bg1
        healthIcon = tc.healthIcon

        self.screen.blit(bg1,(0,self.settings.h-10*self.relativeSize))
        self.screen.blit(healthIcon,(0,self.settings.h-10*self.relativeSize))
        pygame.draw.rect(self.screen, "#ffffff",(10.5*self.relativeSize, self.settings.h-4*self.relativeSize,
                                                 self.relativeSize*7, self.relativeSize/3.5))
        self.renderText(str(math.floor(self.player.health)), 10*self.relativeSize, self.settings.h-10*self.relativeSize,
                        int(5*self.relativeSize), font="assets/zekton_rg.ttf", systemFont=False)
        self.renderText(str(self.player.maxHealth), 11*self.relativeSize, self.settings.h-3.5*self.relativeSize,
                        int(3*self.relativeSize), font="assets/zekton_rg.ttf", systemFont=False)
        if self.player.getSelectedItem() != None:
            if isinstance(self.player.getSelectedItem(), UsableItem):
                self.screen.blit(bg1, (80 * self.relativeSize, self.settings.h - 10 * self.relativeSize))
                self.renderText("Durability: "+str(math.floor(self.player.getSelectedItem().durability)), 80 * self.relativeSize,
                                self.settings.h - 10 * self.relativeSize,
                                int(3 * self.relativeSize), font="assets/zekton_rg.ttf", systemFont=False)
                self.renderText("Amount: " + str(self.player.getSelectedItem().amount), 80 * self.relativeSize,
                                self.settings.h - 5 * self.relativeSize,
                                int(3 * self.relativeSize), font="assets/zekton_rg.ttf", systemFont=False)
        for i in range(self.player.inventorySize):
            if self.player.selectedSlot == i:
                slot = tc.slotSelected
            else:
                slot = tc.slot
            self.screen.blit(slot, (17*self.relativeSize+i*17*self.relativeSize, 0))
            self.renderText("SLOT - " +str(i+1), 17*self.relativeSize+i*17*self.relativeSize + 4.5*self.relativeSize,
                            self.relativeSize * 0.85, int(self.relativeSize*1.6), bold=True)
            if len(self.player.inventory) > i:
                item = self.player.inventory[i]
                self.renderText(item.name,
                                17 * self.relativeSize + i * 17 * self.relativeSize + 0.25 * self.relativeSize,
                                self.relativeSize * 5.5, int(self.relativeSize*1.6), bold=True)
        if self.player.maxHealth / 2 >= self.player.health > self.player.maxHealth/4:
            bgHurt = tc.bgHurt
            self.screen.blit(bgHurt, (0, 0))
        if self.player.health <= self.player.maxHealth/4 and not self.settings.showBloodOnScreen:
            bgHurt = tc.bgHurt
            self.screen.blit(bgHurt, (0, 0))
        if self.settings.showBloodOnScreen:
            if self.player.health <= self.player.maxHealth / 4:
                if self.bloodOnScreen < 255:
                    self.bloodOnScreen += 1
                bgHurtRealBad = tc.bgHurtRealBad
                self.screen.blit(bgHurtRealBad, (0, 0))
            if self.bloodOnScreen > 0 and self.player.health > self.player.maxHealth / 4:
                self.bloodOnScreen -= 1
                bgBlood = tc.bgBlood
                bgBlood.set_alpha(self.bloodOnScreen)
                self.screen.blit(bgBlood, (0, 0))

        if self.settings.showFps:
            self.renderText(str(math.floor(self.clock.get_fps())), 1, 1)
    def update(self):
        print("version: " + self.version + " PRE RELEASE (REAL CLOSE)")
        self.settings.playMusic("assets/sounds/music/Menu.ogg")
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEWHEEL and self.menu == False:
                    if event.y > 0:
                        self.player.changeSlot(-1)
                    if event.y < 0:
                        self.player.changeSlot(1)
            self.screen.fill((0,0,0))
            if self.menu == False:
                self.gameTick()

                for tile in self.map.floorTiles:
                    tile.draw()
                if self.settings.showBlood:
                    for effect in self.map.effects:
                        effect.draw()
                self.player.draw()
                for entity in self.map.entities:
                    entity.draw()


                for object in self.map.objects:
                    object.draw()
                self.ingameGui(self.guiTextures)
            else:
                self.menuDraw()
            self.keyboardInput()
            self.mouseInput()
            self.clock.tick(self.fpsCap)
            pygame.display.flip()

    def keyboardInput(self):
        keys = pygame.key.get_pressed()
        self.player.movementRotation = 0
        self.player.walkingAnim.playing = False
        if keys[pygame.K_ESCAPE]: self.running = False
        if self.player.isDead == False and self.menu == False:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.player.xd = -self.player.moveSpeed * self.relativeSize / 10
                self.player.movementRotation = math.sin(pygame.time.get_ticks() / 100) * math.pi * 2
                if self.player.getSelectedItem() == None:
                    anim = self.player.walkingAnim.play()
                    self.player.originalTexture = textureAtlas("assets/player.png", anim[0], anim[1], anim[2], anim[3],
                                                               True, 3 * self.objectManager.relativeSize / 10)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.player.xd = self.player.moveSpeed * self.relativeSize / 10
                self.player.movementRotation = math.sin(pygame.time.get_ticks() / 100) * math.pi * 2
                if self.player.getSelectedItem() == None:
                    anim = self.player.walkingAnim.play()
                    self.player.originalTexture = textureAtlas("assets/player.png", anim[0], anim[1], anim[2], anim[3],
                                                               True, 3 * self.objectManager.relativeSize / 10)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.player.yd = -self.player.moveSpeed * self.relativeSize / 10
                self.player.movementRotation = math.sin(pygame.time.get_ticks() / 100) * math.pi * 2
                if self.player.getSelectedItem() == None:
                    anim = self.player.walkingAnim.play()
                    self.player.originalTexture = textureAtlas("assets/player.png", anim[0], anim[1], anim[2], anim[3],
                                                               True, 3 * self.objectManager.relativeSize / 10)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.player.yd = self.player.moveSpeed * self.relativeSize / 10
                self.player.movementRotation = math.sin(pygame.time.get_ticks() / 100) * math.pi * 2
                if self.player.getSelectedItem() == None:
                    anim = self.player.walkingAnim.play()
                    self.player.originalTexture = textureAtlas("assets/player.png", anim[0], anim[1], anim[2], anim[3],
                                                               True, 3 * self.objectManager.relativeSize / 10)
            if keys[pygame.K_1]: self.player.selectedSlot = 0
            if keys[pygame.K_2]: self.player.selectedSlot = 1
            if keys[pygame.K_3]: self.player.selectedSlot = 2
            if keys[pygame.K_4]: self.player.selectedSlot = 3

    def mouseInput(self):
        mouse = pygame.mouse
        pos = mouse.get_pos()
        mouse.set_visible(False)
        x = pos[0]
        y = pos[1]
        showCrosshair = True

        buttons = mouse.get_pressed()
        if self.menu == False:
            if buttons[0]:
                if self.player.getSelectedItem() is not None:
                    item = self.player.getSelectedItem()
                    if isinstance(item, UsableItem):
                        item.onUse()

            for entity in self.map.entities:
                if isinstance(entity, ItemEntity):
                    if entity.x <= x <= entity.x + entity.hitbox[0] and entity.y <= y <= entity.y + entity.hitbox[1]:
                        middlePlayer = (self.player.size*self.relativeSize/10/2)
                        middleEntity = (entity.size*self.relativeSize/10/2)
                        c1 = (math.fabs(self.player.x + middlePlayer) - math.fabs(entity.x + middleEntity)) ** 2
                        c2 = (math.fabs(self.player.y + self.player.hitbox[1]/2) - math.fabs(entity.y + entity.hitbox[1]/2)) ** 2
                        if math.fabs(math.sqrt(c1 + c2)) < self.relativeSize*10:

                            textTest = self.ghostText(entity.item.name,
                                                   int(3*self.relativeSize), font="assets/zekton_rg.ttf", systemFont=False)
                            pygame.draw.rect(self.screen, (0, 0, 0), (x+self.relativeSize*2, y-self.relativeSize*6,
                                                                      textTest.get_rect()[2], self.relativeSize*4))
                            self.renderExistingText(textTest,x+self.relativeSize*2, y-self.relativeSize*6)
                            if buttons[0]:
                                if self.player.addToInventory(entity.item):
                                    self.map.entities.remove(entity)
                                    self.settings.playSound("assets/sounds/bp.ogg", 70)
                        else:
                            showCrosshair = False
                            cantGrab = textureLoader("assets/cantGrab.png", self.relativeSize*5,self.relativeSize*5)
                            self.screen.blit(cantGrab, (x-self.relativeSize*2.5, y-self.relativeSize*2.5))
        else:
            if buttons[0]:
                for button in self.menuButtons:
                    if button[1] <= pos[0] <= button[1]+button[3] and button[2] <= pos[1] <= button[2]+button[4]:

                        if button[0] == 0:
                            self.menu = False
                            self.sendToGame()
                        if button[0] == 1:
                            if button[5] == False:
                                button[5] = True
                                self.settings.playSound("assets/sounds/tracker.ogg", 70)
                                self.settingsOpen = not self.settingsOpen

                        if button[5] == False:
                            button[5] = True
                            self.settings.playSound("assets/sounds/tracker.ogg", 70)
                for sbutton in self.settingsButtons:
                    if sbutton[1] <= pos[0] <= sbutton[1] + sbutton[3] and sbutton[2] <= pos[1] <= sbutton[2] + sbutton[4]:
                        if sbutton[0] == 0:
                            if sbutton[5] == False:
                                self.settings.showFps = not self.settings.showFps
                        if sbutton[0] == 1:
                            if sbutton[5] == False:
                                self.settings.showAABB = not self.settings.showAABB
                        if sbutton[0] == 2:
                            if sbutton[5] == False:
                                self.settings.showBlood = not self.settings.showBlood
                        if sbutton[0] == 3:
                            if sbutton[5] == False:
                                self.settings.showBloodOnScreen = not self.settings.showBloodOnScreen
                        if sbutton[0] == 4:
                            if sbutton[5] == False:
                                self.settings.sound = not self.settings.sound
                        if sbutton[0] == 5:
                            if sbutton[5] == False:
                                self.settings.music = not self.settings.music
                        if sbutton[0] == 6:
                            if sbutton[5] == False:
                                if self.settings.soundVolume == 100:
                                    self.settings.soundVolume = 0
                                else:
                                    self.settings.soundVolume += 10
                        if sbutton[0] == 7:
                            if sbutton[5] == False:
                                if self.settings.musicVolume == 100:
                                    self.settings.musicVolume = 0
                                else:
                                    self.settings.musicVolume += 10

                        if sbutton[5] == False:
                            sbutton[5] = True
                            self.settings.save()
                            self.settings.playSound("assets/sounds/tracker.ogg", 70)
            else:
                for button in self.menuButtons:
                    button[5] = False
                for sbutton in self.settingsButtons:
                    sbutton[5] = False

        if showCrosshair:
            crosshair = textureLoader("assets/crosshair.png", self.relativeSize * 5, self.relativeSize * 5)
            self.screen.blit(crosshair, (x - self.relativeSize * 2.5, y - self.relativeSize * 2.5))



    def ghostText(self, string, size=30, font='Arial', color=(255, 255, 255), alias=True, systemFont=True, bold=False):
        pygame.font.init()
        if systemFont:
            my_font = pygame.font.SysFont(font, size, bold=bold)
        else:
            my_font = pygame.font.Font(font, size)
        text_surface = my_font.render(string, alias, color)
        return text_surface

    def renderText(self, string, x, y, size=30, font='Arial', color=(255, 255, 255), alias=True, systemFont=True, bold=False):
        text_surface = self.ghostText(string, size, font, color, alias, systemFont, bold)
        self.screen.blit(text_surface, (x, y))

    def renderExistingText(self, text_surface, x, y):
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
        self.showBlood = True
        self.showBloodOnScreen = True
        self.showAABB = False

    def playSound(self, sound, volume):
        if self.sound:
            playableSound = pygame.mixer.Sound(sound)
            playableSound.set_volume(self.soundVolume/100 * volume/100)
            playableSound.play()

    def playMusic(self, track):
        if self.music:
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(self.musicVolume/100)
            pygame.mixer.music.play(-1)

    def save(self):
        settingsFile = json.dumps({
            "showAABB":self.showAABB,
            "showFps":self.showFps,
            "showBlood": self.showBlood,
            "showBloodOnScreen": self.showBloodOnScreen,
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
                self.showBlood = settingsFile["showBlood"]
                self.showBloodOnScreen = settingsFile["showBloodOnScreen"]
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
        self.items = None

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
        self.rays = []
        self.effects = []
        self.player = player
        self.deathCount = 0
        self.killCount = 0
        self.seed = 0
        self.roomLayer = 0
        self.roomsLeftTillNextLayer = 0
        self.objectManager = objectManager
        self.gunUnstability = 0
        self.durabilityUnstability = 0
        self.entityManager = entityManager
        self.items = None

    def save(self):
        saveFile = json.dumps({
            "objects": self.objects,
            "entities": self.entities,
            "floor": self.floorTiles,
            "rays": self.rays,
            "player": self.player,
            "deathCount": self.deathCount,
            "killCount": self.killCount,
            "seed": self.seed,
            "roomLayer": self.roomLayer,
            "roomsLeft": self.roomsLeftTillNextLayer,
            "gunUnstability": self.gunUnstability
        })
        today = datetime.datetime.now()
        with open(f"saves/save{today.year}.{today.month}.{today.day}.{today.hour}.{today.minute}.json","x", encoding="utf-8") as save:
            print(saveFile, file=save)

    def switchRoom(self):
        self.objects = []
        self.entities = []
        self.floorTiles = []
        self.rays = []
        self.effects = []
        self.roomLayer +=1
        self.seed = random.randint(-10000, 10000)
        rng = random.Random(self.seed)
        self.gunUnstability = rng.randint(-1000, 1000)
        self.durabilityUnstability = rng.randint(-1000, 1000)

        self.createFloor(0,0,32,32)
        wallsAmount = rng.randint(1, 7)
        enemiesAmount = int(rng.randint(1, 4) * (self.roomLayer/2+1))
        for i in range(wallsAmount):
            self.createWall(rng, 128, 0, 32, 32)
        for i in range(enemiesAmount):
            self.spawnEnemy(rng)
        self.createBounds(160, 0, 32, 32)

    def spawnTable(self, x, y):
        self.objects.append(
            TableObject(x, y,self.objectManager,textureAtlas("assets/terrain.png", 192, 0, 64, 32,
                                     True, 2 * self.objectManager.relativeSize / 9.9)
                        ))
    def createWall(self, rng, x0,y0,x1,y1):
        size = 32 * (2 * self.objectManager.relativeSize / 10)
        centeringX = math.floor((self.objectManager.settings.w - size*14)/2)
        centeringY = math.floor((self.objectManager.settings.h - size*9)/2)
        expansion = rng.randint(1, 5)
        for i in range(expansion):
            replacement = rng.randint(1, 5)
            position = rng.randint(1, 10)
            self.objects.append(
                GameObject(centeringX + position * size + i*size, centeringY + rng.randint(0, 7) * size,
                           self.objectManager, 64,
                           textureAtlas("assets/terrain.png", x0, y0, x1, y1,
                                        True, 2 * self.objectManager.relativeSize / 9.9)
                           ))

    def spawnEnemy(self, rng):
        size = 32 * (2 * self.objectManager.relativeSize / 10)
        centeringX = math.floor((self.objectManager.settings.w - size*14)/2)
        centeringY = math.floor((self.objectManager.settings.h - size*9)/2)
        self.entities.append(EntityHostileBase(centeringX+ size + rng.randint(1, 12)*size, centeringY+ size + rng.randint(1, 7)*size, self.objectManager,
                                                   textureAtlas("assets/enemyBaseballbat.png", 0, 0, 32, 32,
                                                                True, 3 * self.objectManager.relativeSize / 10),
                                                   "assets/enemyBaseballbat.png"))

    def createFloor(self, x0, y0, x1, y1):
        size = math.floor(32 * (2 * self.objectManager.relativeSize / 10))
        centeringX = math.floor((self.objectManager.settings.w - size * 14) / 2)
        centeringY = math.floor((self.objectManager.settings.h - size * 9) / 2)
        for i in range(9):
            for j in range(14):
                self.floorTiles.append(
                    GameObject(centeringX + (j * size), centeringY + i * size, self.objectManager, 0,
                               textureAtlas("assets/terrain.png", x0, y0, x1, y1,
                                            True, 2 * self.objectManager.relativeSize / 10)))

    def createBounds(self, x0, y0, x1, y1):
        size = math.floor(32 * (2 * self.objectManager.relativeSize / 10))
        centeringX = math.floor((self.objectManager.settings.w - size*14)/2)
        centeringY = math.floor((self.objectManager.settings.h - size*9)/2)
        for j in range(14):
            self.objects.append(GameObject(centeringX+(j * size), -size*0.5, self.objectManager, 64,
                                              textureAtlas("assets/terrain.png", x0, y0, x1, y1,
                                                           True, 2 * self.objectManager.relativeSize / 10)))
            self.objects.append(GameObject(centeringX + (j * size), self.objectManager.settings.h - size * 0.5, self.objectManager, 64,
                                           textureAtlas("assets/terrain.png", x0, y0, x1, y1,
                                                        True, 2 * self.objectManager.relativeSize / 10)))
        for i in range(9):
            self.objects.append(GameObject(0, size*i, self.objectManager, 64,
                                              textureAtlas("assets/terrain.png", x0, y0, x1, y1,
                                                           True, 2 * self.objectManager.relativeSize / 10)))
            self.objects.append(GameObject(self.objectManager.settings.w - size, size * i, self.objectManager, 64,
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

    def overlapTuples(self, objectA, objectB):
        return (objectA[2] > objectB[0] and
                    objectA[0] < objectB[2] and
                    objectA[1] < objectB[3] and
                    objectA[3] > objectB[1])

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
    def __init__(self, x, y, objectManager, size, texture, indestructible=True, durability=20):
        self.x = x
        self.y = y
        self.size = size
        self.size2 = size
        self.objectManager = objectManager
        self.texture = texture
        self.hitbox = (size,size)
        self.indestructible = indestructible
        self.hardness = 0
        self.explosionResistance = 0
        self.durability = durability

    def setHitbox(self, x, y):
        self.hitbox = (x*self.objectManager.relativeSize/10,y*self.objectManager.relativeSize/10)

    def setStates(self, hardness=1, explosionResistance=0, durability=100):
        if not self.indestructible:
            self.hardness = hardness
            self.explosionResistance = explosionResistance
            self.durability = durability

    def draw(self):
        self.objectManager.screen.blit(self.texture, (self.x, self.y))
        self.hitbox = (self.size*self.objectManager.relativeSize/10,self.size2*self.objectManager.relativeSize/10)
        if self.objectManager.settings.showAABB:
            pygame.draw.rect(self.objectManager.screen, (255, 255, 255),
                             (self.x, self.y, self.hitbox[0], self.hitbox[1]), 1)
class ItemContainerObject(GameObject):
    def __init__(self, x, y, objectManager, size, texture, health):
        super().__init__(x, y, objectManager, size, texture, False)
        self.items = []
        self.health = health
        self.maxHealth = health

    def addItem(self, itemTuple):
        self.items.append(itemTuple)

    def hurt(self, damage):
        if damage >= self.health:
            self.health = 0
            self.dropItems()
        else:
            self.health -= damage

    def dropItems(self):
        for item in self.items:
            self.objectManager.map.entities.append(ItemEntity(self.x + random.randint(-10, 10)/10 * self.objectManager.relativeSize,
                                                              self.y + random.randint(-10, 10)/10 * self.objectManager.relativeSize,
                                                              self.objectManager, item.clone()))


class TableObject(GameObject):
    def __init__(self, x, y, objectManager, texture):
        super().__init__(x, y, objectManager, 64, texture, False)
        self.size = 128
        self.size2 = 64

class Entity(GameObject):
    def __init__(self, x, y, entityManager, size, size2, texture):
        super().__init__(x,y,entityManager,size,texture,False)
        self.direction = 0
        self.size = size2
        self.size2 = size
        self.health = 100
        self.maxHealth = 100
        self.isDead = False
        self.damageResistance = 10
        self.armor = 0
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
        if self.canBeDamaged:
            if self.hurtTime > 0:
                self.hurtTime -= 1
                return
            newDamage = (damage * ((100-self.damageResistance) / 100) + ((math.fabs(attacker.xd) + math.fabs(attacker.yd)) / 2) / 10)

            if self.armor > 0:  newDamage *= (self.armor * 0.1) / 100
            if newDamage > self.health:
                for _ in range(random.randint(1,2)):
                    self.objectManager.map.effects.append(Effect(self.objectManager.screen, textureAtlas("assets/particles.png",
                                                                              random.randint(0,3)*16, 0,
                                                                              16,16, True, 3*self.objectManager.relativeSize/10),
                                                                 self.x + random.randint(-10, 10)/10 * self.objectManager.relativeSize/10,
                                                                 self.y + random.randint(-10, 10)/10 * self.objectManager.relativeSize/10))
                self.health = 0
                self.isDead = True
                self.xd += xd * 2
                self.yd += yd * 2
            else:
                if self.armor > 0:
                    self.armor -= newDamage / 2
                elif self.armor < 0:
                    self.armor = 0
                for _ in range(random.randint(0,1)):
                    self.objectManager.map.effects.append(Effect(self.objectManager.screen, textureAtlas("assets/particles.png",
                                                                              random.randint(0,3)*16, 0,
                                                                              16,16, True, 3*self.objectManager.relativeSize/10),
                                                                 self.x + random.randint(-10, 10)/10 * self.objectManager.relativeSize/10,
                                                                 self.y + random.randint(-10, 10)/10 * self.objectManager.relativeSize/10))
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

    def draw(self):
        self.objectManager.screen.blit(self.texture, (self.x - (self.texture.get_rect()[2]-self.size*self.objectManager.relativeSize/10)/2,
                                                      self.y - (self.texture.get_rect()[3]-self.size2*self.objectManager.relativeSize/10)/2))
        self.hitbox = (self.size*self.objectManager.relativeSize/10,self.size2*self.objectManager.relativeSize/10)
        if self.objectManager.settings.showAABB:
            pygame.draw.rect(self.objectManager.screen, (255, 255, 255),
                             (self.x, self.y, self.hitbox[0], self.hitbox[1]), 1)

class GuiTextures:
    def __init__(self, settings, relativeSize):
        self.settings = settings
        self.relativeSize = relativeSize
        self.logo = textureLoader("assets/logo.png", 22.85*2*self.relativeSize, 4*2*self.relativeSize)
        self.bg1 = pygame.Surface((20*self.relativeSize, 10*self.relativeSize))
        self.healthIcon = textureLoader("assets/health.png", 10*self.relativeSize, 10*self.relativeSize)
        self.bg1.set_alpha(100)
        self.slotSelected = textureLoader("assets/inventorySlotSelected.png", self.relativeSize * 16, self.relativeSize * 8)
        self.slot = textureLoader("assets/inventorySlot.png", self.relativeSize * 16, self.relativeSize * 8)
        self.bgHurt = textureLoader("assets/damaged.png", self.settings.w, self.settings.h).convert_alpha()
        self.bgHurtRealBad = textureLoader("assets/damagedoverlay3NoLag.png", self.settings.w,
                                  self.settings.h).convert_alpha()
        self.bgBlood = textureLoader("assets/damagedoverlay2.png", self.settings.w,
                            self.settings.h).convert_alpha()

class EntityHostileBase(Entity):
    def __init__(self, x, y, entityManager, texture, texturePath):
        super().__init__(x, y, entityManager, 30, 30, texture)
        self.random = random.Random()
        self.damageResistance = self.random.randint(1, 40)
        self.ranged = False
        self.cooldown = 700
        self.reloadCooldown = 3000
        self.attackRange = 4.75
        self.attackDamage = 25
        self.swingSound = "assets/sounds/heavySwing"
        self.swingSoundRandom = 3
        self.knockbackModifier = 0.025
        self.hitSound = "assets/sounds/blunt"
        self.texturePath = texturePath
        self.hitSoundRandom = 1
        self.currentTime = pygame.time.get_ticks()
        self.currentTimeForStun = pygame.time.get_ticks()
        self.stunTime = 0
        self.stunRemoval = 20
        self.angle = 0
        self.originalTexture = texture
        self.movementRotation = 0
        self.hitAnimation = AnimationSequence([(0, 0, 32, 32),(32,0,32,32),(64, 0, 32, 32)], [100,100,500])
        self.deadTextureTuple = (96, 0, 32, 32)
        self.deadTexture = textureAtlas(self.texturePath, self.deadTextureTuple[0], self.deadTextureTuple[1],
                                                self.deadTextureTuple[2], self.deadTextureTuple[3],
                                                True, 3.5 * self.objectManager.relativeSize / 10)

    def rerollArmorStuff(self):
        self.random = random.Random(self.objectManager.map.seed)
        self.damageResistance = self.random.randint(1, 40)

    def update(self):
        super().update()
        if not self.isDead:
            if pygame.time.get_ticks() - self.currentTimeForStun >= self.stunTime:
                if self.stunTime - self.stunRemoval < 0:
                    self.stunTime = 0
                else:
                    self.stunTime -= self.stunRemoval
                self.currentTimeForStun = pygame.time.get_ticks()
                self.AI()
        else:
            self.originalTexture = textureAtlas(self.texturePath, self.deadTextureTuple[0], self.deadTextureTuple[1],
                                                self.deadTextureTuple[2], self.deadTextureTuple[3],
                                                True, 3.5 * self.objectManager.relativeSize / 10)
            self.texture = rotateAtCenter(self.originalTexture, math.degrees(-self.angle) - 90 + self.movementRotation,
                                          self.x, self.y)

    def AI(self):
        player = self.objectManager.map.player
        entityCX = self.x + self.hitbox[0] / 2
        entityCY = self.y + self.hitbox[1] / 2
        playerCX = player.x + player.hitbox[0] / 2
        playerCY = player.y + player.hitbox[1] / 2
        self.angle = math.atan2(self.y - player.y - self.hitbox[1] / 2,
                                self.x - player.x - self.hitbox[0] / 2)
        self.movementRotation = math.sin(pygame.time.get_ticks() / 100) * math.pi * 2
        self.texture = rotateAtCenter(self.originalTexture, math.degrees(-self.angle) + 90 + self.movementRotation,
                                      self.x, self.y)
        stepSize = self.moveSpeed * self.objectManager.relativeSize / 10

        angle = math.atan2(playerCY - entityCY, playerCX - entityCX)
        desiredXD = math.cos(angle) * stepSize
        desiredYD = math.sin(angle) * stepSize

        if hasattr(self, 'xd') and hasattr(self, 'yd'):

            if self.xd == 0.0 and abs(desiredXD) > 0.01:
                desiredXD = 0.0

                if playerCY > entityCY:
                    desiredYD = stepSize
                else:
                    desiredYD = -stepSize

                desiredXD += (1.0 if playerCX > entityCX else -1.0) * (self.objectManager.relativeSize / 50)

            elif self.yd == 0.0 and abs(desiredYD) > 0.01:
                desiredYD = 0.0

                if playerCX > entityCX:
                    desiredXD = stepSize
                else:
                    desiredXD = -stepSize

                desiredYD += (1.0 if playerCY > entityCY else -1.0) * (self.objectManager.relativeSize / 50)

        distance = math.sqrt((playerCX - entityCX) ** 2 + (playerCY - entityCY) ** 2)
        if distance <= self.attackRange * self.objectManager.relativeSize:
            self.attack()
        if distance > stepSize:
            self.xd = desiredXD
            self.yd = desiredYD
        else:
            self.xd = 0.0
            self.yd = 0.0

        if pygame.time.get_ticks() - self.currentTime < self.cooldown:
            anim = self.hitAnimation.play()
            self.originalTexture = textureAtlas(self.texturePath, anim[0], anim[1], anim[2], anim[3],
                                                  True, 3 * self.objectManager.relativeSize / 10)
        else:
            self.originalTexture = textureAtlas(self.texturePath, 0, 0,
                                                  32, 32,
                                                  True, 3 * self.objectManager.relativeSize / 10)

    def attack(self):
        if self.ranged:
            pass
        else:
            if pygame.time.get_ticks() - self.currentTime >= self.cooldown:
                player = self.objectManager.map.player
                self.currentTime = pygame.time.get_ticks()
                self.objectManager.settings.playSound(f"{self.swingSound}{random.randint(1, self.swingSoundRandom)}.ogg",
                                                        80)
                angle = math.atan2(player.y - self.y, player.x - self.x)
                sin = math.sin(angle) * self.attackRange * self.objectManager.relativeSize
                cos = math.cos(angle) * self.attackRange * self.objectManager.relativeSize

                range = self.attackRange * self.objectManager.relativeSize
                playerSize = self.size * self.objectManager.relativeSize / 10
                playerSize2 = self.size2 * self.objectManager.relativeSize / 10

                selfPos = (self.x + cos - range + playerSize / 2, self.y + sin - range + playerSize / 2,
                             self.x + playerSize + cos + range + playerSize / 2,
                             self.y + playerSize2 + sin + range + playerSize / 2)
                playerPos = (player.x, player.y, player.x + player.hitbox[0], player.y + player.hitbox[0])
                if self.objectManager.settings.showAABB:
                    pygame.draw.rect(self.objectManager.screen, "#FFFFFF",
                                     (playerPos[0], playerPos[1], playerSize + range, playerSize2 + range), 2)

                if AABB().overlapTuples(selfPos, playerPos):
                    self.objectManager.settings.playSound(f"{self.hitSound}{random.randint(1, self.hitSoundRandom)}.ogg",
                                                            80)
                    player.hurt(self, self.attackDamage, 0, cos * self.knockbackModifier, sin * self.knockbackModifier)

class Effect:
    def __init__(self, screen, texture, x, y):
        self.screen = screen
        self.texture = texture
        self.x = x
        self.y = y

    def draw(self):
        self.screen.blit(self.texture, (self.x, self.y))

class Ray:
    def __init__(self, x0, y0, x1, y1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def rayCast(self, stepSize, relativeSize, map, entityClass, entityExcluded):
        stepSize *= relativeSize
        angle = math.atan2(self.y1 - self.y0, self.x1 - self.x0)
        c1 = (self.x0 - self.x1) ** 2
        c2 = (self.y0 - self.y1) ** 2
        d1 = math.sqrt(c1 + c2)
        d2 = d1/stepSize
        cos = math.cos(angle) * stepSize,
        sin = math.sin(angle) * stepSize,
        for i in range(math.floor(d2)):
            sx = self.x0 + cos[0] * i
            sy = self.y0 + sin[0] * i
            for object in map.objects:
                if object.x < sx < object.x + object.hitbox[0] and object.y < sy < object.y + object.hitbox[1]:
                    return object, cos[0], sin[0]
            if entityClass == Player:
                player = map.player
                if player.x < sx < player.x + player.hitbox[0] and player.y < sy < player.y + player.hitbox[1]:
                    return player, cos[0], sin[0]
            else:
                for entity in map.entities:
                    if isinstance(entity, entityExcluded): continue
                    if (isinstance(entity, entityClass) and entity.x < sx < entity.x + entity.hitbox[0] and
                            entity.y < sy < entity.y + entity.hitbox[1]):
                        return entity, cos[0], sin[0]

        return None, None, None


class ItemEntity(Entity):
    def __init__(self, x, y, entityManager, itemClass):

        super().__init__(x,y,entityManager,32, 32, itemClass.texture)
        self.canBeDamaged = False
        self.item = itemClass.clone()

class Items:
    def __init__(self, map, objectManager):
        self.items = [FirearmItem(map, textureAtlas("assets/items.png", 16, 0, 16, 16,True,
                                                   2 * objectManager.relativeSize / 9.9),
                                 ".22 Broomhandle", 0, 1, 100,15, (96,0,32,32), 250,
                                  "assets/sounds/headshot", "assets/sounds/pistol1", None, 2, 2),
                      FirearmItem(map, textureAtlas("assets/items.png", 32, 0, 16, 16, True,
                                                   2 * objectManager.relativeSize / 9.9),
                                 "Caldwell Handcannon", 1, 1, 50,15, (128,0,32,32), 300,
                                  "assets/sounds/headshot", "assets/sounds/shotgun1", None, 2, 15, 12),
                      FirearmItem(map, textureAtlas("assets/items.png", 48, 0, 16, 16, True,
                                                   2 * objectManager.relativeSize / 9.9),
                                 "Parabellum", 2, 1, 250,25, (160,0,32,32), 200,
                                  "assets/sounds/headshot", "assets/sounds/pistol2", None, 2, 1.5),
                      FirearmItem(map, textureAtlas("assets/items.png", 64, 0, 16, 16, True,
                                                   2 * objectManager.relativeSize / 9.9),
                                 "Taurus 689", 3, 1, 150,35, (192,0,32,32), 500,
                                  "assets/sounds/headshot", "assets/sounds/revolver2", None, 2, 1),
                      FirearmItem(map, textureAtlas("assets/items.png", 80, 0, 16, 16, True,
                                                   2 * objectManager.relativeSize / 9.9),
                                 "HW 9 ST", 4, 1, 150,70, (224,0,32,32), 700,
                                  "assets/sounds/headshot", "assets/sounds/revolver1", None, 2, 0),
                      FirearmItem(map, textureAtlas("assets/items.png", 96, 0, 16, 16, True,
                                                   2 * objectManager.relativeSize / 9.9),
                                 "vz. 61 Scorpion", 5, 1, 200,10, (0,32,32,32), 70,
                                  "assets/sounds/headshot", "assets/sounds/smg1", None, 2, 3),
                      FirearmItem(map, textureAtlas("assets/items.png", 112, 0, 16, 16, True,
                                                   2 * objectManager.relativeSize / 9.9),
                                 "MP5k", 6, 1, 300,12, (32,32,32,32), 75,
                                  "assets/sounds/headshot", "assets/sounds/smg3", None, 2, 1),
                      FirearmItem(map, textureAtlas("assets/items.png", 128, 0, 16, 16, True,
                                                   2 * objectManager.relativeSize / 9.9),
                                 "CBJ-MS PDW", 7, 1, 250,35, (64,32,32,32), 50,
                                  "assets/sounds/headshot", "assets/sounds/smg2", None, 2, 2),
                      HealingItem(map, textureAtlas("assets/items.png", 0, 0, 16, 16, True,
                                                   2 * objectManager.relativeSize / 9.9),
                                 "Med Kit", 8, 1, 3, 20, 2500, (96, 64, 32, 32)),
                      MeleeItem(map, textureAtlas("assets/items.png", 176, 0, 16, 16, True,
                                                   2 * objectManager.relativeSize / 9.9),
                                 "Riot Shield", 9, 1, 50, 30, 2.5,
                                (192,32,32,32), AnimationSequence([(192,32,32,32),(0, 64, 32, 32),(224, 32, 32, 32)], [600,100,300]), 1000,
                                "assets/sounds/bluntHeavy","assets/sounds/heavyCharge",
                                1, 1, 1, 500),
                      MeleeItem(map, textureAtlas("assets/items.png", 208, 0, 16, 16, True,
                                                  2 * objectManager.relativeSize / 9.9),
                                "Baseball Bat", 10, 1, 75, 20, 3.5,
                                (96,32,32,32), AnimationSequence([(96, 32, 32, 32),(128,32,32,32),(160, 32, 32, 32)], [100,100,300]), 500,
                                "assets/sounds/blunt","assets/sounds/heavySwing",
                                3, 1, 0.5, 50),
                      ]

class Item:
    def __init__(self, gameMap, texture, name, itemId, amount):
        self.map = gameMap
        self.texture = texture
        self.name = name
        self.itemId = itemId
        self.amount = amount

    def clone(self):
        return Item(self.map, self.texture, self.name, self.itemId, self.amount)

class UsableItem(Item):
    def __init__(self, gameMap, texture, name, itemId, amount, durability):
        super().__init__(gameMap,texture,name,itemId,amount)
        self.durability = durability

    def onUse(self):
        if self.durability - math.fabs(1*self.map.durabilityUnstability/100) <= 0:
            self.amount -= 1
        else:
            self.durability -= math.fabs(1*self.map.durabilityUnstability/100)

    def tick(self):
        pass

    def clone(self):
        return UsableItem(
            self.map, self.texture, self.name, self.itemId, self.amount, self.durability
        )

class HealingItem(UsableItem):
    def __init__(self, gameMap, texture, name, itemId, amount, durability, healAmount, cooldown, playerTexture):
        super().__init__(gameMap, texture, name, itemId, amount, durability)
        self.healAmount = healAmount
        self.cooldown = cooldown
        self.playerTexture = playerTexture
        self.currentTime = pygame.time.get_ticks()

    def tick(self):
        player = self.map.player
        player.originalTexture = textureAtlas("assets/player.png", self.playerTexture[0], self.playerTexture[1],
                                                  self.playerTexture[2], self.playerTexture[3],
                                                True, 3 * player.objectManager.relativeSize / 10)

    def onUse(self):
        if pygame.time.get_ticks() - self.currentTime > self.cooldown:
            super().onUse()
            self.currentTime = pygame.time.get_ticks()
            player = self.map.player
            player.objectManager.settings.playSound("assets/sounds/stim.ogg", 80)
            player.heal(self.healAmount)

    def clone(self):
        return HealingItem(self.map, self.texture, self.name, self.itemId, self.amount, self.durability, self.healAmount, self.cooldown, self.playerTexture)

class MeleeItem(UsableItem):
    def __init__(self,gameMap, texture, name, itemId, amount, durability, attackDamage, attackRange, playerTexture, playerAnimSequence, cooldown, hitSound, swingSound, swingSoundRandom, hitSoundRandom, kbMod, stunFor):
        super().__init__(gameMap, texture, name, itemId, amount, durability)
        self.attackDamage = attackDamage
        self.attackRange = attackRange
        self.playerAnimSequence = playerAnimSequence
        self.hitSound = hitSound
        self.knockbackModifier = kbMod
        self.stunning = stunFor
        self.playerTexture = playerTexture
        self.swingSound = swingSound
        self.swingSoundRandom = swingSoundRandom
        self.hitSoundRandom = hitSoundRandom
        self.cooldown = cooldown
        self.currentTime = pygame.time.get_ticks()

    def tick(self):
        player = self.map.player
        if pygame.time.get_ticks() - self.currentTime < self.cooldown:
            anim = self.playerAnimSequence.play()
            player.originalTexture = textureAtlas("assets/player.png", anim[0], anim[1],anim[2], anim[3],
                                                  True, 3 * player.objectManager.relativeSize / 10)
        else:
            player.originalTexture = textureAtlas("assets/player.png", self.playerTexture[0], self.playerTexture[1],
                                                  self.playerTexture[2], self.playerTexture[3],
                                                True, 3 * player.objectManager.relativeSize / 10)

    def clone(self):
        return MeleeItem(
            self.map, self.texture, self.name, self.itemId, self.amount, self.durability,
            self.attackDamage, self.attackRange, self.playerTexture, self.playerAnimSequence, self.cooldown,
            self.hitSound, self.swingSound, self.swingSoundRandom, self.hitSoundRandom, self.knockbackModifier, self.stunning
        )

    def onUse(self):
        if pygame.time.get_ticks() - self.currentTime >= self.cooldown:
            super().onUse()
            player = self.map.player
            self.currentTime = pygame.time.get_ticks()
            player.objectManager.settings.playSound(f"{self.swingSound}{random.randint(1, self.swingSoundRandom)}.ogg",
                                                    80)
            for entity in self.map.entities:
                if isinstance(entity, ItemEntity): continue
                pos = pygame.mouse.get_pos()
                angle = math.atan2(pos[1] - player.y, pos[0] - player.x)
                sin = math.sin(angle) * self.attackRange * player.objectManager.relativeSize
                cos = math.cos(angle) * self.attackRange * player.objectManager.relativeSize

                range = self.attackRange * player.objectManager.relativeSize
                playerSize = player.size * player.objectManager.relativeSize / 10
                playerSize2 = player.size2 * player.objectManager.relativeSize / 10

                playerPos = (player.x + cos - range + playerSize / 2, player.y + sin - range + playerSize / 2,
                             player.x + playerSize + cos + range + playerSize / 2,
                             player.y + playerSize2 + sin + range + playerSize / 2)
                entityPos = (entity.x, entity.y, entity.x + entity.hitbox[0], entity.y + entity.hitbox[1])
                if self.map.objectManager.settings.showAABB:
                    pygame.draw.rect(self.map.objectManager.screen, "#FFFFFF",
                                 (playerPos[0], playerPos[1], playerSize + range, playerSize2 + range), 2)

                if AABB().overlapTuples(playerPos, entityPos):
                    entity.objectManager.settings.playSound(f"{self.hitSound}{random.randint(1, self.hitSoundRandom)}.ogg",
                                                            80)
                    entity.hurt(player, self.attackDamage, 0, cos*self.knockbackModifier, sin*self.knockbackModifier)
                    entity.stunTime += self.stunning

class FirearmItem(UsableItem):
    def __init__(self,gameMap, texture, name, itemId, amount, durability, attackDamage, playerTexture, cooldown, hitSound, swingSound, swingSoundRandom, hitSoundRandom, accuracy, numberShots=1):
        super().__init__(gameMap, texture, name, itemId, amount, durability)
        self.attackDamage = attackDamage
        self.accuracy = accuracy
        self.numberShots = numberShots
        self.hitSound = hitSound
        self.playerTexture = playerTexture
        self.swingSound = swingSound
        self.swingSoundRandom = swingSoundRandom
        self.hitSoundRandom = hitSoundRandom
        self.cooldown = cooldown
        self.currentTime = pygame.time.get_ticks()

    def tick(self):
        player = self.map.player
        player.originalTexture = textureAtlas("assets/player.png", self.playerTexture[0], self.playerTexture[1],
                                                  self.playerTexture[2], self.playerTexture[3],
                                                True, 3 * player.objectManager.relativeSize / 10)

    def clone(self):
        return FirearmItem(
            self.map, self.texture, self.name, self.itemId, self.amount, self.durability,
            self.attackDamage, self.playerTexture, self.cooldown, self.hitSound,
            self.swingSound, self.swingSoundRandom, self.hitSoundRandom, self.accuracy, self.numberShots
        )

    def onUse(self):
        if pygame.time.get_ticks() - self.currentTime >= self.cooldown:
            super().onUse()
            player = self.map.player
            self.currentTime = pygame.time.get_ticks()
            if self.swingSoundRandom == None:
                player.objectManager.settings.playSound(
                    f"{self.swingSound}.ogg",
                    80)
            else:
                player.objectManager.settings.playSound(
                    f"{self.swingSound}{random.randint(1, self.swingSoundRandom)}.ogg",
                    80, random.randint(20000, 96000))
            for _ in range(self.numberShots):
                rnd = self.accuracy*self.map.objectManager.relativeSize*self.map.gunUnstability/500
                r = (-rnd, rnd) if rnd > 0 else (rnd, -rnd)
                pos = pygame.mouse.get_pos()
                newPos = (pos[0]+random.randint(int(r[0]), int(r[1])), pos[1]+random.randint(int(r[0]), int(r[1])))

                ray = Ray(player.x, player.y, newPos[0], newPos[1])
                result = ray.rayCast(2, player.objectManager.relativeSize, self.map, Entity, ItemEntity)
                pygame.draw.line(self.map.objectManager.screen, "#FFFF33",
                                 (player.x + player.hitbox[0] / 2, player.y + player.hitbox[1] / 2),
                                 (newPos[0], newPos[1]), int(0.25 * self.map.objectManager.relativeSize))
                if isinstance(result[0], Entity):
                    player.objectManager.settings.playSound(
                        f"{self.hitSound}{random.randint(1, self.hitSoundRandom)}.ogg",
                        80)
                    result[0].hurt(player, self.attackDamage, 0, result[1] / 1, result[2] / 1)


class AnimationSequence:
    def __init__(self, sequence, timeSequence):
        self.sequence = sequence
        self.timeSequence = timeSequence
        self.currentTime = pygame.time.get_ticks()
        self.frame = 0
        self.playing = False

    def play(self):
        time = self.timeSequence[self.frame] if isinstance(self.timeSequence, list) else self.timeSequence
        self.playing = True
        if pygame.time.get_ticks() - self.currentTime >= time:
            self.currentTime = pygame.time.get_ticks()
            if self.frame + 1 >= len(self.sequence) :
                self.frame = 0
            else:
                self.frame += 1
            self.playing = False
            return self.sequence[self.frame]
        return self.sequence[self.frame]


class Player(Entity):
    def __init__(self, x, y, entityManager, size, texture):
        super().__init__(x,y,entityManager,30, 30,texture)
        self.inventory = []
        self.originalTexture = texture
        self.inventorySize = 4
        self.selectedSlot = 0
        self.movementRotation = 0
        self.angle = 0
        self.walkingAnim = AnimationSequence([ (32, 0, 32, 32), (0, 0, 32, 32), (64, 0, 32, 32), (0, 0, 32, 32)], 125)

    def update(self):
        super().update()
        if self.isDead:
            self.originalTexture = textureAtlas("assets/player.png", 64, 64, 32, 32,
                                                True, 3.5 * self.objectManager.relativeSize / 10)
            self.texture = rotateAtCenter(self.originalTexture, math.degrees(-self.angle) - 90 + self.movementRotation,
                                          self.x, self.y)

            return
        self.angle = math.atan2(pygame.mouse.get_pos()[1] - self.y-self.hitbox[1]/2, pygame.mouse.get_pos()[0] - self.x-self.hitbox[0]/2)
        if self.getSelectedItem() == None:
            if not self.walkingAnim.playing:
                self.originalTexture = textureAtlas("assets/player.png", 0, 0, 32, 32,
                                                    True, 3 * self.objectManager.relativeSize / 10)
        else:
            item = self.getSelectedItem()
            if isinstance(item, UsableItem):
                item.tick()
        self.texture = rotateAtCenter(self.originalTexture, math.degrees(-self.angle) - 90 + self.movementRotation,
                                      self.x, self.y)
        for item in self.inventory:
            if item.amount <= 0:
                self.inventory.remove(item)



    def move(self, xa, ya):

        super().move(xa, ya)

    def changeSlot(self, value):
        if self.selectedSlot + value > self.inventorySize-1:
            self.selectedSlot = 0
        elif self.selectedSlot + value < 0:
            self.selectedSlot = self.inventorySize-1
        else:
            self.selectedSlot += value

    def getSelectedItem(self):
        if len(self.inventory)-1 >= self.selectedSlot:
            return self.inventory[self.selectedSlot]
        return None

    def addToInventory(self, item):
        if len(self.inventory) + 1 <= self.inventorySize:
            self.inventory.extend([item])
            return True
        return False

    def dropFromInventory(self, slot):
        item = self.inventory[slot]
        self.inventory.remove(item)
        self.objectManager.map.entities.append(item)
        return item



#Game(800,450)
Game(1920,1080)