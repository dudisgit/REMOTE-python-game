name = __name__ == "__main__"
if name:
    print("Importing modules")
import pygame,client,time,screenLib,math,os,sys,render,importlib,traceback,mapGenerator,ctypes

ControllerMoveRate = 0.1 #Times a second to move pointer when controller button is held
class ControllerBase:
    def init(self):
        self.__hold = {} #Used to track controller holding
        self.__change = {"Up":False,"Dw":False,"L":False,"R":False,"BD":False,"ND":False,"QO":False,"S":False,"B":False,"E":False}
        self.keyName = {} #Used for command hints
        self.keyName["menuUp"] = "Up arrow"
        self.keyName["menuDown"] = "Down arrow"
        self.keyName["menuLeft"] = "Left arrow"
        self.keyName["menuRight"] = "Right arrow"
        self.keyName["bfDrone"] = "Left trigger"
        self.keyName["nxDrone"] = "Right trigger"
        self.keyName["qOpen"] = "Quick open"
        self.keyName["select"] = "Select"
        self.keyName["back"] = "Back"
        self.keyName["scem"] = "Scematic view"
        self.keyName["mov"] = "Left trackball"
        self.keyName["aim"] = "Right trackball"
        self.cont.init()
        for a in self.__change:
            self.__hold[a] = -1
    def __holding(self,key):
        if self.__hold[key]!=-1 and self.__change[key]: #Holding and key is down
            if time.time()>self.__hold[key]:
                self.__hold[key] = time.time()+ControllerMoveRate
                return True
        elif self.__hold[key]!=-1: #Still holding
            self.__hold[key] = -1
        if self.__change[key] and self.__hold[key]==-1:
            self.__hold[key] = time.time()+0.4
        return False
    def vibrate(self,duration,perc): #Vibrate the controller
        pass
    def loop(self):
        pass
    def getMenuUpChange(self):
        if self.__change["Up"]!=self.getMenuUp():
            self.__change["Up"] = self.getMenuUp()
            return True
        return self.__holding("Up")
    def getMenuDownChange(self):
        if self.__change["Dw"]!=self.getMenuDown():
            self.__change["Dw"] = self.getMenuDown()
            return True
        return self.__holding("Dw")
    def getMenuLeftChange(self):
        if self.__change["L"]!=self.getMenuLeft():
            self.__change["L"] = self.getMenuLeft()
            return True
        return self.__holding("L")
    def getMenuRightChange(self):
        if self.__change["R"]!=self.getMenuRight():
            self.__change["R"] = self.getMenuRight()
            return True
        return self.__holding("R")
    def beforeDroneChange(self):
        if self.__change["BD"]!=self.beforeDrone():
            self.__change["BD"] = self.beforeDrone()
            return True
        return self.__holding("BD")
    def nextDroneChange(self):
        if self.__change["ND"]!=self.nextDrone():
            self.__change["ND"] = self.nextDrone()
            return True
        return self.__holding("ND")
    def quickOpenChange(self):
        if self.__change["QO"]!=self.quickOpen():
            self.__change["QO"] = self.quickOpen()
            return True
        return self.__holding("QO")
    def selectChange(self):
        if self.__change["S"]!=self.select():
            self.__change["S"] = self.select()
            return True
        return self.__holding("S")
    def backChange(self):
        if self.__change["B"]!=self.back():
            self.__change["B"] = self.back()
            return True
        return self.__holding("B")
    def enterScematicViewChange(self):
        if self.__change["E"]!=self.enterScematicView():
            self.__change["E"] = self.enterScematicView()
            return True
        return self.__holding("E")
class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [("wLeftMotorSpeed", ctypes.c_ushort),
                ("wRightMotorSpeed", ctypes.c_ushort)]
