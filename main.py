name = __name__ == "__main__"
if name:
    print("Importing modules")
import pygame,client,time,screenLib,math,os,sys,render,importlib,traceback
if name: #Is the main thread
    print("Loading pygame")
    pygame.init()
    print("Building varaibles")
    FPS = 60 #Default FPS
    RESLUTION = [1000,700]

    def ERROR(*info): #This function is called whenever an unexspected error occures. It is mainly so it can be displayed on the screen without the game crashing
        print("Err: ",info) #Tempory
        if LINK["DEV"]: #If in development mode then exit the game
            pygame.quit()
            traceback.print_exc()
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
    LINK["DEVDIS"] = False #Development display
    LINK["showFPS"] = True #If the FPS counter should be shown
    LINK["NPCignorePlayer"] = False #Used for development
    LINK["floorScrap"] = True #Enable/disable floor scrap
    LINK["particles"] = True #Enable/disable particle effects
    LINK["showRooms"] = False #Used by survayor upgade to show rooms and doors
    LINK["popView"] = False #Cause rooms to pop into view (reduced CPU load but ajasent rooms arn't rendered)
    LINK["hintDone"] = [] #List of hints that are shown

    pygame.joystick.init()
    LINK["controller"] = None
    if pygame.joystick.get_count()!=0:
        LINK["controller"] = pygame.joystick.Joystick(0)
        LINK["controller"].init()
        if LINK["controller"].get_numaxes()!=2:
            LINK["controller"] = None
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
    LINK["controll"]["escape"] = pygame.K_ESCAPE #Escaping key for closing menus
    LINK["controll"]["resetScroll"] = pygame.K_BACKSPACE #Reset scroll position in map editor key
    LINK["mesh"] = {} #Used for fast entity discovery
    LINK["upgradeIDCount"] = 0 #ID count for upgrades
    LINK["scrapCollected"] = 0 #Amount of scrap colected
    LINK["fuelCollected"] = 0 #Amount of fuel colected
    LINK["allPower"] = False #Enable global power, a cheat for development
    LINK["absoluteDoorSync"] = False #Send packets randomly to make doors in SYNC perfectly (bigger the map the more packets)
    LINK["simpleModels"] = False #Enable/disable simple models
    LINK["hints"] = False #Enable game hints or not
    LINK["threading"] = False #Enable/disable cleint-side socket threading
    LINK["backgroundStatic"] = True #Enable/disable background static
    LINK["viewDistort"] = True #Drone view distortion
    LINK["names"] = ["Jeff","Tom","Nathon","Harry","Ben","Fred","Timmy","Potter","Stranger"] #Drone names
    LINK["simpleMovement"] = True #Simplified movement
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
    LINK["drones"][0].settings["upgrades"][1] = ["pry",1,-1]
    LINK["drones"][0].settings["upgrades"][2] = ["gather",1,-1]
    LINK["drones"][1].settings["upgrades"][0] = ["lure",0,-1]
    LINK["drones"][1].settings["upgrades"][1] = ["generator",1,-1]
    LINK["drones"][1].settings["upgrades"][2] = ["speed",1,-1]
    LINK["drones"][2].settings["upgrades"][0] = ["interface",0,-1]
    LINK["drones"][2].settings["upgrades"][1] = ["tow",0,-1]
    LINK["drones"][2].settings["upgrades"][2] = ["stealth",0,-1]
    LINK["drones"][0].loadUpgrades()
    LINK["drones"][1].loadUpgrades()
    LINK["drones"][2].loadUpgrades()
    LINK["shipEnt"] = LINK["ents"]["ship"].Main(0,0,LINK,-1)
    LINK["shipEnt"].settings["upgrades"][0] = ["remote power",1,-1]
    LINK["shipEnt"].settings["upgrades"][1] = ["overload",1,-1]
    LINK["shipEnt"].loadUpgrades()

    if LINK["multi"]==1: #Client
        CLI = client.Client("127.0.0.1",3746,LINK["threading"])
        LINK["cli"] = CLI
    loadScreen("game") #Load the main game screen (TEMPORY)
    if LINK["multi"]!=1:
        currentScreen.open("Testing map.map") #Open the map for the game (TEMPORY)
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
            CLI.loop()
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
        if LINK["showFPS"]:
            main.blit(LINK["font24"].render("FPS: "+str(int(30/lag)),16,(255,255,255)),[0,0])
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    if LINK["multi"]==1:
        LINK["cli"].close()