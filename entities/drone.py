#Do not run this file, it is a module!
import pygame, math, time, random
import entities.base as base

DEFAULT_SIZE = 3 #Defualt upgrade slots for a drone

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.settings["health"] = random.randint(10,40) #Health of the drone
        self.settings["maxHealth"] = 100 #Maximum health of the drone
        self.settings["angle"] = 0 #Angle of the drone
        self.settings["name"] = "Name" #Name of the drone
        self.settings["upgrades"] = [] #Default upgrades that should be loaded onto the drone for the first time it is spawned.
        for i in range(DEFAULT_SIZE): #Fill the upgrade slots with empty upgrades
            self.settings["upgrades"].append(["",0])
        self.upgrades = [] #Upgrade objects inside the drone.
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the drone is inside a room
        self.hintMessage = "This is a disabled drone, you can add items, change health and name in the context/options menu."
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["drone",self.ID,self.pos,
            self.settings["angle"]+0,self.settings["health"]+0,self.settings["maxHealth"]+0,
            self.settings["name"]+"",self.settings["upgrades"]]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["angle"] = data[3]
        self.settings["health"] = data[4]+0
        self.settings["maxHealth"] = data[5]+0
        self.settings["name"] = data[6]+""
        self.settings["upgrades"] = data[7]
        self.upgrades = [] #Empty upgrades on the drone
        for a in self.settings["upgrades"]: #Start loading the upgrades as objects rather than strings.
            if a[0]!="":
                self.upgrades.append(self.LINK["upgrade"][a[0]].Main)
                self.upgrades[-1].damage = a[1]+0
    def __AddUpgrade(self,LINK): #Adds a new empty upgrade slot to the drone
        if len(self.__upgrades)>=5: #Maximum limit to the amount of upgrade slots allowed to be on a drone
            return 0
        self.settings["upgrades"].append(["",0]) #Add the upgade to the default upgrade lists
        #Get all the upgrades availible
        adding = ["Empty"]
        for a in self.LINK["upgrade"]:
            if a!="base":
                adding.append(a)
        if len(self.__upgrades)>=3: #Decide if it should put the Combo box left or right
            self.__upgrades.append(self.LINK["screenLib"].ComboBox(105,((len(self.__upgrades)-3)*35)+75,self.LINK,100,adding))
        else:
            self.__upgrades.append(self.LINK["screenLib"].ComboBox(5,(len(self.__upgrades)*35)+75,self.LINK,100,adding))
        self.__rightReload() #Reload the +, - and dmg buttons
    def __RemoveUpgrade(self,LINK): #Removes the last upgrade slot on a drone
        if len(self.__upgrades)<=1: #Needs to be atleast 1 upgrade slot left
            return 0
        self.settings["upgrades"].pop() #Remove the last item of the default upgrades
        self.__upgrades.pop() #Remove the last item of the upgrade combo box list.
        self.__rightReload() #Reload the +, - and dmg buttons
    def __damageUpgrade(self,LINK): #Damages the last upgrade
        self.settings["upgrades"][-1][1]+=1
        if self.settings["upgrades"][-1][1]>2:
            self.settings["upgrades"][-1][1] = 0
    def rightInit(self,surf): #Initialize context menu for map designer
        self.HINT = False
        self.__surface = pygame.Surface((210,215)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__nameI = self.LINK["screenLib"].TextEntry(5,40,self.LINK,200,False,"Input name") #Name input feild
        self.__nameI.text = self.settings["name"]+"" #Put the name of the drone into the name feild
        self.__health = self.LINK["screenLib"].TextEntry(5,180,self.LINK,80,False,"HP") #Health input feild
        self.__health.text = str(self.settings["health"]) #Put the health of the drone into the input feild
        self.__label = self.LINK["screenLib"].Label(90,180,self.LINK,"/") #Put a label in between the two text feilds for drone health
        self.__maxHealth = self.LINK["screenLib"].TextEntry(120,180,self.LINK,80,False,"Max HP") #Maximum drone HP
        self.__maxHealth.text = str(self.settings["maxHealth"]) #Put the maximum drone HP in.
        self.__upgrades = [] #Used to store the upgrades widgets. This is a list of combo boxes
        #Get all the possible entities
        adding = ["Empty"]
        for a in self.LINK["upgrade"]:
            if a!="base":
                adding.append(a)
        for i,a in enumerate(self.settings["upgrades"]):
            self.__upgrades.append(self.LINK["screenLib"].ComboBox(5+(int(i/3)*100),(i*35)+75-(int(i/3)*105),self.LINK,100,adding))
            if self.settings["upgrades"][i][0]!="":
                self.__upgrades[-1].select = adding.index(self.settings["upgrades"][i][0])
        del adding #Remove all the items to fix memory leaking.
        self.__rightReload() #Load the +, - and dmg button
    def __rightReload(self): #Reload some menu stuff
        if len(self.__upgrades)>=3: #Right
            self.__addButton = self.LINK["screenLib"].Button(105,((len(self.__upgrades)-3)*35)+75,self.LINK,"+",self.__AddUpgrade)
            self.__remButton = self.LINK["screenLib"].Button(125,((len(self.__upgrades)-3)*35)+75,self.LINK,"-",self.__RemoveUpgrade)
            self.__dmgButton = self.LINK["screenLib"].Button(150,((len(self.__upgrades)-3)*35)+75,self.LINK,"Dmg",self.__damageUpgrade)
        else: #Left
            self.__addButton = self.LINK["screenLib"].Button(5,(len(self.__upgrades)*35)+75,self.LINK,"+",self.__AddUpgrade)
            self.__remButton = self.LINK["screenLib"].Button(25,(len(self.__upgrades)*35)+75,self.LINK,"-",self.__RemoveUpgrade)
            self.__dmgButton = self.LINK["screenLib"].Button(50,(len(self.__upgrades)*35)+75,self.LINK,"Damage",self.__damageUpgrade)
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__nameI.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__addButton.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__remButton.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__dmgButton.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__health.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__maxHealth.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        for a in self.__upgrades: #Event loop for all the upgade widgets
            a.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
    def rightRender(self,x,y,surf): #Render the context menu
        windowPos = [x,y+50] #Window position
        #The 4 IF statments below will make sure the context menu is allways on the screen, even if this entity is not.
        if windowPos[0]<300:
            windowPos[0] = 300
        if windowPos[0]>self.LINK["reslution"][0]-150:
            windowPos[0] = self.LINK["reslution"][0]-150
        if windowPos[1]<10:
            windowPos[1] = 10
        if windowPos[1]>self.LINK["reslution"][1]-230:
            windowPos[1] = self.LINK["reslution"][1]-230
        self.__surface.fill((0,0,0)) #Empty the context menu surface
        self.__but1.render(self.__but1.pos[0],self.__but1.pos[1],1,1,self.__surface) #Render delete button
        self.__nameI.render(self.__nameI.pos[0],self.__nameI.pos[1],1,1,self.__surface) #Render name input
        self.__addButton.render(self.__addButton.pos[0],self.__addButton.pos[1],1,1,self.__surface) #Render adding button
        self.__remButton.render(self.__remButton.pos[0],self.__remButton.pos[1],1,1,self.__surface) #Render remove button
        self.__dmgButton.render(self.__dmgButton.pos[0],self.__dmgButton.pos[1],1,1,self.__surface) #Render damage button
        self.__health.render(self.__health.pos[0],self.__health.pos[1],1,1,self.__surface) #Render health input area
        self.__label.render(self.__label.pos[0],self.__label.pos[1],1,1,self.__surface) #Render label
        self.__maxHealth.render(self.__maxHealth.pos[0],self.__maxHealth.pos[1],1,1,self.__surface) #Render max health input feild
        for i,a in enumerate(self.__upgrades): #Render all the upgrade widgets
            #Get a colour for the damage icon, some of these will flash
            if self.settings["upgrades"][i][1]==0: #Working
                col = (0,127+abs(math.cos(time.time()*3)*127),0)
            elif self.settings["upgrades"][i][1]==1: #Small damage
                col = (127+abs(math.cos(time.time()*3)*127),127+abs(math.cos(time.time()*3)*127),0)
            elif self.settings["upgrades"][i][1]==2: #Heavy damage
                col = (127+abs(math.cos(time.time()*3)*127),0,0)
            else:
                col = (255,255,255) #Error colour
            a.render(a.pos[0],a.pos[1],1,1,self.__surface) #Draw the widget
            #Draw the damage rating over the upgrade widget.
            if i>2:
                pygame.draw.rect(self.__surface,col,[105,((i-3)*35)+75,100,30],2)
            else:
                pygame.draw.rect(self.__surface,col,[5,(i*35)+75,100,32],2)
        surfSize = self.__surface.get_size() #Get the size of the context menu
        self.__lastRenderPos = [windowPos[0]-int(surfSize[0]/2),windowPos[1]] #Used for event loops
        pygame.draw.polygon(surf,(0,255,0),[ [windowPos[0]-int(surfSize[0]/3),windowPos[1]],
                                             [x,y],
                                             [windowPos[0]+int(surfSize[0]/3),windowPos[1]] ],2) #This is the triangle pointing from the menu to the entity
        pygame.draw.rect(self.__surface,(0,255,0),[1,1,208,surfSize[1]-3],2) #Outline rectangle
        surf.blit(self.__surface,self.__lastRenderPos) #Draw all results to the screen
    def rightUnload(self): #This delets the pygame surface and widget classes. This is mainly so theirs no memory leaks.
        self.__surface = None
        self.__but1 = None
        if self.__nameI.text!="": #Replace the drones name if anything was entered
            self.settings["name"] = self.__nameI.text+""
        self.__nameI = None
        self.__addButton = None
        self.__remButton = None
        self.__dmgButton = None
        if self.__health.text.isnumeric(): #Replace the health of the drone if something numerical was entered
            self.settings["health"] = int(self.__health.text)
        self.__health = None
        if self.__maxHealth.text.isnumeric(): #Same as the IF statement before but for max health
            self.settings["maxHealth"] = int(self.__maxHealth.text)
        if self.settings["health"]>self.settings["maxHealth"]:
            self.settings["health"] = self.settings["maxHealth"]+0
        self.__maxHealth = None
        self.__label = None
        #Get all the possible entities
        adding = ["Empty"]
        for a in self.LINK["upgrade"]:
            if a!="base":
                adding.append(a)
        #Put the contents of all the upgrade widgets back into the default upgrade slots.
        for i,a in enumerate(self.__upgrades):
            if a.select==0:
                self.settings["upgrades"][i] = ["",0]
            else:
                self.settings["upgrades"][i][0] = adding[a.select]+""
        self.__upgrades = None
    def editMove(self,ents): #Fuel outlet is being moved
        self.__inRoom = type(self.insideRoom(ents)) != bool
    def giveError(self,ents): #Scans and gives an error out
        if type(self.insideRoom(ents)) == bool: #Check if inside a room
            return "No room (drone)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if edit:
            if self.__inRoom:
                if self.settings["health"] == 0:
                    surf.blit(self.getImage("droneDead"),(x,y))
                else:
                    surf.blit(self.getImage("droneNormal"),(x,y))
            else:
                surf.blit(self.getImage("droneDisabled"),(x,y))
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