class XBoxController(ControllerBase):
        def __init__(self,cont):
            self.cont = cont
            self.init()
            ####### This is not my code but will setup vibration #######
            xinput = ctypes.windll.xinput1_1
            self.__XInputSetState = xinput.XInputSetState
            self.__XInputSetState.argtypes = [ctypes.c_uint, ctypes.POINTER(XINPUT_VIBRATION)]
            self.__XInputSetState.restype = ctypes.c_uint
            #Source = https://stackoverflow.com/questions/20499946/xbox-360-vibrate-rumble
            self.__vibStart = -1
            self.keyName["qOpen"] = "Y"
            self.keyName["select"] = "A"
            self.keyName["back"] = "B"
            self.keyName["scem"] = "X"
        def vibrate(self,duration,perc): #Vibrate the controller
            vibration = XINPUT_VIBRATION(int(65535*perc), int(32768*perc))
            self.__XInputSetState(0, ctypes.byref(vibration))
            self.__vibStart = time.time()+duration
        def loop(self):
            if time.time()>self.__vibStart and self.__vibStart!=-1:
                self.vibrate(0,0)
                self.__vibStart = -1
        def test(self): #Test if controller has all its buttons
            return self.cont.get_numbuttons()==10 and self.cont.get_numhats()==1 and self.cont.get_numaxes()==5
        def getMovement(self,inMenu=False):
            return [self.cont.get_axis(0),self.cont.get_axis(1)]
        def getAim(self,inMenu=False):
            #Either return a list for x and y or a rotation movement
            return [self.cont.get_axis(4),self.cont.get_axis(3)]
        def getMenuUp(self):
            x,y = self.cont.get_hat(0)
            return y>0.5 and abs(x)<0.5
        def getMenuDown(self):
            x,y = self.cont.get_hat(0)
            return y<-0.5 and abs(x)<0.5
        def getMenuLeft(self):
            x,y = self.cont.get_hat(0)
            return x<-0.5 and abs(y)<0.5
        def getMenuRight(self):
            x,y = self.cont.get_hat(0)
            return x>0.5 and abs(y)<0.5
        def beforeDrone(self):
            return self.cont.get_axis(2)>0.5
        def nextDrone(self):
            return self.cont.get_axis(2)<-0.5
        def quickOpen(self):
            return self.cont.get_button(3)
        def select(self):
            return self.cont.get_button(0)
        def back(self):
            return self.cont.get_button(1)
        def enterScematicView(self):
            return self.cont.get_button(2)
class N64Controller(ControllerBase):
    def __init__(self,cont):
        self.cont = cont
        self.init()
        self.keyName["qOpen"] = "A"
        self.keyName["select"] = "X"
        self.keyName["back"] = "B"
        self.keyName["scem"] = "Y"
        self.keyName["mov"] = "Arrow keys"
        self.keyName["aim"] = "Arrow keys"
    def test(self):
        return self.cont.get_numbuttons()==10 and self.cont.get_numaxes()==2
    def getMovement(self,inMenu=False):
        if inMenu:
            return 0
        else:
            return self.cont.get_axis(1)
    def getAim(self,inMenu=False):
        if inMenu:
            return 0
        else:
            return self.cont.get_axis(0)
    def getMenuUp(self):
        return self.cont.get_axis(1)<-0.5
    def getMenuDown(self):
        return self.cont.get_axis(1)>0.5
    def getMenuLeft(self):
        return self.cont.get_axis(0)<-0.5
    def getMenuRight(self):
        return self.cont.get_axis(0)>0.5
    def beforeDrone(self):
        return self.cont.get_button(4)
    def nextDrone(self):
        return self.cont.get_button(5)
    def quickOpen(self):
        return self.cont.get_button(3)
    def select(self):
        return self.cont.get_button(0)
    def back(self):
        return self.cont.get_button(2)
    def enterScematicView(self):
        return self.cont.get_button(1)
class PS3Controller(ControllerBase):
    def __init__(self,cont):
        self.cont = cont
        self.init()
        self.keyName["qOpen"] = "Triangle"
        self.keyName["select"] = "X"
        self.keyName["back"] = "O"
        self.keyName["scem"] = "Square"
    def test(self):
        return self.cont.get_numbuttons()==15 and self.cont.get_numhats()==1 and self.cont.get_numaxes()==4
    def getMovement(self,inMenu=False):
        return [self.cont.get_axis(0),self.cont.get_axis(1)]
    def getAim(self,inMenu=False):
        return [self.cont.get_axis(2),self.cont.get_axis(3)]
    def getMenuUp(self):
        x,y = self.cont.get_hat(0)
        return y>0.5
    def getMenuDown(self):
        x,y = self.cont.get_hat(0)
        return y<-0.5
    def getMenuLeft(self):
        x,y = self.cont.get_hat(0)
        return x<-0.5
    def getMenuRight(self):
        x,y = self.cont.get_hat(0)
        return x>0.5
    def beforeDrone(self):
        return self.cont.get_button(6) or self.cont.get_button(8)
    def nextDrone(self):
        return self.cont.get_button(7) or self.cont.get_button(9)
    def quickOpen(self):
        return self.cont.get_button(4)
    def select(self):
        return self.cont.get_button(0)
    def back(self):
        return self.cont.get_button(1)
    def enterScematicView(self):
        return self.cont.get_button(3)

CONTROLLERS = {}
CONTROLLERS["Controller (XBOX 360 For Windows)"] = XBoxController
CONTROLLERS["usb gamepad           "] = N64Controller
CONTROLLERS["HJD-X"] = PS3Controller

