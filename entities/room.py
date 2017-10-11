#Do not run this file, it is a module!
import pygame, math, time
import entities.base as base

ROOM_UPDATE_RATE = 14 #Amount of times a second to run physics events on the room

class Main(base.Main):
    def __init__(self,x,y,LINK,ID,number=-1):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.number = number #The room number this room is.
        self.settings["radiation"] = False
        self.settings["scanable"] = True #Is the room scannable
        self.settings["power"] = [] #List of generators room is linked to
        if self.ID<0:
            self.number = 1
            self.settings["scanable"] = False
        self.powered = False#If the room is being powered
        self.poweredBefore = False #Has the room been powered before?
        self.radiation = False #Is the room full of radiation
        self.doors = [] #The doors attached to this room
        self.air = True #Is their air in the room
        self.SCAN = 0 #Scan type
        #0 = Off
        #1 = Safe
        #2 = Error
        #3 = Bad
        self.__drawSurf = pygame.Surface((200,200)) #Surface to draw to when rendering bubbles
        self.__lastUpdate = time.time()+(1/ROOM_UPDATE_RATE) #Used to make sure rooms don't continuesly scan for new entities when in a vacuum every screen refresh
        self.__airBurst = [] #Air vacume circles that expant
        self.__airDone = [] #Doors that have allredey been vacumed
        self.__radDone = [] #Doors that have allredey been filled with radiation
        self.__vacumeAirlocks = [] #A list of airlocks that this room is vacumed because of
        self.__vacumeShortPath = "" #Shortest path to an airlock
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the room is inside anouther room
        self.hintMessage = "A room is a space the drone can move about in, you can resize it using the slanted line at the bottom right"
    def __ChangeRadiation(self,LINK,state): #switches radiation on/off
        self.settings["radiation"] = state == True
    def __LinkTo(self,LINK): #"Link to" button was pressed
        LINK["currentScreen"].linkItem(self,"power") #A bit bodgy but this can only be called in the map designer.
    def __UnlinkAll(self,LINK): #Deletes all links on this entity
        self.settings["power"] = []
    def SyncData(self,data): #Syncs the data with this room
        self.air = data["A"]
        self.powered = data["P"]
        self.radiation = data["R"]
        self.SCAN = data["S"]
        if self.powered:
            self.poweredBefore = True
    def GiveSync(self): #Returns the synced data for this room
        res = {}
        res["A"] = self.air
        res["R"] = self.radiation
        res["P"] = self.powered
        res["S"] = self.SCAN
        return res
    def loop2(self,lag): #Is not a client
        self.powered = False
        for a in self.settings["power"]: #Check all power connections to see if this room is powered
            if a.active:
                self.powered = True
                self.poweredBefore = True
                break
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
        elif self.LINK["multi"]==2: #Server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
        if self.LINK["multi"]!=1: #Is not a client, singple player or server
            self.loop2(lag)
        if time.time()>self.__lastUpdate: #Is not a client, single player or server
            self.__lastUpdate = time.time()+(1/ROOM_UPDATE_RATE)
            if self.air or len(self.__airBurst)!=0: #The room has air inside it
                sz = math.sqrt((self.size[0]**2)+(self.size[1]**2))+50 #Find the maximum distance from one corner to anouther in the room
                rem = []
                ENTS = self.EntitiesInside() #Gets all the entities inside this room
                for a in self.__airBurst: #Simulate all air pickets being vacumed.
                    if a[2]!=-1: #Is not an instant bubble
                        if a[4]==1: #Air bubble
                            a[2] += 8*lag #Increase the bubbles size
                        else: #Radiation bubble
                            a[2] += 1.2*lag #Increase the bubbles size
                    if self.LINK["multi"]!=1: #Is not a client
                        for b in ENTS: #Make all entities inside this bubble get sucked out of the airlock
                            dist = math.sqrt(((b.pos[0]-a[0][0])**2)+((b.pos[1]-a[0][1])**2)) #Distance from the start of the bubble to the door
                            if (dist<=a[2] or a[2]==-1) and ((b.beingSucked == False and a[4]==1) or a[4]==2):
                                if a[4]==1: #Is a normal air bubble
                                    b.suckOutOfAirlock(a[1])
                                elif type(b)==self.getEnt("drone") or b.isNPC: #Damage object
                                    b.takeDamage(lag,"radiation")
                        for b in self.doors: #Find any doors it might be touching
                            dist = math.sqrt(((b.pos[0]-a[0][0])**2)+((b.pos[1]-a[0][1])**2)) #Distance from the start of the bubble to the door
                            if b.settings["open"] and not b.room2 is None and (dist<=a[2] or a[2]==-1) and ((not [a[3],b] in self.__airDone and a[4]==1) or (not [a[3],b] in self.__radDone and a[4]==2)): #Is open and hasn't been visited
                                POS = []
                                #Get the of the start of the air bubble inside the door
                                if type(b)==self.getEnt("door"): #Find air sucktion point on a door
                                    if b.settings["lr"]:
                                        if b.pos[0]<self.pos[0]:
                                            POS = [b.pos[0]+0,b.pos[1]+25]
                                        else:
                                            POS = [b.pos[0]+50,b.pos[1]+25]
                                    else:
                                        if b.pos[1]<self.pos[1]:
                                            POS = [b.pos[0]+25,b.pos[1]+0]
                                        else:
                                            POS = [b.pos[0]+25,b.pos[1]+50]
                                else: #Find air sucktion point on an airlock
                                    if b.settings["dir"]>=2:
                                        if b.pos[0]<self.pos[0]:
                                            POS = [b.pos[0]+0,b.pos[1]+25]
                                        else:
                                            POS = [b.pos[0]+50,b.pos[1]+25]
                                    else:
                                        if b.pos[1]<self.pos[1]:
                                            POS = [b.pos[0]+25,b.pos[1]+0]
                                        else:
                                            POS = [b.pos[0]+25,b.pos[1]+50]
                                #Make a new bubble into anouther room
                                if a[4]==1: #Air bubble
                                    if b.room1 == self:
                                        b.room2.airBurst(POS,a[1]+"/"+str(b.ID),a[3],b)
                                    else:
                                        b.room1.airBurst(POS,a[1]+"/"+str(b.ID),a[3],b)
                                    self.__airDone.append([a[3],b])
                                    self.__airDone.append(b)
                                else: #Radiation bubble
                                    if b.room1 == self:
                                        b.room2.radBurst(POS)
                                    else:
                                        b.room1.radBurst(POS)
                                    self.__radDone.append([a[3],b])
                                    self.__radDone.append(b)
                            elif not b.settings["open"] and (([a[3],b] in self.__airDone and a[4]==1) or ([a[3],b] in self.__radDone and a[4]==2)): #Door has been closed, remove it from the list of done doors
                                if a[4]==1: #Is an air bubble
                                    self.__airDone.remove([a[3],b])
                                    self.__airDone.remove(b)
                                else: #Remove door from previously done radiation doors
                                    self.__radDone.remove([a[3],b])
                                    self.__radDone.remove(b)
                    if a[2]>sz or a[2]==-1: #Bubble has reached maximum size or virtual bubble is over
                        if self.LINK["multi"]!=1 and a[4]==1: #Is not a client and is air bubble
                            self.air = False
                        elif self.LINK["multi"]!=1 and a[4]==2: #Is not a client and is radiation bubble
                            if not self.radiation:
                                self.LINK["outputCommand"]("Radiation has completely flooded R"+str(self.number),(255,0,0))
                            self.radiation = True
                        rem.append(a) #Remove this bubble
                for a in rem:
                    self.__airBurst.remove(a)
                if len(rem)!=0:
                    if self.radiation: #Remove all radiation bubbles
                        self.__clearRadiation()
            if (not self.air or len(self.__airBurst)!=0 or self.radiation) and self.LINK["multi"]!=1: #Used to detect new opened rooms and stop the vacume if all airlocks are closed
                isVac = False
                for a in self.__vacumeAirlocks: #Check if this room is still in a vacume
                    if a.settings["open"] and a.room2 is None: #Airlock is open and not connected to a ship
                        iS = False
                        for b in self.doors:
                            if b.settings["open"]:
                                if b.isPathTo(a) or b==a: #There is a path from the door to the airlock sucking this room or we are currently at the airlock
                                    iS = True #Room is still vacuumed
                                    break
                        if iS: #Room is still vacuumed
                            isVac = True
                            break
                if not self.__containsBubble(1) and not self.air: #Room is completely vacuumed
                    for a in self.doors:
                        if a.settings["open"] and not a in self.__airDone and not a.room2 is None: #A new door has opened
                            for b in self.__vacumeAirlocks:
                                self.airBurst(self.pos,self.__vacumeShortPath+"/"+str(self.ID),b)
                        elif not a.settings["open"] and a in self.__airDone: #A previously open door has closed
                            for b in self.__vacumeAirlocks:
                                if [b,a] in self.__airDone:
                                    self.__airDone.remove([b,a])
                            self.__airDone.remove(a)
                        if a.settings["open"]: #Suck all entites inside the door out the airlock
                            ENTS = a.EntitiesInside()
                            for b in ENTS:
                                if b.beingSucked == False:
                                    b.suckOutOfAirlock(self.__vacumeShortPath+"/"+str(self.ID))
                    ENTS = self.EntitiesInside() #Suck any remaining or new entiteis inside this room out the airlock
                    for a in ENTS:
                        if a.beingSucked == False:
                            a.suckOutOfAirlock(self.__vacumeShortPath+"/"+str(self.ID))
                if self.radiation:
                    DroneObject = self.getEnt("drone")
                    for a in self.doors:
                        if a.settings["open"] and not a in self.__radDone and not a.room2 is None: #A new door has opened
                            self.radBurst(self.pos) #Create a virtual bubble to fill not allredey filled doors with radiation
                        Ents = a.EntitiesInside()
                        for b in Ents: #Go through all the entities inside the door and cause them to be damaged by radiation
                            if type(b) == DroneObject or b.isNPC:
                                b.takeDamage(lag,"radiation")
                    ENTS = self.EntitiesInside()
                    for b in ENTS: #Damage all entities inside the room
                        if type(b)==DroneObject or b.isNPC:
                            b.takeDamage(lag,"radiation")
                if not isVac and (not self.air or len(self.__airBurst)!=0): #Vaccum has finished, filling with air...
                    self.fillAir()
                    self.air = True
                    if self.LINK["multi"]==2: #Is server
                        self.LINK["Broadcast"]("rbud",self.ID)
    def __containsBubble(self,ID): #Returns true if the bubble is inside the list
        for a in self.__airBurst:
            if a[4]==ID:
                return True
        return False
    def fillAir(self): #Cancels all vacumes in the room (should only be used in multiplayer on clients)
        self.__vacumeAirlocks = []
        rem = []
        for a in self.__airBurst:
            if a[4]==1:
                rem.append(a)
        for a in rem:
            self.__airBurst.remove(a)
        self.__airDone = []
        self.__vacumeShortPath = ""
    def __clearRadiation(self): #Clears all radiation bubbles (does not turn off radiation in the room)
        rem = []
        for a in self.__airBurst:
            if a[4]==2:
                rem.append(a)
        for a in rem:
            self.__airBurst.remove(a)
    def airBurst(self,startPos,path,airlock,door=None): #Air vacume
        self.__airBurst.append([startPos,path+"/"+str(self.ID),3,airlock,1])
        if self.LINK["multi"]!=-1: #Is not a client
            if len(path)<len(self.__vacumeShortPath) or len(self.__vacumeShortPath)==0:
                self.__vacumeShortPath = path+""
            if not self.air: #Air bubble must be an instant one since the room doesen't have air in it
                self.__airBurst[-1][2] = -1
            elif self.LINK["multi"]==2: #Is server
                self.LINK["Broadcast"]("rbub",self.ID,startPos)
            if not airlock in self.__vacumeAirlocks: #Airlock doesen't exist
                self.__vacumeAirlocks.append(airlock)
            if not door in self.__airDone and not door is None: #Door that air burst came from must not be visited again.
                self.__airDone.append(door)
                self.__airDone.append([airlock,door])
    def radBurst(self,startPos): #Radiation leak
        if not self.__containsBubble(2):
            self.LINK["outputCommand"]("Radiation is flooding R"+str(self.number),(255,0,0))
        self.__airBurst.append([startPos,"",3,None,2])
        if self.LINK["multi"]!=-1: #Is not a client
            if self.radiation: #Air bubble must be an instant one since the room doesen't have air in it
                self.__airBurst[-1][2] = -1
            elif self.LINK["multi"]==2: #Is server
                self.LINK["Broadcast"]("rrub",self.ID,startPos)
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        pows = []
        for i,a in enumerate(self.settings["power"]):
            try:
                pows.append(a.ID)
            except:
                self.LINK["errorDisplay"]("Saving power link "+str(i)+"(index) in room "+str(self.ID)+"(ID) failed.")
        return ["room",self.ID,self.pos,self.size,self.settings["radiation"],self.settings["scanable"],pows]
    def reloadSize(self): #Must be called when the room has changed size
        self.__drawSurf = pygame.Surface(self.size)
        self.__drawSurf.set_colorkey((0,0,0))
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.size = data[3]
        self.settings["radiation"] = data[4]
        self.settings["scanable"] = data[5]
        self.reloadSize()
        for a in data[6]:
            if a in idRef:
                self.settings["power"].append(idRef[a])
            else:
                self.LINK["errorDisplay"]("Loading power link "+str(a)+"(ID) failed in room "+str(self.ID)+"(ID).")
        if self.LINK["multi"]==-1: #In map editor
            if not data[5]:
                self.SCAN = 2
    def afterLoad(self): #Link generators inside this room to the room
        Ents = self.EntitiesInside()
        GenObj = self.getEnt("generator")
        for a in Ents:
            if type(a)==GenObj:
                if not a in self.settings["power"]:
                    self.settings["power"].append(a)
    def __ChangeScan(self,LINK,state):
        self.settings["scanable"] = state==True
        if state:
            self.SCAN = 0
        else:
            self.SCAN = 2
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,145)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check1 = self.LINK["screenLib"].CheckButton(5,40,self.LINK,"Radiation leak",self.settings["radiation"],self.__ChangeRadiation) #Radiation checkbox
        self.__check2 = self.LINK["screenLib"].CheckButton(5,75,self.LINK,"Scannable",self.settings["scanable"],self.__ChangeScan) #Scannable checkbox
        self.__but2 = self.LINK["screenLib"].Button(5,110,self.LINK,"Link to",self.__LinkTo)
        self.__but3 = self.LINK["screenLib"].Button(5,145,self.LINK,"Unlink all",self.__UnlinkAll)
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check2.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__but2.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__but3.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
    def rightRender(self,x,y,surf): #Render the context menu
        windowPos = [x,y+50] #Window position
        #The 4 IF statments below will make sure the context menu is allways on the screen, even if this entity is not.
        if windowPos[0]<300:
            windowPos[0] = 300
        if windowPos[0]>self.LINK["reslution"][0]-150:
            windowPos[0] = self.LINK["reslution"][0]-150
        if windowPos[1]<10:
            windowPos[1] = 10
        if windowPos[1]>self.LINK["reslution"][1]-150:
            windowPos[1] = self.LINK["reslution"][1]-150
        self.__surface.fill((0,0,0)) #Empty the context menu surface
        self.__but1.render(self.__but1.pos[0],self.__but1.pos[1],1,1,self.__surface) #Render delete button
        self.__check1.render(self.__check1.pos[0],self.__check1.pos[1],1,1,self.__surface) #Render checkbutton
        self.__check2.render(self.__check2.pos[0],self.__check2.pos[1],1,1,self.__surface) #Render checkbutton
        self.__but2.render(self.__but2.pos[0],self.__but2.pos[1],1,1,self.__surface) #Render link button
        self.__but3.render(self.__but3.pos[0],self.__but3.pos[1],1,1,self.__surface) #Render unlink button
        surfSize = self.__surface.get_size() #Get the size of the context menu
        self.__lastRenderPos = [windowPos[0]-int(surfSize[0]/2),windowPos[1]] #Used for event loops
        pygame.draw.polygon(surf,(0,255,0),[ [windowPos[0]-int(surfSize[0]/3),windowPos[1]],
                                             [x,y],
                                             [windowPos[0]+int(surfSize[0]/3),windowPos[1]] ],2) #This is the triangle pointing from the menu to the entity
        pygame.draw.rect(self.__surface,(0,255,0),[1,1,208,surfSize[1]-3],2) #Outline rectangle
        surf.blit(self.__surface,self.__lastRenderPos) #Draw all results to the screen
    def rightUnload(self): #This delets the pygame surface and widget classes. This is mainly so theirs no memory leaks.
        self.__surface = None
        self.HINT = False
        self.__but1 = None
        self.__but2 = None
        self.__but3 = None
        self.__check1 = None
        self.__check2 = None
    def editMove(self,ents): #Room is being moved
        ins = self.findInsideOrNextTo(ents,[self])
        for ent in ins:
            if type(ent)==Main:
                self.__inRoom = True
                break
        else:
            self.__inRoom = False
    def giveError(self,ents): #Scans and gives an error out
        ins = self.findInsideOrNextTo(ents,[self])
        for ent in ins:
            if type(ent)==Main:
                return "Room colide"
        if len(self.settings["power"])==0:
            return "No power (room)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if self.SCAN!=0: #Draw scan lines on room
            if self.SCAN==1: #Safe
                col = (0,255,0)
            elif self.SCAN==2: #Error
                col = (255,255,0)
            elif self.SCAN==3: #Bad
                col = (255,0,0)
            else: #Scan variable error
                col = (255,255,255)
            perc = (time.time()-int(time.time()))*2
            if perc>1:
                perc = 2-perc
            pygame.draw.line(surf,col,[x+(self.size[0]*scale*perc),y],[x+(self.size[0]*scale*perc),y+(self.size[1]*scale)],int(3*scale))
            pygame.draw.line(surf,col,[x,y+(self.size[1]*scale*perc)],[x+(self.size[0]*scale),y+(self.size[1]*scale*perc)],int(3*scale))
        if not edit:
            scrolPos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y]
            self.__drawSurf.fill((0,0,0))
            for a in self.__airBurst:
                if a[2]!=-1: #Air bubble is not an instant air bubble
                    if a[4]==1: #Air bubble
                        pygame.draw.circle(self.__drawSurf,(255,255,255),[int(a[0][0]-self.pos[0]),int(a[0][1]-self.pos[1])],int(a[2]),3)
                    else: #Radiation bubble
                        pygame.draw.circle(self.__drawSurf,(255,0,0),[int(a[0][0]-self.pos[0]),int(a[0][1]-self.pos[1])],int(a[2]))
            surf.blit(pygame.transform.scale(self.__drawSurf,(int(self.size[0]*scale),int(self.size[1]*scale))),[int(x),int(y)])
        if (self.settings["radiation"] and edit) or self.radiation: #Draw slanting lines for radiation
            for i in range(-int(self.size[1]/25)+1,int(self.size[0]/25)):
                if i<0:
                    ad1 = abs(i)*25*scale
                else:
                    ad1 = 0
                if i>int(self.size[0]/25)-int(self.size[1]/25):
                    ad2 = abs(i-(int(self.size[0]/25)-int(self.size[1]/25)))*25*scale
                else:
                    ad2 = 0
                pygame.draw.line(surf,(200,0,0),[x+(i*25*scale)+ad1,y+ad1],[x+(((i*25)+self.size[1])*scale)-ad2,y+(self.size[1]*scale)-ad2])
        if not self.air: #Draw slanting lines for no air
            for i in range(-int(self.size[1]/25)+1,int(self.size[0]/25)):
                if i<0:
                    ad1 = abs(i)*25*scale
                else:
                    ad1 = 0
                if i>int(self.size[0]/25)-int(self.size[1]/25):
                    ad2 = abs(i-(int(self.size[0]/25)-int(self.size[1]/25)))*25*scale
                else:
                    ad2 = 0
                pygame.draw.line(surf,(200,200,200),[x+(self.size[0]*scale)-((i*25*scale)+ad1),y+ad1],[x+((self.size[0])*scale)-((((i*25)+self.size[1])*scale)-ad2),y+(self.size[1]*scale)-ad2])
        if self.__inRoom and edit: #If inside a room in the map editor, used to raise error
            pygame.draw.rect(surf,(200,0,0),[x,y,self.size[0]*scale,self.size[1]*scale],int(5*scale))
        elif self.powered:
            pygame.draw.rect(surf,(0,200,0),[x,y,self.size[0]*scale,self.size[1]*scale],int(5*scale))
            for x2 in range(int(self.size[0]/25)):
                pygame.draw.line(surf,(0,200,0),[x+(x2*25*scale),y],[x+(x2*25*scale),y+(self.size[1]*scale)])
            for y2 in range(int(self.size[1]/25)):
                pygame.draw.line(surf,(0,200,0),[x,y+(y2*25*scale)],[x+(self.size[0]*scale),y+(y2*25*scale)])
        else:
            pygame.draw.rect(surf,(200,200,200),[x,y,self.size[0]*scale,self.size[1]*scale],int(5*scale))
            if self.poweredBefore:
                for x2 in range(int(self.size[0]/25)):
                    pygame.draw.line(surf,(200,200,200),[x+(x2*25*scale),y],[x+(x2*25*scale),y+(self.size[1]*scale)])
                for y2 in range(int(self.size[1]/25)):
                    pygame.draw.line(surf,(200,200,200),[x,y+(y2*25*scale)],[x+(self.size[0]*scale),y+(y2*25*scale)])
        if edit:
            pygame.draw.line(surf,(255,255,255),[x+(self.size[0]*scale),y+((self.size[1]-25)*scale)],[x+((self.size[0]-25)*scale),y+(self.size[1]*scale)],int(5*scale))
            scrolPos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Calculate the scroll position
            rem = [] #Items to remove because they where deleted
            for a in self.settings["power"]: #Loop through power wires
                pygame.draw.line(surf,(100,0,100),[x+(self.size[0]*0.5*scale),y+(self.size[1]*0.5*scale)],
                                                    [((a.pos[0]+(a.size[0]/2))*scale)-scrolPos[0],((a.pos[1]+(a.size[1]/2))*scale)-scrolPos[1]],3)
                if a.REQUEST_DELETE: #Entity is has been deleted (this entity is keeping it alive with its pointer)
                    rem.append(a)
            for a in rem: #Remote entities that have been deleted
                self.settings["power"].remove(a)
        elif self.number != -1: #Draw the room number
            if self.powered: #Is the room being powered
                textSurf = self.LINK["font42"].render("R"+str(self.number),16,(0,100,0)) #Create a surface that is the rendered text
            else:
                textSurf = self.LINK["font42"].render("R"+str(self.number),16,(100,100,100)) #Create a surface that is the rendered text
            textSize = list(textSurf.get_size()) #Get the size of the text rendered
            pygame.draw.rect(surf,(0,0,0),[x+(((self.size[0]/2)-(textSize[0]/2))*scale),y+((self.size[1]/4)*scale)]+textSize) #Draw a black background for the text to be displayed infront of
            surf.blit(textSurf,(x+(((self.size[0]/2)-(textSize[0]/2))*scale),y+((self.size[1]/4)*scale))) #Render text
        if not edit and self.LINK["DEVDIS"]: #Development display, display room ID
            textSurf = self.LINK["font42"].render("ID: "+str(self.ID),16,(0,150,0))
            surf.blit(textSurf,(x+((self.size[0]/2)*scale),y+((self.size[1]/2)*scale))) #Render text
        if self.radiation or not self.air: #Draw warning sign
            surf.blit(self.getImage("warning"),(x+int((self.size[0]/2)*scale)-(25*scale),y+int((self.size[1]/2)*scale)-(25*scale)))
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
