import pygame,client,time,screenLib,math,os,sys,render,importlib
pygame.init()

FPS = 30
RESLUTION = [800,500]

def ERROR(*info): #This function is called whenever an unexspected error occures. It is mainly so it can be displayed on the screen without the game crashing
    print("Err: ",info) #Tempory
    if LINK["DEV"]: #If in development mode then exit the game
        pygame.quit()
        sys.exit(1)
def ADDLOG(mes): #Used to show logs (used for console)
    print(mes)
def loadScreen(name): #Loads a screen
    global currentScreen
    if name in LINK["screens"]:
        ADDLOG("Loading screen - "+name)
        currentScreen = LINK["screens"][name].Main(LINK)
        ADDLOG("Loaded!")
        LINK["currentScreen"] = currentScreen
    else:
        ERROR("Attempt to load a screen that doesen't exist '"+name+"'")

LINK = {} #This is a global variable for allowing controll over the whole program through one variable. Every class in this program should have a link to this!
LINK["errorDisplay"] = ERROR
LINK["reslution"] = RESLUTION
LINK["DEV"] = True #Development mode, this will stop the game when errors occur.
LINK["loadScreen"] = loadScreen
LINK["render"] = render
LINK["screenLib"] = screenLib
LINK["log"] = ADDLOG

main = pygame.display.set_mode(RESLUTION)
pygame.display.set_caption("REMOTE")
clock = pygame.time.Clock()
currentScreen = None
LINK["currentScreen"] = currentScreen
LINK["main"] = main
LINK["font24"] = pygame.font.Font("comandFont.ttf",24)

#Load all content from the folders...
#Screens
files = os.listdir("screens")
LINK["screens"] = {}
for a in files:
    if a[-3:]==".py":
        LINK["screens"][a[:-3]] = importlib.import_module("screens."+a[:-3])
#Entities
files = os.listdir("entities")
LINK["ents"] = {}
for a in files:
    if a[-3:]==".py":
        LINK["ents"][a[:-3]] = importlib.import_module("entities."+a[:-3])
#Content
files = os.listdir("content")
LINK["content"] = {}
for a in files:
    if a[-4:]==".png":
        LINK["content"][a[:-4]] = pygame.image.load("content/"+a)
        LINK["content"][a[:-4]].set_colorkey((0,0,0))
LINK["cont"] = {} #This is used for storing "content" in LINK but is resized every frame.
#Maps
LINK["maps"] = os.listdir("maps")
#Upgrades
files = os.listdir("upgrades")
LINK["upgrade"] = {} #Drone upgrades
LINK["shipUp"] = {} #Ship upgrades
for a in files:
    if a[-3:]==".py":
        itm = importlib.import_module("upgrades."+a[:-3])
        if a=="base.py":
            LINK["upgrade"][a[:-3]] = itm
        elif itm.Main(LINK).droneUpgrade:
            LINK["upgrade"][a[:-3]] = itm
        else:
            LINK["shipUp"][a[:-3]] = itm

class NULLENT(LINK["ents"]["base"].Main): #Null entity for keeping the game running when an entity doesen't exist
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK)
        self.ID = ID
        self.settings = {}
        self.pos = [x,y]
        self.size = [50,50]
        self.LINK = LINK
        self.HINT = True
    def editMove(*args):
        pass
    def SaveFile(self):
        return []
    def rightInit(self,surf):
        self.__surface = pygame.Surface((50,50))
        self.__lastRenderPos = [0,0]
    def rightLoop(self,mouse,kBuf):
        pass
    def rightUnload(self):
        self.__surface = None
        self.__lastRenderPos = None
    def rightRender(self):
        pass
    def sRender(self,x,y,scale,surf=None,edit=False):
        self.renderHint(surf,"Null entity, please remove.",[x,y])
LINK["null"] = NULLENT

loadScreen("game")
currentScreen.open("Testing map.map")

run = True
lastTime = time.time()-0.1
while run:
    lag = (time.time()-lastTime)*FPS
    lastTime = time.time()
    KeyEvent = [] #A list of key events to send to all users
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            KeyEvent.append(event)
        if event.type == 6: #Mouse wheel
            KeyEvent.append(event)
    mouseRaw = pygame.mouse.get_pressed()
    mouse = [mouseRaw[0]]+list(pygame.mouse.get_pos())+[mouseRaw[1],mouseRaw[2]]
    if not currentScreen is None:
        try:
            currentScreen.loop(mouse,KeyEvent,lag)
        except:
            ERROR("Error inside screen event loop",sys.exc_info())
    main.fill((0,0,0))
    if not currentScreen is None:
        try:
            currentScreen.render(main)
        except:
            ERROR("Error when rendering screen",sys.exc_info())
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
