import pygame,client,time,screenLib,math,os,sys,render,importlib
pygame.init()

FPS = 30 #Default FPS
RESLUTION = [1000,700]

def ERROR(*info): #This function is called whenever an unexspected error occures. It is mainly so it can be displayed on the screen without the game crashing
    print("Err: ",info) #Tempory
    if LINK["DEV"]: #If in development mode then exit the game
        pygame.quit()
        sys.exit(1)
def ADDLOG(mes): #Used to show logs (used for console)
    print(mes)
def loadScreen(name): #Loads a screen
    global currentScreen
    if name in LINK["screens"]: #Screen exists
        ADDLOG("Loading screen - "+name)
        currentScreen = LINK["screens"][name].Main(LINK)
        ADDLOG("Loaded!")
        LINK["currentScreen"] = currentScreen
    else:
        ERROR("Attempt to load a screen that doesen't exist '"+name+"'")

LINK = {} #This is a global variable for allowing controll over the whole program through one variable. Every class in this program should have a link to this!
LINK["errorDisplay"] = ERROR #Used to show errors
LINK["reslution"] = RESLUTION #Reslution of the game
LINK["DEV"] = True #Development mode, this will stop the game when errors occur.
LINK["loadScreen"] = loadScreen #Used so other scripts can load the map
LINK["render"] = render #Used so other scripts can use its tools for rendering
LINK["screenLib"] = screenLib #Used as a GUI tool for the map designer
LINK["log"] = ADDLOG #Used to log infomation (not seen in game unless developer console is turned on)

main = pygame.display.set_mode(RESLUTION)
pygame.display.set_caption("REMOTE")
clock = pygame.time.Clock()
currentScreen = None #The currently open screen
LINK["currentScreen"] = currentScreen
LINK["main"] = main #Main pygame window
#Fonts
LINK["font24"] = pygame.font.Font("comandFont.ttf",24)
LINK["font16"] = pygame.font.Font("comandFont.ttf",16)
LINK["font42"] = pygame.font.Font("comandFont.ttf",42)
#Controlls (can be changed)
LINK["controll"] = {} #Used to let controlls for the game be changable
LINK["controll"]["up"] = pygame.K_UP #Up arrow key
LINK["controll"]["down"] = pygame.K_DOWN #Down arrow key
LINK["controll"]["left"] = pygame.K_LEFT #Left arrow key
LINK["controll"]["right"] = pygame.K_RIGHT #Right arrow key
LINK["mesh"] = {} #Used for fast entity discovery
LINK["multi"] = 1 #Is the game currently multiplayer, 0 = Single player, 1 = Client, 2 = Server

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
    def loop(self,lag):
        pass
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

LINK["drones"] = [] #Drone list of the players drones
for i in range(0,3):
    LINK["drones"].append(LINK["ents"]["drone"].Main(i*60,0,LINK,-2-i))
LINK["shipEnt"] = LINK["ents"]["ship"].Main(0,0,LINK,-1)

if LINK["multi"]:
    CLI = client.Client("192.168.1.136")
    LINK["cli"] = CLI
loadScreen("game") #Load the main game screen (TEMPORY)
#currentScreen.open("Testing map.map") #Open the map for the game (TEMPORY)

run = True
lastTime = time.time()-0.1
while run:
    lag = (time.time()-lastTime)*30
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
    if LINK["multi"]==1:
        CLI.loop()
        if not CLI.loading and not currentScreen.mapLoading and not currentScreen.mapLoaded:
            currentScreen.joinGame()
            print("CALL LOADING")
    if not currentScreen is None:
        try:
            currentScreen.loop(mouse,KeyEvent,lag)
        except:
            if LINK["DEV"]:
                raise
            ERROR("Error inside screen event loop",sys.exc_info())
    main.fill((0,0,0))
    if not currentScreen is None:
        try:
            currentScreen.render(main)
        except:
            if LINK["DEV"]:
                raise
            ERROR("Error when rendering screen",sys.exc_info())
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