def reloadControllers(LINK):
    pygame.joystick.init()
    conts = pygame.joystick.get_count()
    LINK["controller"] = None
    if conts!=0:
        controllers = []
        for i in range(conts): #Find a compatable controller
            controller = pygame.joystick.Joystick(i)
            if controller.get_name() in CONTROLLERS:
                controllers.append( pygame.joystick.Joystick(i))
        if len(controllers)!=0:
            LINK["controller"] = CONTROLLERS[controllers[0].get_name()](controllers[0])
            if len(controllers)!=1: #More than 1 controller plugged in
                LINK["controller2"] = CONTROLLERS[controllers[1].get_name()](controllers[1])
if name: #Is the main thread
    print("Loading pygame")
    pygame.init()

    print("Building varaibles")
    FPS = 60 #Default FPS
    RESLUTION = [1200,700]

    def ERROR(*info): #This function is called whenever an unexspected error occures. It is mainly so it can be displayed on the screen without the game crashing
        print("Err: ",info) #Tempory
        traceback.print_exc()
        if LINK["DEV"]: #If in development mode then exit the game
            pygame.quit()
            sys.exit(1)
    def ADDLOG(mes): #Used to show logs (used for console)
        #print(mes)
        pass #Tempory because of a windows 10 bug with printing
    def loadScreen(name,*args): #Loads a screen
        global currentScreen
        if name in LINK["screens"]: #Screen exists
            ADDLOG("Loading screen - "+name)
            currentScreen = LINK["screens"][name].Main(LINK,*args)
            ADDLOG("Loaded!")
            LINK["currentScreen"] = currentScreen
        else:
            ERROR("Attempt to load a screen that doesen't exist '"+name+"'")
    LINK = {} #This is a global variable for allowing controll over the whole program through one variable. Every class in this program should have a link to this!
    LINK["errorDisplay"] = ERROR #Used to show errors
    LINK["reslution"] = RESLUTION #Reslution of the game
    LINK["befRes"] = None #Before reslution
    LINK["DEV"] = False  #Development mode, this will stop the game when errors occur.
    LINK["loadScreen"] = loadScreen #Used so other scripts can load the map
    LINK["render"] = render #Used so other scripts can use its tools for rendering
    LINK["screenLib"] = screenLib #Used as a GUI tool for the map designer
    LINK["log"] = ADDLOG #Used to log infomation (not seen in game unless developer console is turned on)
    LINK["DEVDIS"] = False #Development display
    LINK["showFPS"] = False #If the FPS counter should be shown
    LINK["NPCignorePlayer"] = False #Used for development
    LINK["floorScrap"] = True #Enable/disable floor scrap
    LINK["particles"] = True #Enable/disable particle effects
    LINK["showRooms"] = False #Used by survayor upgade to show rooms and doors
    LINK["popView"] = False #Cause rooms to pop into view (reduced CPU load but ajasent rooms arn't rendered)
    LINK["splitScreen"] = False #Is the game running in split screen?
    LINK["client"] = client
    LINK["hintDone"] = [] #List of hints that are shown

    pygame.joystick.init()
    LINK["controller"] = None
    LINK["controller2"] = None #Player 2 (if two controllers are plugged in)
    reloadControllers(LINK)
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
    LINK["font64"] = pygame.font.Font("comandFont.ttf",64)
    LINK["font128"] = pygame.font.Font("comandFont.ttf",128)
    #Controlls (can be changed)
    LINK["controll"] = {} #Used to let controlls for the game be changable
    LINK["controll"]["up"] = pygame.K_UP #Up arrow key
    LINK["controll"]["down"] = pygame.K_DOWN #Down arrow key
    LINK["controll"]["left"] = pygame.K_LEFT #Left arrow key
    LINK["controll"]["right"] = pygame.K_RIGHT #Right arrow key
    LINK["controll"]["escape"] = pygame.K_ESCAPE #Escaping key for closing menus
    LINK["controll"]["resetScroll"] = pygame.K_BACKSPACE #Reset scroll position in map editor key
    LINK["mesh"] = {} #Used for fast entity discovery
    LINK["upgradeIDCount"] = 0 #ID count for upgrades
    LINK["scrapCollected"] = 0 #Amount of scrap colected
    LINK["fuelCollected"] = 0 #Amount of fuel colected
    LINK["shipData"] = {"fuel":5,"scrap":50,"shipUpgs":[],"maxShipUpgs":2,"reserveUpgs":[],"reserveMax":8,"invent":[],
        "beforeMap":-1,"mapSaves":[],"maxScore":0,"reserve":[],"maxDrones":4,"maxReserve":2,"maxInvent":70} #Data about the players ship
    #Reference:
    #'fuel' - Amount of fuel inside the ship
    #'scrap' - Amount of scrap insdie the ship
    #'shupUpgs' - List of ship upgrades
    #'maxShipUpgs' - Maximum number of ship upgrades allowed on the ship when docked.
    #'reserveUpgs' - Reserve ship upgrades
    #'reserveMax' - Maximum reserve upgrades allowed on the ship
    #'invent' - Upgrade inventory (not on the drones)
    #'beforeMap' - Index of the previously loaded map (stops the same map being played twise)
    #'mapSaves' - Stores info about previously generated maps
    #'maxScore' - Overall score added up each map
    #'reserve' - Drones in reserve
    #'maxDrones' - Maximum number of drones the ship can take on a mission
    #'maxReserve' - Maximum number of reserve drones
    LINK["allPower"] = False #Enable global power, a cheat for development
    LINK["absoluteDoorSync"] = False #Send packets randomly to make doors in SYNC perfectly (bigger the map the more packets)
    LINK["simpleModels"] = False #Enable/disable simple models
    LINK["hints"] = True #Enable game hints or not
    LINK["threading"] = False #Enable/disable cleint-side socket threading
    LINK["backgroundStatic"] = False #Enable/disable background static
    LINK["viewDistort"] = True #Drone view distortion
    LINK["names"] = ["Jeff","Tom","Nathon","Harry","Ben","Fred","Timmy","Potter","Stranger"] #Drone names
    LINK["shipNames"] = ["Franks","Daron","Hassle","SETT","BENZYA"] #Ship names
    LINK["simpleMovement"] = False #Simplified movement
    LINK["commandSelect"] = True #Command selecting window
    LINK["multi"] = 0 #Is the game currently multiplayer, -1 = Map editor, 0 = Single player, 1 = Client, 2 = Server

    print("Loading content")
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
    LINK["content"] = {} #Images
    LINK["models"] = {} #3D models
    for a in files:
        if a[-4:]==".png":
            LINK["content"][a[:-4]] = pygame.image.load("content/"+a)
        elif a[-4:]==".obj":
            LINK["models"][a[:-4]] = render.openModel("content/"+a)
    LINK["cont"] = {} #This is used for storing "content" in LINK but is resized every frame.
    pygame.display.set_icon(LINK["content"]["gameIcon"])
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
    print("Initilazing drones")
    LINK["drones"] = [] #Drone list of the players drones
    for i in range(0,3):
        LINK["drones"].append(LINK["ents"]["drone"].Main(i*60,0,LINK,-2-i,i+1))
    LINK["drones"][0].settings["upgrades"][0] = ["motion",0,-1]
    LINK["drones"][0].settings["upgrades"][1] = ["gather",0,-1]
    LINK["drones"][1].settings["upgrades"][0] = ["generator",0,-1]
    LINK["drones"][2].settings["upgrades"][0] = ["interface",0,-1]
    LINK["drones"][2].settings["upgrades"][1] = ["tow",0,-1]
    LINK["drones"][0].loadUpgrades()
    LINK["drones"][1].loadUpgrades()
    LINK["drones"][2].loadUpgrades()
    LINK["shipEnt"] = LINK["ents"]["ship"].Main(0,0,LINK,-1)
    LINK["shipEnt"].settings["upgrades"][0] = ["remote power",0,-1]
    LINK["shipEnt"].loadUpgrades()

    if LINK["multi"]==1: #Client (tempory)
        CLI = client.Client("127.0.0.1",3746,LINK["threading"])
        LINK["cli"] = CLI
    loadScreen("mainMenu") #Load the main game screen
    #currentScreen.open("ServGen.map")
    print("Going into event loop")
    
    run = True
    lastTime = time.time()-0.1
    while run:
        lag = (time.time()-lastTime)*30
        if lag>6: #Limit to how slow the game can skip
            lag = 6
        lastTime = time.time()
        KeyEvent = [] #A list of key events to send to all users
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP or event.type==pygame.QUIT:
                KeyEvent.append(event)
            if event.type == 6: #Mouse wheel
                KeyEvent.append(event)
        mouseRaw = pygame.mouse.get_pressed()
        mouse = [mouseRaw[0]]+list(pygame.mouse.get_pos())+[mouseRaw[1],mouseRaw[2]]
        if LINK["multi"]==1:
            LINK["cli"].loop()
        if not currentScreen is None:
            try:
                currentScreen.loop(mouse,KeyEvent,lag)
            except:
                if LINK["DEV"]:
                    raise
                ERROR("Error inside screen event loop",sys.exc_info())
        if not LINK["controller"] is None:
            LINK["controller"].loop()
        if not LINK["controller2"] is None:
            LINK["controller2"].loop()
        main.fill((0,0,0))
        if not currentScreen is None:
            try:
                currentScreen.render(main)
            except:
                if LINK["DEV"]:
                    raise
                ERROR("Error when rendering screen",sys.exc_info())
        if LINK["showFPS"]:
            main.blit(LINK["font24"].render("FPS: "+str(int(30/lag)),16,(255,255,255)),[0,0])
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    if LINK["multi"]==1:
        LINK["cli"].close()
