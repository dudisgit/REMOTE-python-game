import pygame, random, math, time, mapGenerator

OVERLAY_OPASITY = 50 #Opasity of the overlay (0-255)
PRICE = {"gather":8,"generator":8,"interface":12,"lure":16,"motion":12,"overload":8,"pry":12,"remote power":12,"sensor":16,"stealth":12,"surveyor":8,"tow":8}

class Main:
    def __init__(self,LINK):
        self.__LINK = LINK
        if LINK["multi"]!=1: #Is not running as client
            LINK["shipData"]["scrap"] += LINK["scrapCollected"]
            LINK["scrapCollected"] = 0
            LINK["shipData"]["fuel"] += LINK["fuelCollected"]
            LINK["fuelCollected"] = 0
            LINK["showRooms"] = False
            LINK["shipData"]["shipUpgs"] = []
            for a in LINK["shipEnt"].settings["upgrades"]:
                if not a[0]=="":
                    LINK["shipData"]["shipUpgs"].append(a.copy())
            for a in LINK["drones"]:
                a.unloadUpgrades()
        if LINK["multi"]==2: #Being ran as a server
            LINK["serv"].SYNC["F"] = LINK["shipData"]["fuel"]
            LINK["serv"].SYNC["S"] = LINK["shipData"]["scrap"]
            self.__LINK["serv"].TRIGGER["dswp"] = self.__swapDrone #Move a drone to and from the reserve area
            self.__LINK["serv"].TRIGGER["mufd"] = self.__moveUpgradeFromDrone #Move an upgrade from a drone into the inventory
            self.__LINK["serv"].TRIGGER["mutd"] = self.__moveUpgradeToDrone #Move an upgrade from the inventory to a drone
            self.__LINK["serv"].TRIGGER["swdr"] = self.__swpDroneLR #Swap a drone from left to right
            self.__LINK["serv"].TRIGGER["disu"] = self.__dismantleUpgradeServer #Dismantle an upgrade
            self.__LINK["serv"].TRIGGER["fxud"] = self.__fixDroneOrUpgradeServer #Fix an upgrade or drone
            self.__LINK["serv"].TRIGGER["bob"] = self.__swapShipUpgrade #Swaps the ship upgrade
            self.__LINK["serv"].TRIGGER["fxsu"] = self.__fixShipUpgradeServer #Fixes a ship upgrade
            self.__LINK["serv"].TRIGGER["dssu"] = self.__dismantleShipUpgradeServer #Dismantles a ship upgrade
            self.__LINK["serv"].TRIGGER["buy"] = self.__buyUpgradeServer #Buy an upgrade from the buying menu
        self.__shipName = "Your ship" #Name of the ship
        self.__maxDrones = 4 #Max drones that can be on the ship
        self.__maxUpgrades = LINK["shipData"]["maxShipUpgs"] #Maximum upgrade slots
        self.__upgrades = 0 #Upgrades installed on the ship
        self.__scrapCollected = LINK["shipData"]["scrap"] #Scrap inside the ship
        self.__scrapCopasity = 50 #Maximum scrap allowed in the ship
        self.__fuelLeft = LINK["shipData"]["fuel"] #Gathered fuel
        self.failed = [False,0] #Game lost
        self.__dialog = [False,"Test question",None,0] #Dialog yes/no for menu system
        self.__cols = []
        self.maps = []
        #Syntax
        #0: Map generator object
        #1: Scrap capasity
        #2: Age (string)
        #3: Ship name
        #4: Threat types
        #5: Fuel/distance
        self.__HoldKeys = {} #Keys being held down
        if LINK["multi"]!=2: #Is not a server
            blackImage = pygame.Surface((120,120))
            blackImage.fill((0,0,0))
            blackImage.set_alpha(175)
            self.__droneNormal = pygame.transform.scale(self.getImage("droneNormal"), (120,120))
            self.__droneDead = pygame.transform.scale(self.getImage("droneDisabled"), (120,120))
            self.__droneNormalDark = pygame.transform.scale(self.getImage("droneNormal"), (120,120)).copy()
            self.__droneDeadDark = pygame.transform.scale(self.getImage("droneDisabled"), (120,120)).copy()
            self.__droneNormalDark.blit(blackImage,(0,0))
            self.__droneDeadDark.blit(blackImage,(0,0))
            sx,sy = LINK["main"].get_size()
            #sx = 1000
            #sy = 700
            sx2 = sy*1.777
            self.__displayInfo = [False,pygame.transform.scale(LINK["content"]["loading"],(int(sx2),int(sy))),(sx2-sx)/-2,[sx,sy],"Unknown error"]
            self.__extrInfo = []
        self.__sel = 0 #Selecting ship
        self.__sels = [0,0,0,0] #Used to select items and panels in the inventory config menu
        self.__tab = False #Ship selector
        if LINK["multi"]!=2: #Is not a server
            sx,sy = LINK["main"].get_size()
            sx2 = sy*1.777
            self.__loading = [False,pygame.transform.scale(LINK["content"]["loading"],(int(sx2),int(sy))),(sx2-sx)/-2,0,"Generating maps",[sx,sy]]
            self.__changeEffect = [0,0.0]
        else:
            self.__loading = [False]
        if LINK["backgroundStatic"] and LINK["multi"]!=2: #Background static
            print("Generating overlays")
            for a in range(3):
                self.__cols.append(pygame.Surface((sx,sy)))
                matr = pygame.PixelArray(self.__cols[-1])
                for x in range(int(sx/3)):
                    for y in range(int(sy/3)):
                        matr[x*3:(x*3)+3,y*3:(y*3)+3] = pygame.Color(random.randint(0,50),random.randint(0,50),random.randint(0,50))
                    if self.__LINK["multi"]==1:
                        self.__LINK["cli"].loop()
            print("Done")
        if self.__LINK["multi"]!=1: #Game is not being ran as a client
            self.__generateMaps()
        else: #Game is being ran as a client
            self.__loading[0] = True
            self.__loading[4] = "Waiting for server"
            self.__LINK["cli"].finishLoading = self.__FinishLoading
            self.__LINK["cli"].TRIGGER["sss"] = self.servInit
            self.__LINK["cli"].TRIGGER["dinf"] = self.displayInfo #Called when the server wants to display info.
    def __swapShipUpgrade(self,sock,upg): #Swap a ship upgrade between reserve and active
        if upg>=self.__LINK["shipData"]["maxShipUpgs"]: #Move upgrade from reserve into the active
            self.__LINK["shipData"]["shipUpgs"].append(self.__LINK["shipData"]["reserveUpgs"].pop(upg-self.__LINK["shipData"]["maxShipUpgs"]))
        else: #Move active into reserve
            self.__LINK["shipData"]["reserveUpgs"].append(self.__LINK["shipData"]["shipUpgs"].pop(upg))
        MX1,MX2, Nlink, NL2 = self.__getShipInfo()
        for i,a in enumerate(self.__LINK["shipData"]["shipUpgs"]):
            self.__LINK["serv"].SYNC["G"+str(NL2[a[2]])]["P"] = i+0
        for i,a in enumerate(self.__LINK["shipData"]["reserveUpgs"]):
            self.__LINK["serv"].SYNC["G"+str(NL2[a[2]])]["P"] = i+self.__LINK["shipData"]["maxShipUpgs"]
        self.__LINK["serv"].SYNC["UC"] = len(self.__LINK["shipData"]["shipUpgs"])
    def __swpDroneLR(self,sock,drone,dir): #Swap drone to left or right drone
        MXD,MXR,Nlink = self.__getDroneInfo()
        if dir==-1: #Move to the left
            if drone<MXD and not MXD==0:
                next = (drone-1)%MXD
                self.__LINK["serv"].SYNC["D"+str(Nlink[drone])]["O"],self.__LINK["serv"].SYNC["D"+str(Nlink[next])]["O"]=self.__LINK["serv"].SYNC["D"+str(Nlink[next])]["O"],self.__LINK["serv"].SYNC["D"+str(Nlink[drone])]["O"]
            elif drone-self.__LINK["shipData"]["maxDrones"]<MXR and drone-self.__LINK["shipData"]["maxDrones"]>=0:
                next = (drone-self.__LINK["shipData"]["maxDrones"]-1)%MXR
                next+=self.__LINK["shipData"]["maxDrones"]
                self.__LINK["serv"].SYNC["D"+str(Nlink[drone])]["O"],self.__LINK["serv"].SYNC["D"+str(Nlink[next])]["O"]=self.__LINK["serv"].SYNC["D"+str(Nlink[next])]["O"],self.__LINK["serv"].SYNC["D"+str(Nlink[drone])]["O"]
        elif dir==1: #Move to the right
            if drone<MXD and not MXD==0:
                next = (drone+1)%MXD
                self.__LINK["serv"].SYNC["D"+str(Nlink[drone])]["O"],self.__LINK["serv"].SYNC["D"+str(Nlink[next])]["O"]=self.__LINK["serv"].SYNC["D"+str(Nlink[next])]["O"],self.__LINK["serv"].SYNC["D"+str(Nlink[drone])]["O"]
            elif drone-self.__LINK["shipData"]["maxDrones"]<MXR and drone-self.__LINK["shipData"]["maxDrones"]>=0:
                next = (drone-self.__LINK["shipData"]["maxDrones"]+1)%MXR
                next+=self.__LINK["shipData"]["maxDrones"]
                self.__LINK["serv"].SYNC["D"+str(Nlink[drone])]["O"],self.__LINK["serv"].SYNC["D"+str(Nlink[next])]["O"]=self.__LINK["serv"].SYNC["D"+str(Nlink[next])]["O"],self.__LINK["serv"].SYNC["D"+str(Nlink[drone])]["O"]
    def __swapDrone(self,sock,sel):
        MXD,MXR,Nlink = self.__getDroneInfo()
        sel2 = sel+0
        if sel>=self.__LINK["shipData"]["maxDrones"]: #Move to drone squad
            for i,a in enumerate(self.__LINK["shipData"]["reserve"]):
                if a.GID==Nlink[sel]:
                    sel2 = i+self.__LINK["shipData"]["maxDrones"]
                    break
            if len(self.__LINK["drones"])<self.__LINK["shipData"]["maxDrones"]:
                dr = self.__LINK["shipData"]["reserve"].pop(sel2-self.__LINK["shipData"]["maxDrones"])
                self.__LINK["drones"].append(dr)
        else: #Move to reserve squad
            for i,a in enumerate(self.__LINK["drones"]):
                if a.GID==Nlink[sel]:
                    sel2 = i+0
                    break
            if len(self.__LINK["shipData"]["reserve"])<self.__LINK["shipData"]["maxReserve"]:
                dr = self.__LINK["drones"].pop(sel2)
                self.__LINK["shipData"]["reserve"].append(dr)
        for i,a in enumerate(self.__LINK["drones"]):
            self.__LINK["serv"].SYNC["D"+str(a.GID)]["O"] = i+0
        for i,a in enumerate(self.__LINK["shipData"]["reserve"]):
            self.__LINK["serv"].SYNC["D"+str(a.GID)]["O"] = i+self.__LINK["shipData"]["maxDrones"]
        self.__recalculateDroneNumbers()
        self.__LINK["serv"].SYNC["DC"] = len(self.__LINK["drones"])
    def __getInventInfo(self):
        Refs = {}
        if len(self.__LINK["shipData"]["invent"])==0 and self.__LINK["multi"]==2:
            return 0,Refs
        MX = 1
        if self.__LINK["multi"]==1: #Running as a client
            Ments = [] #Upgrades that are mentioned
            NotMents = [] #Upgrade that wasn't mentioned (probebly the start)
            for i in range(0,self.__LINK["shipData"]["maxInvent"]): #Find the first upgrade
                if self.__LINK["cli"].SYNC["U"+str(i)]["E"]: #Is an active upgrade
                    Ments.append(self.__LINK["cli"].SYNC["U"+str(i)]["P"])
                    if self.__LINK["cli"].SYNC["U"+str(i)]["P"] in NotMents:
                        NotMents.remove(self.__LINK["cli"].SYNC["U"+str(i)]["P"])
                    if not i in Ments:
                        NotMents.append(i)
                    MX += 1
            #print(NotMents)
            if len(NotMents)==0:
                return 0,Refs
            Refs[0] = NotMents[0]
            Node = NotMents[0]+0
            MX2 = 0
            for i in range(1,MX):
                Refs[i] = self.__LINK["cli"].SYNC["U"+str(Node)]["P"]+0
                Node = self.__LINK["cli"].SYNC["U"+str(Node)]["P"]+0
                MX2+=1
                if Node==-1:
                    break
            #print(Refs)
            return MX2,Refs
        else:
            Ments = [] #Upgrades that are mentioned
            NotMents = [] #Upgrade that wasn't mentioned (probebly the start)
            for i in range(0,self.__LINK["shipData"]["maxInvent"]): #Find the first upgrade
                if self.__LINK["serv"].SYNC["U"+str(i)]["E"]: #Is an active upgrade
                    Ments.append(self.__LINK["serv"].SYNC["U"+str(i)]["P"])
                    if self.__LINK["serv"].SYNC["U"+str(i)]["P"] in NotMents:
                        NotMents.remove(self.__LINK["serv"].SYNC["U"+str(i)]["P"])
                    if not i in Ments:
                        NotMents.append(i)
            Refs[0] = NotMents[0]
            Node = NotMents[0]+0
            for i in range(1,len(self.__LINK["shipData"]["invent"])):
                Refs[i] = self.__LINK["serv"].SYNC["U"+str(Node)]["P"]+0
                Node = self.__LINK["serv"].SYNC["U"+str(Node)]["P"]+0
                if i+1>MX:
                    MX = i+1
        return MX,Refs
    def __moveUpgradeFromDrone(self,sock,drone,upgrade): #Move an upgrade from a drone into the inventory area
        DR = None
        MD,MRD,DLink = self.__getDroneInfo()
        #DR = self.__LINK["drones"][DLink[drone]]
        if drone<len(self.__LINK["drones"]): #Is a reserved drone
            DR = self.__LINK["drones"][DLink[drone]]
        else:
            DR = self.__LINK["shipData"]["reserve"][DLink[drone-self.__LINK["shipData"]["maxDrones"]]]
        MX, refs = self.__getInventInfo()
        DR.unloadUpgrades()
        UPG = DR.settings["upgrades"][upgrade].copy()
        self.__LINK["shipData"]["invent"].append(DR.settings["upgrades"][upgrade].copy())
        DR.upgrades.pop(upgrade)
        DR.unloadUpgrades()
        #Reload all the drones upgrades with the SYNC dictionary
        self.__LINK["serv"].SYNC["D"+str(DR.GID)]["US"] = len(DR.settings["upgrades"]) #Drone upgrade amount
        for i2,b in enumerate(DR.settings["upgrades"]): #Sync all the drones upgrades
            if b[0]=="":
                self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = ""
            else:
                if len(b)==5:
                    if len(b[4])!=0:
                        self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])+","+str(b[4][0])
                    else:
                        self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])
                else:
                    self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])
        #Add the upgrade to the inventory area
        key = "ERR"
        for i in range(0,self.__LINK["shipData"]["maxInvent"]):
            if not self.__LINK["serv"].SYNC["U"+str(i)]["E"]:
                key = "U"+str(i)
        self.__LINK["serv"].SYNC[key]["E"] = True
        self.__LINK["serv"].SYNC[key]["N"] = UPG[0]
        self.__LINK["serv"].SYNC[key]["D"] = UPG[1]
        self.__LINK["serv"].SYNC[key]["P"] = -1
        if len(self.__LINK["shipData"]["invent"])!=1: #Is not the first time an item has been put in
            self.__LINK["serv"].SYNC["U"+str(refs[MX-1])]["P"] = int(key[1:])
        #for i in range(len(self.__LINK["shipData"]["invent"])+1,self.__LINK["shipData"]["maxInvent"]):
        #    self.__LINK["serv"].SYNC["U"+str(i)]["P"] += 1
    def __moveUpgradeToDrone(self,sock,drone,upgrade): #Move an upgrade from a drone into the inventory area
        DR = None
        MD,MRD,DLink = self.__getDroneInfo()
        #DR = self.__LINK["drones"][DLink[drone]]
        if drone<len(self.__LINK["drones"]): #Is a reserved drone
            DR = self.__LINK["drones"][DLink[drone]]
        else:
            DR = self.__LINK["shipData"]["reserve"][DLink[drone-self.__LINK["shipData"]["maxDrones"]]]
        MX,inf = self.__getInventInfo()
        DR.unloadUpgrades()
        DR.settings["upgrades"][len(DR.upgrades)] = self.__LINK["shipData"]["invent"].pop(upgrade)
        DR.loadUpgrades()
        #Reload all the drones upgrades with the SYNC dictionary
        self.__LINK["serv"].SYNC["D"+str(DR.GID)]["US"] = len(DR.settings["upgrades"]) #Drone upgrade amount
        for i2,b in enumerate(DR.settings["upgrades"]): #Sync all the drones upgrades
            if b[0]=="":
                self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = ""
            else:
                if len(b)==5:
                    if len(b[4])!=0:
                        self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])+","+str(b[4][0])
                    else:
                        self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])
                else:
                    self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])
        #Remove the upgrade from the inventory area
        self.__LINK["serv"].SYNC["U"+str(inf[upgrade])]["E"] = False
        #Reload all the inventory upgrade positions to sync with users
        if upgrade!=0 and not upgrade>=len(self.__LINK["shipData"]["invent"]): #Is not the start or the end
            self.__LINK["serv"].SYNC["U"+str(inf[upgrade-1])]["P"] = inf[upgrade+1]+0
        elif upgrade>=len(self.__LINK["shipData"]["invent"]) and upgrade!=0:
            self.__LINK["serv"].SYNC["U"+str(inf[upgrade-1])]["P"] = -1
    def servInit(self,bol,fail): #Called when this screen was called by the server
        self.__LINK["mesh"] = {}
        if fail!=-1:
            self.__LINK["loadScreen"]("death",fail)
        elif not bol:
            self.__LINK["loadScreen"]("game")
    def displayInfo(self,inf,scr): #Called by the server to display info about a mission
        self.__extrInfo = inf
        self.__displayInfo[0] = True
        self.__displayInfo[4] = "Your score is "+str(scr)
    def getEnt(self,name): #Returns the entity with the name
        if name in self.__LINK["ents"]: #Does the entity exist?
            return self.__LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.__LINK["errorDisplay"]("Tried to create entity but doesen't exist '"+name+"'")
        return self.__LINK["null"]
    def __generateMaps(self): #Generates all maps
        self.__loading[0] = True
        print("Generating maps")
        FIR = False
        if len(self.__LINK["shipData"]["mapSaves"])==0: #Generate map saving slots
            FIR = True
            for i in range(0,5):
                self.__LINK["shipData"]["mapSaves"].append(["Madamada",0])
        for i in range(0,5): #Create 5 maps
            if random.randint(0,1)==1 or i==self.__LINK["shipData"]["beforeMap"] or FIR: #50 Percent chance the map will be generated
                MP = mapGenerator.MapGenerator(self.__LINK,random.randint(5,8),"ShipSelect"+str(i))
            else:
                MP = mapGenerator.FakeMapGenerator(self.__LINK,"ShipSelect"+str(i))
            Scrap = 0 #Scrap in the map
            ScrapReferenceObject = self.getEnt("scrap")
            AirlockReferenceObject = self.getEnt("airlock")
            RoomReferenceObject = self.getEnt("room")
            FailLock = 0 #Number of failed airlocks
            FailRoom = 0 #Number of failing rooms (radiation)
            Threats = [] #List of threat types on the ship
            for a in MP.ents: #Go through all entities in the ship and analyze infomation about them
                Scrap+=int(type(a)==ScrapReferenceObject)
                if type(a)==AirlockReferenceObject:
                    FailLock += int(a.settings["fail"])
                elif type(a)==RoomReferenceObject:
                    FailRoom += int(a.settings["radiation"])
                elif a.isNPC:
                    if not type(a) in Threats:
                        Threats.append(type(a))
            msg = str(random.randint(1,64))+" <STABLE>" #Age message (normal)
            if FailLock!=0 or FailRoom!=0: #Ship is dangourus, airlock or rooms will fill with radiation
                msg = str(random.randint(74,200))+" <VOLITILE>"
            if FailLock!=0 and FailRoom!=0: #Room and airlocks will fail, ship is very dangourus
                msg = str(random.randint(200,500))+" <HAZARDOUS>"
            CAP = random.randint(1,4)*20 #Scrap copasity
            while Scrap>CAP: #Keep adding 20 scrap until the scrap copasity is higher than the scrap count.
                CAP += 20
            Fuel = 1 #Fuel to get to the ship
            if FailLock==0 and FailRoom==0: #Rooms and airlocks are safe
                Fuel += random.randint(0,2)
            if len(Threats)==0: #No threats on ship
                Fuel += random.randint(2,4)
            if Scrap>20:
                Fuel += 1
            if type(MP)==mapGenerator.FakeMapGenerator: #Map is a previously generated one
                self.maps.append([MP,CAP,msg,self.__LINK["shipData"]["mapSaves"][i][0],len(Threats),self.__LINK["shipData"]["mapSaves"][i][1]])
            else:
                self.maps.append([MP,CAP,msg,self.__LINK["shipNames"][random.randint(0,len(self.__LINK["shipNames"])-1)],len(Threats),Fuel])
                self.__LINK["shipData"]["mapSaves"][i] = [self.maps[-1][3],Fuel]
            if self.__LINK["multi"]!=2: #Is not the server
                self.__loading[3] = i/5
                self.__updateScreen()
            print(str(int((i/5)*100))+"%")
        print("done")
        self.__loading[0] = False
        for a in self.maps:
            if self.__LINK["shipData"]["fuel"]>=a[5]: #Ship has enough fuel to head to ship
                break
        else: #Ship ran out of fuel
            self.failed = [True,1]
        if len(self.__LINK["drones"])==0: #TEMPORY (fogot why, fails when there are no drones left)
            self.failed = [True,2]
    def __updateScreen(self): #Update the screen
        self.render(self.__LINK["main"]) #Render the screen
        pygame.event.get() #Disregard events
        pygame.display.flip() #Update display
    def displayLoadingScreen(self): #Display a loading screen
        if self.__LINK["multi"]==2: #Is the server
            return None
        surf = self.__LINK["main"]
        surf.blit(self.__loading[1],(self.__loading[2],0))
        #Error message
        fren = self.__LINK["font42"].render("Loading...",16,(0,255,0))
        sx,sy = fren.get_size()
        pygame.draw.rect(surf,(0,0,0),[int(self.__loading[5][0]/2)-int(sx/2)-5,int(self.__loading[5][1]/2)-5,sx+10,sy+10])
        pygame.draw.rect(surf,(0,255,0),[int(self.__loading[5][0]/2)-int(sx/2)-5,int(self.__loading[5][1]/2)-5,sx+10,sy+10],2)
        surf.blit(fren,(int(self.__loading[5][0]/2)-int(sx/2),int(self.__loading[5][1]/2)))
        pygame.display.flip()
    def __isKeyDown(self,key): #Returns true if the key is being held down
        if key in self.__HoldKeys: #Has the key been pressed before?
            return self.__HoldKeys[key]
        return False
    def __recalculateDroneNumbers(self): #Recalculates all drone numbers
        NUM = 1
        for a in self.__LINK["drones"]:
            a.number = NUM+0
            NUM += 1
    def __recalculateDroneNumbersByOrder(self): #Same as __recalculateDroneNumbers but sorts by SYNC position
        NEWD = [0]*len(self.__LINK["drones"])
        for a in self.__LINK["drones"]:
            a.number = self.__LINK["serv"].SYNC["D"+str(a.GID)]["O"]+1
            NEWD[a.number-1] = a
        self.__LINK["drones"] = NEWD
    def __reloadSpecs(self): #Reload ship infomation for server
        for i,a in enumerate(self.maps):
            self.__LINK["serv"].SYNC["S"+str(i)] = {}
            self.__LINK["serv"].SYNC["S"+str(i)]["N"] = a[3] #Ship name
            self.__LINK["serv"].SYNC["S"+str(i)]["S"] = a[1] #Scrap capasity
            self.__LINK["serv"].SYNC["S"+str(i)]["T"] = a[4] #Threat types
            self.__LINK["serv"].SYNC["S"+str(i)]["D"] = a[5] #Distance/fuel
            self.__LINK["serv"].SYNC["S"+str(i)]["A"] = a[2] #Age
    def __FinishLoading(self): #When the server has finished syncing all variables
        if self.__LINK["cli"].SYNC["SS"]: #Still insite ship selecting screen
            DWN = self.__LINK["cli"].SYNC
            self.maps = []
            for i in range(0,5):
                dic = DWN["S"+str(i)]
                self.maps.append([None,dic["S"],dic["A"],dic["N"],dic["T"],dic["D"]])
            self.__loading[0] = False
            self.__fuelLeft = DWN["F"]
            self.__scrapCollected = DWN["S"]
            self.__LINK["shipData"]["scrap"] = self.__scrapCollected
            self.__LINK["shipData"]["fuel"] = self.__fuelLeft
            self.__LINK["shipData"]["maxDrones"] = self.__LINK["cli"].SYNC["MD"]
            self.__LINK["shipData"]["maxReserve"] = self.__LINK["cli"].SYNC["MR"]
            self.__LINK["shipData"]["maxInvent"] = self.__LINK["cli"].SYNC["MI"]
            self.__LINK["shipData"]["maxShipUpgs"] = self.__LINK["cli"].SYNC["MS"]
            self.__LINK["shipData"]["reserveMax"] = self.__LINK["cli"].SYNC["MSS"]
            for i in range(0,DWN["MD"]+DWN["MR"]):
                if DWN["D"+str(i)]["E"]: #Drone exists
                    if i >=DWN["MD"]: #Is a reserved drone
                        pass
                    else: #Is a normal drone
                        pass
    def __getDroneInfo(self): #Gets drone infomation when running as a client
        MXD = 0
        MXR = 0
        NumLink = {}
        NumReverse = {}
        if self.__LINK["multi"]==1: #Game is running as a client
            for i3 in range(0,self.__LINK["shipData"]["maxDrones"]+self.__LINK["shipData"]["maxReserve"]):
                if self.__LINK["cli"].SYNC["D"+str(i3)]["E"]:
                    O = self.__LINK["cli"].SYNC["D"+str(i3)]["O"]
                    NumLink[O] = i3+0
                    NumReverse[i3] = O+0
                    if O >= self.__LINK["shipData"]["maxDrones"] and (O-self.__LINK["shipData"]["maxDrones"])+1>MXR:
                        MXR = (O-self.__LINK["shipData"]["maxDrones"])+1
                    elif O < self.__LINK["shipData"]["maxDrones"] and O+1 > MXD:
                        MXD = O+1
        elif self.__LINK["multi"]==2: #Game is running in a server
            for i3 in range(0,self.__LINK["shipData"]["maxDrones"]+self.__LINK["shipData"]["maxReserve"]):
                if self.__LINK["serv"].SYNC["D"+str(i3)]["E"]:
                    O = self.__LINK["serv"].SYNC["D"+str(i3)]["O"]
                    NumLink[O] = i3+0
                    if O >= self.__LINK["shipData"]["maxDrones"] and (O-self.__LINK["shipData"]["maxDrones"])+1>MXR:
                        MXR = (O-self.__LINK["shipData"]["maxDrones"])+1
                    elif O < self.__LINK["shipData"]["maxDrones"] and O+1 > MXD:
                        MXD = O+1
            return MXD,MXR,NumLink
        return MXD,MXR,NumLink,NumReverse
    def __getShipInfo(self): #Gets ship upgrade infomation
        MXD = 0
        MXR = 0
        NumLink = {}
        IDLink = {}
        if self.__LINK["multi"]==1: #Game is running as a client
            for i3 in range(0,self.__LINK["shipData"]["maxShipUpgs"]+self.__LINK["shipData"]["reserveMax"]):
                if self.__LINK["cli"].SYNC["G"+str(i3)]["E"]:
                    O = self.__LINK["cli"].SYNC["G"+str(i3)]["P"]
                    NumLink[O] = i3+0
                    if O >= self.__LINK["shipData"]["maxShipUpgs"] and (O-self.__LINK["shipData"]["maxShipUpgs"])+1>MXR:
                        MXR = (O-self.__LINK["shipData"]["maxShipUpgs"])+1
                    elif O < self.__LINK["shipData"]["maxShipUpgs"] and O+1 > MXD:
                        MXD = O+1
        elif self.__LINK["multi"]==2: #Game is running in a server
            for i3 in range(0,self.__LINK["shipData"]["maxShipUpgs"]+self.__LINK["shipData"]["reserveMax"]):
                if self.__LINK["serv"].SYNC["G"+str(i3)]["E"]:
                    O = self.__LINK["serv"].SYNC["G"+str(i3)]["P"]
                    NumLink[O] = i3+0
                    IDLink[self.__LINK["serv"].SYNC["G"+str(i3)]["I"]] = i3+0
                    if O >= self.__LINK["shipData"]["maxShipUpgs"] and (O-self.__LINK["shipData"]["maxShipUpgs"])+1>MXR:
                        MXR = (O-self.__LINK["shipData"]["maxShipUpgs"])+1
                    elif O < self.__LINK["shipData"]["maxShipUpgs"] and O+1 > MXD:
                        MXD = O+1
            return MXD,MXR,NumLink,IDLink
        return MXD,MXR,NumLink
    def __getDroneUpgradeCount(self,key):
        MX = 0
        if self.__LINK["multi"]==1: #Game is running as a client
            for i in range(0,self.__LINK["cli"].SYNC["D"+str(key)]["US"]):
                if self.__LINK["cli"].SYNC["D"+str(key)]["U"+str(i)]!="":
                    MX += 1
        return MX
    def loop(self,mouse,kBuf,lag):
        if self.failed[0]:
            self.__LINK["loadScreen"]("death",self.failed[1])
        if self.__LINK["backgroundStatic"]:
            self.__changeEffect[1]+=lag*4 #Used to alpha overlay
            if self.__changeEffect[1]>=OVERLAY_OPASITY: #Next overlay
                self.__changeEffect[1] = 0
                self.__changeEffect[0] = (self.__changeEffect[0]+1)%len(self.__cols)
        if self.__LINK["multi"]==1: #Running as a client
            if self.__LINK["cli"].loading and self.__LINK["cli"].getPercent()!=0:
                self.__loading[4] = "Downloading variables"
                self.__loading[3] = self.__LINK["cli"].getPercent()
            elif not self.__LINK["cli"].loading:
                self.__LINK["drones"] = [0]*self.__LINK["cli"].SYNC["DC"]
                self.__scrapCollected = self.__LINK["cli"].SYNC["S"]
                self.__LINK["shipData"]["scrap"] = self.__scrapCollected
                self.__upgrades = self.__LINK["cli"].SYNC["UC"]
        if not self.__LINK["controller"] is None:
            if self.__LINK["controller"].getMenuUpChange():
                if self.__LINK["controller"].getMenuUp():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_UP}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_UP}))
            if self.__LINK["controller"].getMenuDownChange():
                if self.__LINK["controller"].getMenuDown():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_DOWN}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_DOWN}))
            if self.__LINK["controller"].getMenuLeftChange():
                if self.__LINK["controller"].getMenuLeft():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_LEFT}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_LEFT}))
            if self.__LINK["controller"].getMenuRightChange():
                if self.__LINK["controller"].getMenuRight():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_RIGHT}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_RIGHT}))
            if self.__LINK["controller"].selectChange():
                if self.__LINK["controller"].select():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_RETURN}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_RETURN}))
            if self.__LINK["controller"].quickOpenChange():
                if self.__LINK["controller"].quickOpen():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_LCTRL}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_LCTRL}))
            if self.__LINK["controller"].backChange():
                if self.__LINK["controller"].back():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_d}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_d}))
            if self.__LINK["controller"].enterScematicViewChange():
                if self.__LINK["controller"].enterScematicView():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_f}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_f}))
            if self.__LINK["controller"].beforeDrone():
                self.__tab = False
            if self.__LINK["controller"].nextDrone():
                self.__tab = True
        if self.__displayInfo[0]: #Game is in info display menu
            for event in kBuf: #Loop for return button pressed
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.__displayInfo[0] = False
            return 0
        for event in kBuf: #Keyboard event
            if event.type == pygame.KEYUP:
                self.__HoldKeys[event.key] = False
            elif event.type == pygame.KEYDOWN: #A key was pressed
                self.__HoldKeys[event.key] = True
                if event.key == pygame.K_LEFT: #Move to previous ship
                    if self.__dialog[0]:
                        self.__dialog[3] = 1
                    elif self.__tab: #Is in tab view
                        if self.__sels[-1]==0: #Is selecting a window
                            self.__sels[0]-=1 #Go to previous window
                            if self.__sels[0]<0: #Go to last
                                self.__sels[0]=2
                        elif self.__sels[0]==2: #Selecting a drone
                            if self.__sels[-1]==1:
                                if self.__isKeyDown(pygame.K_LCTRL): #Shift a drone to the left, swapping it with any drones to the left
                                    if self.__LINK["multi"]==1: #Game is running as a client
                                        MXD,MXR,Nlink,Nl2 = self.__getDroneInfo()
                                        if self.__sels[1]<MXD and not MXD==0:
                                            self.__LINK["cli"].sendTrigger("swdr",self.__sels[1],-1)
                                        elif self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<MXR and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0:
                                            self.__LINK["cli"].sendTrigger("swdr",self.__sels[1],-1)
                                    elif self.__sels[1]<len(self.__LINK["drones"]) and not len(self.__LINK["drones"])==0:
                                        next = (self.__sels[1]-1)%len(self.__LINK["drones"])
                                        self.__LINK["drones"][self.__sels[1]],self.__LINK["drones"][next] = self.__LINK["drones"][next],self.__LINK["drones"][self.__sels[1]]
                                        self.__recalculateDroneNumbers()
                                    elif self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<len(self.__LINK["shipData"]["reserve"]) and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0:
                                        next = (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]-1)%len(self.__LINK["shipData"]["reserve"])
                                        self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]],self.__LINK["shipData"]["reserve"][next] = self.__LINK["shipData"]["reserve"][next],self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
                                        self.__recalculateDroneNumbers()
                                self.__sels[1]-=1
                                if self.__sels[1]<0: #Below begining, moving to the end
                                    self.__sels[1] = self.__LINK["shipData"]["maxDrones"]+self.__LINK["shipData"]["maxReserve"]-1
                            elif self.__sels[-1]==3: #Selecting an upgrade from the reserve
                                sx,sy = self.__LINK["main"].get_size()
                                if self.__sels[2]>=int((sy-425)/30): #Go to previous column
                                    self.__sels[2]-=int((sy-425)/30)
                    else: #In ship selecting tab
                        self.__sel -= 1
                        if self.__sel<0:
                            self.__sel = len(self.maps)-1
                elif event.key == pygame.K_RIGHT: #Move to next ship
                    if self.__dialog[0]:
                        self.__dialog[3] = 0
                    elif self.__tab: #Is in tab view
                        if self.__sels[-1]==0: #Is selecting a window
                            self.__sels[0]+=1 #Go to next window
                            if self.__sels[0]>2: #Go to first
                                self.__sels[0]=0
                        elif self.__sels[0]==2: #In the drone config window
                            if self.__sels[-1]==1: #Selecting a drone
                                if self.__isKeyDown(pygame.K_LCTRL): #Shift a drone to the right, swapping it with any drones to the right
                                    if self.__LINK["multi"]==1: #Game is running as a client
                                        MXD,MXR,Nlink,Nl2 = self.__getDroneInfo()
                                        if self.__sels[1]<MXD and not MXD==0:
                                            self.__LINK["cli"].sendTrigger("swdr",self.__sels[1],1)
                                        elif self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<MXR and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0:
                                            self.__LINK["cli"].sendTrigger("swdr",self.__sels[1],1)
                                    elif self.__sels[1]<len(self.__LINK["drones"]) and not len(self.__LINK["drones"])==0:
                                        next = (self.__sels[1]+1)%len(self.__LINK["drones"])
                                        self.__LINK["drones"][self.__sels[1]],self.__LINK["drones"][next] = self.__LINK["drones"][next],self.__LINK["drones"][self.__sels[1]]
                                        self.__recalculateDroneNumbers()
                                    elif self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<len(self.__LINK["shipData"]["reserve"]) and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0:
                                        next = (self.__sels[1]+self.__LINK["shipData"]["maxDrones"]-1)%len(self.__LINK["shipData"]["reserve"])
                                        self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]],self.__LINK["shipData"]["reserve"][next] = self.__LINK["shipData"]["reserve"][next],self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
                                        self.__recalculateDroneNumbers()
                                self.__sels[1]+=1
                                if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]+self.__LINK["shipData"]["maxReserve"]: #At the end, go to begining
                                    self.__sels[1] = 0
                            elif self.__sels[-1]==3: #Selecting an upgrade
                                sx,sy = self.__LINK["main"].get_size()
                                self.__sels[2]+=int((sy-425)/30) #Go to next column
                                if self.__sels[2]>=self.__LINK["shipData"]["maxInvent"]: #Hit end, go to last box
                                    self.__sels[2] = self.__LINK["shipData"]["maxInvent"]-1
                    else: #In ship selecting tab
                        self.__sel += 1
                        if self.__sel>=len(self.maps):
                            self.__sel = 0
                elif event.key == pygame.K_UP and self.__tab: #Up arrow
                    if self.__dialog[0]:
                        pass
                    elif self.__sels[0]==0 and self.__sels[-1]==1: #In ship upgrade selecting window
                        self.__sels[1]-=1 #Before upgrade
                        if self.__sels[1]<0: #Exit out to window selecting
                            self.__sels[-1] = 0
                            self.__sels[1] = 0
                    elif self.__sels[0]==1 and self.__sels[-1]==1: #In assembly window
                        self.__sels[1]-=1 #Before item
                        if self.__sels[1]<0: #Exit out to window selecting
                            self.__sels[-1] = 0
                            self.__sels[1] = 0
                    elif self.__sels[0]==2: #In drone upgrade window
                        if self.__sels[-1]==1:
                            self.__sels[-1]-=1 #Before window widget
                        elif self.__sels[-1]==2: #Selecting drone upgrade
                            self.__sels[2]-=1
                            if self.__sels[2]<0: #Go into drone selecting mode
                                self.__sels[2] = 0
                                self.__sels[-1]-=1
                        elif self.__sels[-1]==3: #Selecting an upgrade from reserves
                            DR = None #Get the drone being selected
                            if self.__LINK["multi"]==1: #Game is running as a client
                                MXD,MXR,Nlink,Nl2 = self.__getDroneInfo()
                                if self.__sels[1]<MXD:
                                    DR = Nlink[self.__sels[1]]
                                elif self.__sels[1]>=self.__LINK["shipData"]["maxDrones"] and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<MXR:
                                    DR = Nlink[self.__sels[1]]
                            elif self.__sels[1]<len(self.__LINK["drones"]): #Drone is in drone fleet
                                DR = self.__LINK["drones"][self.__sels[1]]
                            else: #Drone is in reserve fleet
                                DR = self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
                            sx,sy = self.__LINK["main"].get_size()
                            if self.__sels[2]%int((sy-425)/30)==0 and not DR is None: #Is at top of screen, go back to drone upgrade selecting
                                self.__sels[-1] -= 1
                                if self.__LINK["multi"]==1: #Game is running as a client
                                    self.__sels[2] = self.__LINK["cli"].SYNC["D"+str(DR)]["US"]-1
                                else: #Game is running in single player
                                    self.__sels[2] = len(DR.settings["upgrades"])-1
                            elif DR is None: #Exit to drone selecting since previous drone doesen't exist anymore
                                self.__sels[-1] -= 2
                            else: #Normaly move the cursor upwards
                                self.__sels[2]-=1
                elif event.key == pygame.K_DOWN and self.__tab: #Down arrow
                    if self.__dialog[0]:
                        pass
                    elif self.__sels[-1]==0: #Selecting area
                        self.__sels[-1] += 1
                        self.__sels[1] = 0
                    elif self.__sels[0]==0 and self.__sels[-1]==1: #In ship upgrade selecting window
                        self.__sels[1]+=1 #Next upgrade
                        if self.__sels[1]>=self.__LINK["shipData"]["maxShipUpgs"]+self.__LINK["shipData"]["reserveMax"]: #Reset back to first upgrade
                            self.__sels[1]=0
                    elif self.__sels[0]==1 and self.__sels[-1]==1: #In assembly window
                        self.__sels[1]+=1 #Next item
                        if self.__sels[1]>=4: #Reset back to first item
                            self.__sels[1]=0
                    elif self.__sels[0]==2: #Drone config menu
                        if self.__sels[-1]==1 and self.__LINK["multi"]==1: #Selecting a drone when running as a client
                            MXD,MXR,Nlink,Nl2 = self.__getDroneInfo()
                            if self.__sels[1]<MXD or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<MXR and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
                                self.__sels[-1]+=1
                                self.__sels[2] = 0
                        elif self.__sels[-1]==1: #Selecting drone
                            if self.__sels[1]<len(self.__LINK["drones"]) or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<len(self.__LINK["shipData"]["reserve"]) and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
                                self.__sels[-1]+=1
                                self.__sels[2] = 0
                        elif self.__sels[-1]==2: #Selecting drone upgrade (inside drone)
                            self.__sels[2] += 1
                            if self.__LINK["multi"]==1: #Game is runnign as as client
                                MXD,MXR,Nlink,Nl2 = self.__getDroneInfo()
                                if self.__sels[2]>=self.__LINK["cli"].SYNC["D"+str(Nlink[self.__sels[1]])]["US"]: #Go down into upgrade selection area
                                    self.__sels[-1] +=1 #Go to upgrade reserves
                                    self.__sels[2] = 0
                            else:
                                DR = None #Get the drone being selected
                                if self.__sels[1]<len(self.__LINK["drones"]): #Drone is in drone fleet
                                    DR = self.__LINK["drones"][self.__sels[1]]
                                else: #Drone is in reserve fleet
                                    DR = self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
                                if self.__sels[2]>=len(DR.settings["upgrades"]): #Go down into upgrade selection area
                                    self.__sels[-1] +=1 #Go to upgrade reserves
                                    self.__sels[2] = 0
                        elif self.__sels[-1]==3: #Selecting an upgrade from reserves
                            self.__sels[2] += 1
                            if self.__sels[2]>=self.__LINK["shipData"]["maxInvent"]: #Hit the end of the screen, make sure user cannot select past.
                                self.__sels[2] = self.__LINK["shipData"]["maxInvent"]-1
                elif event.key == pygame.K_d:
                    self.__dialog[0] = False
                    if self.__sels[0]==0 and self.__sels[-1]==1 and self.__tab:
                        UPG = None
                        MX,MXR,Nlink = self.__getShipInfo()
                        if self.__LINK["multi"]==1:
                            if self.__sels[1]>=self.__LINK["shipData"]["maxShipUpgs"]:
                                if self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"]<MXR:
                                    UPG = [self.__LINK["cli"].SYNC["G"+str(Nlink[self.__sels[1]])]["N"],self.__LINK["cli"].SYNC["G"+str(Nlink[self.__sels[1]])]["D"]]
                            elif self.__sels[1]<MX:
                                UPG = [self.__LINK["cli"].SYNC["G"+str(Nlink[self.__sels[1]])]["N"],self.__LINK["cli"].SYNC["G"+str(Nlink[self.__sels[1]])]["D"]]
                        elif self.__sels[1]>=self.__LINK["shipData"]["maxShipUpgs"]: #Something in the reserved ship upgrades
                            if self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"]<len(self.__LINK["shipData"]["reserveUpgs"]):
                                UPG = self.__LINK["shipData"]["reserveUpgs"][self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"]]
                        else: #Something in the ship upgrades
                            if self.__sels[1]<len(self.__LINK["shipData"]["shipUpgs"]):
                                UPG = self.__LINK["shipData"]["shipUpgs"][self.__sels[1]]
                        if not UPG is None:
                            self.__dialog[0] = True
                            self.__dialog[1] = "Dismantle '"+UPG[0]+"'? ("+str(int(PRICE[UPG[0]]/(UPG[1]+1)))+")"
                            self.__dialog[2] = self.__dismantleShipUpgrade
                    elif self.__sels[0]==2 and self.__tab: #Inventory config area
                        self.__dialog[2] = self.__dismantleDroneOrUpgrade
                        if self.__sels[-1]==1: #Dismantle a drone
                            DRONE = None
                            if self.__LINK["multi"]==1: #Running as a client
                                MXD,MXR,Nlink,Nl2 = self.__getDroneInfo()
                                if self.__sels[1]<MXD or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<MXR and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
                                    DRONE = "D"+str(Nlink[self.__sels[1]])
                            else: #Running in single player
                                if self.__sels[1]<len(self.__LINK["drones"]) or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<len(self.__LINK["shipData"]["reserve"]) and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
                                    if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]: #Cursor is in reserve drones
                                        DRONE = self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
                                    else: #Move to reserve squad
                                        DRONE = self.__LINK["drones"][self.__sels[1]]
                            if not DRONE is None:
                                self.__dialog[0] = True
                                if self.__LINK["multi"]==1:
                                    self.__dialog[1] = "Dismantle drone '"+self.__LINK["cli"].SYNC[DRONE]["N"]+"'? ("+str(self.__calculateScrap(DRONE))+")"
                                else:
                                    self.__dialog[1] = "Dismantle drone '"+DRONE.settings["name"]+"'? ("+str(self.__calculateScrap(DRONE))+")"
                        elif self.__sels[-1]==2: #Selecting an upgrade inside the drone
                            DRONE = None
                            if self.__LINK["multi"]==1: #Running as a client
                                MXD,MXR,Nlink,Nl2 = self.__getDroneInfo()
                                if self.__sels[1]<MXD or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<MXR and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
                                    DRONE = "D"+str(Nlink[self.__sels[1]])
                            else:
                                if self.__sels[1]<len(self.__LINK["drones"]) or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<len(self.__LINK["shipData"]["reserve"]) and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
                                    if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]: #Cursor is in reserve drones
                                        DRONE = self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
                                    else: #Move to reserve squad
                                        DRONE = self.__LINK["drones"][self.__sels[1]]
                            if not DRONE is None:
                                if self.__LINK["multi"]==1: #Game is running as a client
                                    upgC = self.__getDroneUpgradeCount(DRONE[1:])
                                    if self.__sels[2]<upgC:
                                        self.__dialog[0] = True
                                        upg = self.__LINK["cli"].SYNC[DRONE]["U"+str(self.__sels[2])].split(",")
                                        self.__dialog[1] = "Dismantle upgrade '"+upg[0]+"'? ("+str(self.__calculateScrap(upg))+")"
                                elif self.__sels[2]<len(DRONE.upgrades):
                                    self.__dialog[0] = True
                                    self.__dialog[1] = "Dismantle upgrade '"+DRONE.settings["upgrades"][self.__sels[2]][0]+"'? ("+str(self.__calculateScrap(DRONE.upgrades[self.__sels[2]]))+")"
                        elif self.__sels[-1]==3: #Selecing an upgrade inside the inventory
                            if self.__LINK["multi"]==1: #Game is running as a client
                                MX,Nlink = self.__getInventInfo()
                                if self.__sels[2]<MX:
                                    self.__dialog[0] = True
                                    Upg = self.__LINK["cli"].SYNC["U"+str(Nlink[self.__sels[2]])]
                                    self.__dialog[1] = "Dismantle upgrade '"+Upg["N"]+"'? ("+str(self.__calculateScrap([Upg["N"],Upg["D"]]))+")"
                            elif self.__sels[2]<len(self.__LINK["shipData"]["invent"]):
                                self.__dialog[0] = True
                                self.__dialog[1] = "Dismantle upgrade '"+self.__LINK["shipData"]["invent"][self.__sels[2]][0]+"'? ("+str(self.__calculateScrap(self.__LINK["shipData"]["invent"][self.__sels[2]]))+")"
                elif event.key == pygame.K_f and not self.__dialog[0] and self.__tab:
                    if self.__sels[0]==0 and self.__sels[-1]==1:
                        UPG = None
                        MX,MXR,Nlink = self.__getShipInfo()
                        if self.__LINK["multi"]==1:
                            if self.__sels[1]>=self.__LINK["shipData"]["maxShipUpgs"]:
                                if self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"]<MXR:
                                    UPG = [self.__LINK["cli"].SYNC["G"+str(Nlink[self.__sels[1]])]["N"],self.__LINK["cli"].SYNC["G"+str(Nlink[self.__sels[1]])]["D"]]
                            elif self.__sels[1]<MX:
                                UPG = [self.__LINK["cli"].SYNC["G"+str(Nlink[self.__sels[1]])]["N"],self.__LINK["cli"].SYNC["G"+str(Nlink[self.__sels[1]])]["D"]]
                        elif self.__sels[1]>=self.__LINK["shipData"]["maxShipUpgs"]: #Something in the reserved ship upgrades
                            if self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"]<len(self.__LINK["shipData"]["reserveUpgs"]):
                                UPG = self.__LINK["shipData"]["reserveUpgs"][self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"]]
                        else: #Something in the ship upgrades
                            if self.__sels[1]<len(self.__LINK["shipData"]["shipUpgs"]):
                                UPG = self.__LINK["shipData"]["shipUpgs"][self.__sels[1]]
                        if not UPG is None:
                            if UPG[1]!=2 and self.__LINK["shipData"]["scrap"]>int(PRICE[UPG[0]]/2) and UPG[1]!=0: #Upgrade is not dead and is failing
                                self.__dialog[0] = True
                                self.__dialog[1] = "Fix '"+UPG[0]+"'? ("+str(int(PRICE[UPG[0]]/2))+")"
                                self.__dialog[2] = self.__fixShipUpgrade
                    elif self.__sels[0]==2:
                        self.__dialog[2] = self.__fixDroneOrUpgrade
                        DRONE = None
                        if self.__sels[-1]!=3:
                            DRONE = None
                            if self.__LINK["multi"]==1: #Running as a client
                                MXD,MXR,Nlink,Nl2 = self.__getDroneInfo()
                                if self.__sels[1]<MXD or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<MXR and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
                                    DRONE = "D"+str(Nlink[self.__sels[1]])
                            else:
                                if self.__sels[1]<len(self.__LINK["drones"]) or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<len(self.__LINK["shipData"]["reserve"]) and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
                                    if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]: #Cursor is in reserve drones
                                        DRONE = self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
                                    else: #Move to reserve squad
                                        DRONE = self.__LINK["drones"][self.__sels[1]]
                        if self.__sels[-1]==1: #Fix a drone
                            if not DRONE is None:
                                if self.__LINK["multi"]==1: #Game is running as a clinet
                                    MXD,MXR,Nlink,Nl2 = self.__getDroneInfo()
                                    DR = self.__LINK["cli"].SYNC[DRONE]
                                    if DR["H"]!=DR["HM"] and self.__LINK["shipData"]["scrap"]>=round((1-(DR["H"]/DR["HM"]))*8):
                                        self.__dialog[0] = True
                                        self.__dialog[1] = "Fix drone '"+DR["N"]+"'? ("+str(round((1-(DR["H"]/DR["HM"]))*8))+")"
                                elif DRONE.health!=DRONE.settings["maxHealth"] and self.__LINK["shipData"]["scrap"]>=round((1-(DRONE.health/DRONE.settings["maxHealth"]))*8):
                                    self.__dialog[0] = True
                                    self.__dialog[1] = "Fix drone '"+DRONE.settings["name"]+"'? ("+str(round((1-(DRONE.health/DRONE.settings["maxHealth"]))*8))+")"
                        elif self.__sels[-1]==2: #Selecting an upgrade inside the drone
                            if not DRONE is None:
                                if self.__LINK["multi"]==1: #Game is running as a client
                                    MXD,MXR,Nlink,Nl2 = self.__getDroneInfo()
                                    DR = self.__LINK["cli"].SYNC[DRONE]
                                    MXU = self.__getDroneUpgradeCount(DRONE[1:])
                                    if self.__sels[2]<MXU:
                                        UPG = DR["U"+str(self.__sels[2])].split(",")
                                        if int(UPG[1])==1 and self.__LINK["shipData"]["scrap"]>=self.__calculateScrap(UPG)/2: #Upgrade is damaged and player has enough scrap to fix
                                            self.__dialog[0] = True
                                            self.__dialog[1] = "Fix upgrade '"+UPG[0]+"'? ("+str(self.__calculateScrap(UPG)/2)+")"
                                elif self.__sels[2]<len(DRONE.upgrades):
                                    if DRONE.settings["upgrades"][self.__sels[2]][1]==1 and self.__LINK["shipData"]["scrap"]>=self.__calculateScrap(DRONE.upgrades[self.__sels[2]])/2:
                                        self.__dialog[0] = True
                                        self.__dialog[1] = "Fix upgrade '"+DRONE.settings["upgrades"][self.__sels[2]][0]+"'? ("+str(self.__calculateScrap(DRONE.upgrades[self.__sels[2]])/2)+")"
                        elif self.__sels[-1]==3: #Selecing an upgrade inside the inventory
                            if self.__LINK["multi"]==1: #Game is running as a client
                                MX,Nlink = self.__getInventInfo()
                                if self.__sels[2]<MX:
                                    Upg = self.__LINK["cli"].SYNC["U"+str(Nlink[self.__sels[2]])]
                                    if Upg["D"]==1 and self.__LINK["shipData"]["scrap"]>=self.__calculateScrap([Upg["N"],Upg["D"]])/2:
                                        self.__dialog[0] = True
                                        self.__dialog[1] = "Fix upgrade '"+Upg["N"]+"'? ("+str(self.__calculateScrap([Upg["N"],Upg["D"]])/2)+")"
                            elif self.__sels[2]<len(self.__LINK["shipData"]["invent"]):
                                if self.__LINK["shipData"]["invent"][self.__sels[2]][1]==1 and self.__LINK["shipData"]["scrap"]>=self.__calculateScrap(self.__LINK["shipData"]["invent"][self.__sels[2]])/2:
                                    self.__dialog[0] = True
                                    self.__dialog[1] = "Fix upgrade '"+self.__LINK["shipData"]["invent"][self.__sels[2]][0]+"'? ("+str(self.__calculateScrap(self.__LINK["shipData"]["invent"][self.__sels[2]])/2)+")"
                elif event.key == pygame.K_RETURN: #Selecting key was pressed
                    if self.__dialog[0]:
                        self.__dialog[0] = False
                        if self.__dialog[3]==1:
                            self.__dialog[2]()
                    elif self.__tab: #In window tab view
                        if self.__sels[0]==0 and self.__sels[-1]==1:
                            if self.__sels[1]>=self.__LINK["shipData"]["maxShipUpgs"]: #Putting something into the ship upgrades
                                if self.__LINK["multi"]==1: #Game is running as client
                                    MUX,MUR,Nlink = self.__getShipInfo()
                                    if MUX<self.__LINK["shipData"]["maxShipUpgs"] and self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"]<MUR:
                                        self.__LINK["cli"].sendTrigger("bob",self.__sels[1])
                                elif len(self.__LINK["shipData"]["shipUpgs"])<self.__LINK["shipData"]["maxShipUpgs"] and self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"]<len(self.__LINK["shipData"]["reserveUpgs"]):
                                    self.__LINK["shipData"]["shipUpgs"].append(self.__LINK["shipData"]["reserveUpgs"].pop(self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"]))
                            else: #Move from upgrades to reserve
                                if self.__LINK["multi"]==1: #Game is running as client
                                    MUX,MUR,Nlink = self.__getShipInfo()
                                    if MUR<self.__LINK["shipData"]["reserveMax"] and self.__sels[1]<MUX:
                                        self.__LINK["cli"].sendTrigger("bob",self.__sels[1])
                                elif len(self.__LINK["shipData"]["reserveUpgs"])<self.__LINK["shipData"]["reserveMax"] and self.__sels[1]<len(self.__LINK["shipData"]["shipUpgs"]):
                                    self.__LINK["shipData"]["reserveUpgs"].append(self.__LINK["shipData"]["shipUpgs"].pop(self.__sels[1]))
                        elif self.__sels[0]==1 and self.__sels[-1]==1: #Buying an upgrade
                            UPG = ["generator","gather","interface","tow"][self.__sels[1]]
                            MX = 0
                            if self.__LINK["multi"]==1: #Game is running as a client
                                MX,Nlink = self.__getInventInfo()
                            else:
                                MX = len(self.__LINK["shipData"]["invent"])
                            if self.__LINK["shipData"]["scrap"]>=PRICE[UPG] and MX<self.__LINK["shipData"]["maxInvent"]:
                                self.__dialog[0] = True
                                self.__dialog[1] = "Are you sure you want to spend "+str(PRICE[UPG])+" scrap?"
                                self.__dialog[2] = self.__buyUpgrade
                        elif self.__sels[0]==2: #Drone upgrade config
                            if self.__sels[-1]==1: #Moving drone to and from the reserve slots
                                MXD = 0
                                MXR = 0
                                if self.__LINK["multi"]==1: #Game is running as a client
                                    MXD,MXR,NLINK,NLINK2 = self.__getDroneInfo()
                                else:
                                    MXD = len(self.__LINK["drones"])
                                    MXR = len(self.__LINK["shipData"]["reserve"])
                                if self.__sels[1]<MXD or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<MXR and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
                                    if self.__LINK["multi"]==1: #Running as a client
                                        if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]:
                                            if MXD<self.__LINK["shipData"]["maxDrones"]:
                                                self.__LINK["cli"].sendTrigger("dswp",self.__sels[1]) #Ask server to swap drones
                                        elif MXR<self.__LINK["shipData"]["maxReserve"]:
                                            self.__LINK["cli"].sendTrigger("dswp",self.__sels[1]) #Ask server to swap drones
                                    elif self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]: #Move to drone squad
                                        if len(self.__LINK["drones"])<self.__LINK["shipData"]["maxDrones"]:
                                            self.__LINK["drones"].append(self.__LINK["shipData"]["reserve"].pop(self.__sels[1]-self.__LINK["shipData"]["maxDrones"]))
                                            self.__recalculateDroneNumbers()
                                    else: #Move to reserve squad
                                        if len(self.__LINK["shipData"]["reserve"])<self.__LINK["shipData"]["maxReserve"]:
                                            self.__LINK["shipData"]["reserve"].append(self.__LINK["drones"].pop(self.__sels[1]))
                                            self.__recalculateDroneNumbers()
                            elif self.__sels[-1]==2: #Moving an upgrade from the drone to reserve upgrades
                                DRONE = None
                                if self.__LINK["multi"]==1: #Game is running as a client
                                    MXD,MXR, Nlink,Nlink2 = self.__getDroneInfo()
                                    if self.__sels[1]<MXD:
                                        DRONE = Nlink[self.__sels[1]]
                                    elif self.__sels[1]>=self.__LINK["shipData"]["maxDrones"] and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<MXR:
                                        DRONE = Nlink[self.__sels[1]]
                                elif self.__sels[1]<len(self.__LINK["drones"]) or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<len(self.__LINK["shipData"]["reserve"]) and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
                                    if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]: #Cursor is in reserve drones
                                        DRONE = self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
                                    else: #Move to reserve squad
                                        DRONE = self.__LINK["drones"][self.__sels[1]]
                                if not DRONE is None:
                                    if self.__LINK["multi"]==1: #Game is running as a client
                                        MX = self.__getDroneUpgradeCount(DRONE)
                                        if self.__sels[2]<MX:
                                            MX,Nlink = self.__getInventInfo()
                                            if MX<self.__LINK["shipData"]["maxInvent"]:
                                                self.__LINK["cli"].sendTrigger("mufd",self.__sels[1],self.__sels[2])
                                    elif self.__sels[2]<len(DRONE.upgrades) and len(self.__LINK["shipData"]["invent"])<self.__LINK["shipData"]["maxInvent"]: #Game is running in single player
                                        DRONE.unloadUpgrades()
                                        self.__LINK["shipData"]["invent"].append(DRONE.settings["upgrades"][self.__sels[2]].copy())
                                        DRONE.upgrades.pop(self.__sels[2])
                                        DRONE.unloadUpgrades()
                            elif self.__sels[-1]==3: #Moving an upgrade from reserve to a drone
                                DRONE = None
                                if self.__LINK["multi"]==1: #Game is running as a client
                                    MXD,MXR, Nlink, Nlink2 = self.__getDroneInfo()
                                    if self.__sels[1]<MXD:
                                        DRONE = Nlink[self.__sels[1]]
                                    elif self.__sels[1]>=self.__LINK["shipData"]["maxDrones"] and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<MXR:
                                        DRONE = Nlink[self.__sels[1]]
                                elif self.__sels[1]<len(self.__LINK["drones"]) or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<len(self.__LINK["shipData"]["reserve"]) and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
                                    if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]: #Cursor is in reserve drones
                                        DRONE = self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
                                    else: #Move to reserve squad
                                        DRONE = self.__LINK["drones"][self.__sels[1]]
                                if not DRONE is None: #Drone exists
                                    if self.__LINK["multi"]==1: #Game is running as a client
                                        MX = self.__getDroneUpgradeCount(DRONE)
                                        if MX<self.__LINK["cli"].SYNC["D"+str(DRONE)]["US"]:
                                            MX2,Nlink = self.__getInventInfo()
                                            if self.__sels[2]<MX2:
                                                self.__LINK["cli"].sendTrigger("mutd",self.__sels[1],self.__sels[2])
                                    elif self.__sels[2]<len(self.__LINK["shipData"]["invent"]) and len(DRONE.upgrades)<len(DRONE.settings["upgrades"]): #Can move
                                        DRONE.unloadUpgrades()
                                        DRONE.settings["upgrades"][len(DRONE.upgrades)] = self.__LINK["shipData"]["invent"].pop(self.__sels[2])
                                        DRONE.loadUpgrades()
                    elif self.__LINK["shipData"]["fuel"]>=self.maps[self.__sel][5]: #Load a ship
                        self.__dialog[0] = True
                        self.__dialog[1] = "Are you sure you want to dock?"
                        self.__dialog[2] = self.selectShip
                elif event.key == pygame.K_TAB and not self.__dialog[0]:
                    self.__tab = not self.__tab
    def __gainScrap(self,scrap):
        self.__LINK["shipData"]["scrap"]+=scrap
        if self.__LINK["shipData"]["scrap"]>self.__scrapCopasity:
            self.__LINK["shipData"]["scrap"] = self.__scrapCopasity+0
        self.__scrapCollected = self.__LINK["shipData"]["scrap"]+0
        if self.__LINK["multi"]==2: #Game is running in a server
            self.__LINK["serv"].SYNC["S"] = self.__LINK["shipData"]["scrap"]
    def __calculateScrap(self,Ent): #Returns the scrap worth of a drone/upgrade (object not text)
        if self.__LINK["multi"]==1: #Game is running as a client
            if type(Ent)==str: #A Drone
                SCR = 0
                if self.__LINK["cli"].SYNC[Ent]["A"]: #Tempory
                    SCR = 12
                else:
                    SCR = 8
                for i in range(self.__LINK["cli"].SYNC[Ent]["US"]):
                    if self.__LINK["cli"].SYNC[Ent]["U"+str(i)]!="":
                        SCR += self.__calculateScrap(self.__LINK["cli"].SYNC[Ent]["U"+str(i)].split(","))
                return SCR
            elif type(Ent)==list: #Is an upgrade
                return PRICE[Ent[0]]/(int(Ent[1])+1)
        elif type(Ent)==self.getEnt("drone"):
            SCR = 0
            if Ent.alive: #Tempory
                SCR = 12
            else:
                SCR = 8
            for a in Ent.settings["upgrades"]:
                if a[0]!="":
                    SCR += PRICE[a[0]]/(a[1]+1)
            return SCR
        elif type(Ent)==list:
            return PRICE[Ent[0]]/(Ent[1]+1)
        else:
            return PRICE[Ent.name]/(Ent.damage+1)
    def __fixDroneOrUpgradeServer(self,sock,sels): #Called by clients to fix an upgrade in server
        MX1,MX2,Nlink = self.__getDroneInfo()
        MX,inf = self.__getInventInfo()
        if sels[1]>=self.__LINK["shipData"]["maxDrones"]: #In reserved squad
            for i,a in enumerate(self.__LINK["shipData"]["reserve"]):
                if a.GID==Nlink[sels[1]]:
                    self.__sels[1] = i+self.__LINK["shipData"]["maxDrones"]
                    break
        else: #Normal drone fleet
            for i,a in enumerate(self.__LINK["drones"]):
                if a.GID==Nlink[sels[1]]:
                    self.__sels[1] = i+0
                    break
        self.__sels[2] = sels[2]+0
        self.__sels[-1] = sels[-1]+0
        code = self.__fixDroneOrUpgrade()
        if code==1: #Update drone health
            self.__LINK["serv"].SYNC["D"+str(Nlink[sels[1]])]["A"] = True
            if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]:
                self.__LINK["serv"].SYNC["D"+str(Nlink[sels[1]])]["H"] = self.__LINK["drones"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]].health
            else:
                self.__LINK["serv"].SYNC["D"+str(Nlink[sels[1]])]["H"] = self.__LINK["drones"][self.__sels[1]].health
        elif code==2: #Update drone upgrades
            if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]:
                DR = self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
            else:
                DR = self.__LINK["drones"][self.__sels[1]]
            for i2,b in enumerate(DR.settings["upgrades"]): #Sync all the drones upgrades
                if b[0]=="":
                    self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = ""
                else:
                    if len(b)==5:
                        if len(b[4])!=0:
                            self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])+","+str(b[4][0])
                        else:
                            self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])
                    else:
                        self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])
        elif code==3: #Update an inventoy item
            self.__LINK["serv"].SYNC["U"+str(inf[self.__sels[2]])]["D"] = self.__LINK["shipData"]["invent"][self.__sels[2]][1]+0
    def __fixDroneOrUpgrade(self): #Called to fix a drone or upgrade
        if self.__LINK["multi"]==1: #Game is running as a client
            self.__LINK["cli"].sendTrigger("fxud",self.__sels)
            return None
        DRONE = None
        if self.__sels[1]<len(self.__LINK["drones"]) or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<len(self.__LINK["shipData"]["reserve"]) and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
            if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]: #Cursor is in reserve drones
                DRONE = self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
            else: #Move to reserve squad
                DRONE = self.__LINK["drones"][self.__sels[1]]
        if not DRONE is None and self.__sels[-1]==1: #Calculate score for drone
            self.__LINK["shipData"]["scrap"]-=round((1-(DRONE.health/DRONE.settings["maxHealth"]))*8)
            DRONE.health = DRONE.settings["maxHealth"]+0
            DRONE.alive = True
            DRONE.aliveShow = True
            return 1
        elif self.__sels[-1]==2: #Fix an upgrade in a drone
            if self.__sels[2]<len(DRONE.upgrades):
                self.__LINK["shipData"]["scrap"]-=self.__calculateScrap(DRONE.upgrades[self.__sels[2]])/2
                DRONE.upgrades[self.__sels[2]].damage = 0
                DRONE.unloadUpgrades()
                return 2
        elif self.__sels[-1]==3: #Fix an upgrade in reserved upgrades (inventory)
            self.__LINK["shipData"]["scrap"]-=self.__calculateScrap(self.__LINK["shipData"]["invent"][self.__sels[2]])/2
            self.__LINK["shipData"]["invent"][self.__sels[2]][1] = 0
            return 3
        self.__scrapCollected = self.__LINK["shipData"]["scrap"] #Scrap inside the ship
    def __dismantleUpgradeServer(self,sock,sels): #Called by clients to dismantle an upgrade
        MX1,MX2,Nlink = self.__getDroneInfo()
        MX,inf = self.__getInventInfo()
        if sels[1]>=self.__LINK["shipData"]["maxDrones"]: #In reserved squad
            for i,a in enumerate(self.__LINK["shipData"]["reserve"]):
                if a.GID==Nlink[sels[1]]:
                    self.__sels[1] = i+self.__LINK["shipData"]["maxDrones"]
                    break
        else: #Normal drone fleet
            for i,a in enumerate(self.__LINK["drones"]):
                if a.GID==Nlink[sels[1]]:
                    self.__sels[1] = i+0
                    break
        self.__sels[2] = sels[2]+0
        self.__sels[-1] = sels[-1]+0
        obj = self.__dismantleDroneOrUpgrade()
        if type(obj)==self.getEnt("drone"): #Dismantled a drone
            self.__LINK["serv"].SYNC["D"+str(obj.GID)]["E"] = False
            if self.__LINK["serv"].SYNC["D"+str(obj.GID)]["O"]<self.__LINK["shipData"]["maxDrones"]:
                for i in range(self.__LINK["serv"].SYNC["D"+str(obj.GID)]["O"]+1,self.__LINK["shipData"]["maxDrones"]):
                    if i in Nlink:
                        if self.__LINK["serv"].SYNC["D"+str(Nlink[i])]["E"]:
                            self.__LINK["serv"].SYNC["D"+str(Nlink[i])]["O"] -= 1
            else:
                for i in range(self.__LINK["serv"].SYNC["D"+str(obj.GID)]["O"]+1,self.__LINK["shipData"]["maxDrones"]+self.__LINK["shipData"]["maxReserve"]):
                    if i in Nlink:
                        if self.__LINK["serv"].SYNC["D"+str(Nlink[i])]["E"]:
                            self.__LINK["serv"].SYNC["D"+str(Nlink[i])]["O"] -= 1
        elif type(obj)==list: #Is a reserved area upgrade
            #Remove the upgrade from the inventory area
            self.__LINK["serv"].SYNC["U"+str(inf[self.__sels[2]])]["E"] = False
            #Reload all the inventory upgrade positions to sync with users
            if self.__sels[2]!=0 and not self.__sels[2]>=len(self.__LINK["shipData"]["invent"]): #Is not the start or the end
                self.__LINK["serv"].SYNC["U"+str(inf[self.__sels[2]-1])]["P"] = inf[self.__sels[2]+1]+0
            elif self.__sels[2]>=len(self.__LINK["shipData"]["invent"]) and self.__sels[2]!=0:
                self.__LINK["serv"].SYNC["U"+str(inf[self.__sels[2]-1])]["P"] = -1
        else: #Must be an upgrade inside a drone
            if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]:
                DR = self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
            else:
                DR = self.__LINK["drones"][self.__sels[1]]
            self.__LINK["serv"].SYNC["D"+str(DR.GID)]["US"] = len(DR.settings["upgrades"]) #Drone upgrade amount
            for i2,b in enumerate(DR.settings["upgrades"]): #Sync all the drones upgrades
                if b[0]=="":
                    self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = ""
                else:
                    if len(b)==5:
                        if len(b[4])!=0:
                            self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])+","+str(b[4][0])
                        else:
                            self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])
                    else:
                        self.__LINK["serv"].SYNC["D"+str(DR.GID)]["U"+str(i2)] = b[0]+","+str(b[1])
    def __dismantleDroneOrUpgrade(self): #Called to dismantle a drone or an upgrade in the drone inventory config window
        if self.__LINK["multi"]==1: #Game is running as a client
            self.__LINK["cli"].sendTrigger("disu",self.__sels)
            return None
        DRONE = None
        if self.__sels[1]<len(self.__LINK["drones"]) or (self.__sels[1]-self.__LINK["shipData"]["maxDrones"]<len(self.__LINK["shipData"]["reserve"]) and self.__sels[1]-self.__LINK["shipData"]["maxDrones"]>=0):
            if self.__sels[1]>=self.__LINK["shipData"]["maxDrones"]: #Cursor is in reserve drones
                if self.__sels[-1]==1:
                    DRONE = self.__LINK["shipData"]["reserve"].pop(self.__sels[1]-self.__LINK["shipData"]["maxDrones"])
                else:
                    DRONE = self.__LINK["shipData"]["reserve"][self.__sels[1]-self.__LINK["shipData"]["maxDrones"]]
            else: #Remove from drone squad
                if self.__sels[-1]==1:
                    DRONE = self.__LINK["drones"].pop(self.__sels[1])
                else:
                    DRONE = self.__LINK["drones"][self.__sels[1]]
        UPG = None
        if not DRONE is None and self.__sels[-1]==1: #Calculate score for drone
            self.__gainScrap(self.__calculateScrap(DRONE))
        elif self.__sels[-1]==2: #Dismantle an upgrade
            if self.__sels[2]<len(DRONE.upgrades):
                UPG = DRONE.upgrades.pop(self.__sels[2])
                self.__gainScrap(self.__calculateScrap(UPG))
                DRONE.unloadUpgrades()
        elif self.__sels[-1]==3: #Dismantle upgrade inside inventory
            UPG = self.__LINK["shipData"]["invent"].pop(self.__sels[2])
            self.__gainScrap(self.__calculateScrap(UPG))
        if self.__sels[-1]==1:
            return DRONE
        return UPG
    def __buyUpgradeServer(self,sock,sel): #Called by clients to buy an upgrade
        self.__sels[1] = sel
        MX, refs = self.__getInventInfo()
        self.__buyUpgrade()
        key = "ERR"
        for i in range(0,self.__LINK["shipData"]["maxInvent"]):
            if not self.__LINK["serv"].SYNC["U"+str(i)]["E"]:
                key = "U"+str(i)
        self.__LINK["serv"].SYNC[key]["E"] = True
        self.__LINK["serv"].SYNC[key]["N"] = self.__LINK["shipData"]["invent"][len(self.__LINK["shipData"]["invent"])-1][0]
        self.__LINK["serv"].SYNC[key]["D"] = self.__LINK["shipData"]["invent"][len(self.__LINK["shipData"]["invent"])-1][1]
        self.__LINK["serv"].SYNC[key]["P"] = -1
        if len(self.__LINK["shipData"]["invent"])!=1: #Is not the first time an item has been put in
            self.__LINK["serv"].SYNC["U"+str(refs[MX-1])]["P"] = int(key[1:])
    def __buyUpgrade(self): #Buy an upgrade the user has selected
        if self.__LINK["multi"]==1: #Game is running as a client
            self.__LINK["cli"].sendTrigger("buy",self.__sels[1])
            return None
        UPG = ["generator","gather","interface","tow"][self.__sels[1]]
        self.__LINK["shipData"]["invent"].append([UPG,0,-1,0])
        self.__gainScrap(-PRICE[UPG])
    def __fixShipUpgradeServer(self,sock,sel): #Called by clients to fix a ship upgrade
        MX,MXR,Nlink,Nl2 = self.__getShipInfo()
        self.__sels[1] = sel
        self.__fixShipUpgrade()
        self.__LINK["serv"].SYNC["G"+str(Nlink[sel])]["D"] = 0
    def __fixShipUpgrade(self): #Fixes the upgrade the user has selected
        if self.__LINK["multi"]==1: #Game is running as a client
            self.__LINK["cli"].sendTrigger("fxsu",self.__sels[1])
            return None
        UPG = None
        if self.__sels[1]>=self.__LINK["shipData"]["maxShipUpgs"]: #Selecting an item from the ship upgrades
            UPG = self.__LINK["shipData"]["reserveUpgs"][self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"]]
        else: #Selecting an item from the reserve
            UPG = self.__LINK["shipData"]["shipUpgs"][self.__sels[1]]
        UPG[1] = 0
        if len(UPG)==4:
            UPG[3] = 0
        else:
            print("Failure to reset upgrade brake probability")
        self.__LINK["shipData"]["scrap"]-=int(PRICE[UPG[0]]/2)
        self.__scrapCollected = self.__LINK["shipData"]["scrap"] #Scrap inside the ship
    def __dismantleShipUpgradeServer(self,sock,sel): #Called by clients to dismantle a ship upgrade
        MX,MXR,Nlink,Nl2 = self.__getShipInfo()
        self.__sels[1] = sel
        Upg = self.__dismantleShipUpgrade()
        self.__LINK["serv"].SYNC["G"+str(Nl2[Upg[2]])]["E"] = False
        if self.__LINK["serv"].SYNC["G"+str(Nl2[Upg[2]])]["P"]<self.__LINK["shipData"]["maxShipUpgs"]:
            for i in range(self.__LINK["serv"].SYNC["G"+str(Nl2[Upg[2]])]["P"]+1,self.__LINK["shipData"]["maxShipUpgs"]):
                if i in Nlink:
                    if self.__LINK["serv"].SYNC["G"+str(Nlink[i])]["E"]:
                        self.__LINK["serv"].SYNC["G"+str(Nlink[i])]["P"] -= 1
        else:
            for i in range(self.__LINK["serv"].SYNC["G"+str(Nl2[Upg[2]])]["P"]+1,self.__LINK["shipData"]["maxShipUpgs"]+self.__LINK["shipData"]["reserveMax"]):
                if i in Nlink:
                    if self.__LINK["serv"].SYNC["G"+str(Nlink[i])]["E"]:
                        self.__LINK["serv"].SYNC["G"+str(Nlink[i])]["P"] -= 1
    def __dismantleShipUpgrade(self): #Dismantles the upgrade the user has selected
        if self.__LINK["multi"]==1: #Game is running as a client
            self.__LINK["cli"].sendTrigger("dssu",self.__sels[1])
            return None
        UPG = None
        if self.__sels[1]>=self.__LINK["shipData"]["maxShipUpgs"]: #Selecting an item from the ship upgrades
            UPG = self.__LINK["shipData"]["reserveUpgs"].pop(self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"])
        else: #Selecting an item from the reserve
            UPG = self.__LINK["shipData"]["shipUpgs"].pop(self.__sels[1])
        self.__gainScrap(PRICE[UPG[0]]/(UPG[1]+1))
        return UPG
    def selectShip(self,sl=None): #Opens the ship selected
        if self.__LINK["multi"]==1: #Game is being ran as a client
            self.__LINK["cli"].sendTrigger("sls",self.__sel)
        else:
            if not sl is None:
                self.__sel = sl+0
            self.__LINK["shipData"]["fuel"] -= self.maps[self.__sel][5]
            self.displayLoadingScreen()
            if self.__LINK["multi"]==2: #Running as a server
                self.__recalculateDroneNumbersByOrder()
            self.__LINK["shipData"]["beforeMap"] = self.__sel+0
            for i in range(len(self.__LINK["shipEnt"].settings["upgrades"])): #Empty ship upgrades
                self.__LINK["shipEnt"].settings["upgrades"][i] = ["",0,-1,0]
            for i,a in enumerate(self.__LINK["shipData"]["shipUpgs"]): #Apply ship upgrades to ship
                self.__LINK["shipEnt"].settings["upgrades"][i] = a.copy()
            self.__LINK["shipEnt"].loadUpgrades()
            if self.__LINK["multi"]!=2: #Is not the server
                self.__LINK["loadScreen"]("game")
                self.__LINK["currentScreen"].open("ShipSelect"+str(self.__sel))
    def render(self,surf=None): #Render the screen
        if surf is None:
            surf = self.__LINK["main"]
        smult = (abs(math.cos(time.time()*3))/2)+0.5 #Box flashing
        sx,sy = surf.get_size()
        if self.__LINK["hints"]:
            if self.__LINK["controller"] is None:
                surf.blit(self.__LINK["font16"].render("Press TAB to switch between tabs",16,(0,255*smult,255*smult)),[sx-770,15])
            else:
                LT = self.__LINK["controller"].keyName["bfDrone"]
                RT = self.__LINK["controller"].keyName["nxDrone"]
                surf.blit(self.__LINK["font16"].render("Press "+LT+" or "+RT+" to switch between tabs",16,(0,255*smult,255*smult)),[sx-770,15])
        if self.__tab: #In inventory tab
            self.__renderInventory(surf)
        else: #In ship selecting tab
            self.__renderShips(surf)
        if self.__dialog[0]: #Render yes/no dialog
            pygame.draw.rect(surf,(0,0,0),[(sx/2)-200,(sy/2)-50,400,100])
            pygame.draw.rect(surf,(0,255,0),[(sx/2)-200,(sy/2)-50,400,100],2)
            surf.blit(self.__LINK["font24"].render(self.__dialog[1],16,(255,255,255)),[(sx/2)-190,(sy/2)-40])
            surf.blit(self.__LINK["font42"].render("YES",16,(255,255,255)),[(sx/2)-190,(sy/2)+10])
            if self.__dialog[3]==0: #No option is selected
                pygame.draw.rect(surf,(0,200,0),[(sx/2)+148,(sy/2)+10,47,35],4)
                pygame.draw.rect(surf,(200,200,200),[(sx/2)-195,(sy/2)+10,65,35],1)
            else: #Yes option is selected
                pygame.draw.rect(surf,(200,200,200),[(sx/2)+148,(sy/2)+10,47,35],1)
                pygame.draw.rect(surf,(0,200,0),[(sx/2)-195,(sy/2)+10,65,35],4)
            surf.blit(self.__LINK["font42"].render("NO",16,(255,255,255)),[(sx/2)+153,(sy/2)+10])
            if self.__LINK["controller"] is None:
                surf.blit(self.__LINK["font24"].render("Presss enter to select",16,(255,255,255)),[(sx/2)-110,(sy/2)+15])
            else:
                A = self.__LINK["controller"].keyName["select"]
                surf.blit(self.__LINK["font24"].render("Presss "+A+" to select",16,(255,255,255)),[(sx/2)-110,(sy/2)+15])
        #Overlay
        if self.__LINK["backgroundStatic"]:
            self.__cols[self.__changeEffect[0]].set_alpha(OVERLAY_OPASITY-self.__changeEffect[1])
            self.__cols[(self.__changeEffect[0]+1)%len(self.__cols)].set_alpha(self.__changeEffect[1])
            surf.blit(self.__cols[self.__changeEffect[0]],(0,0))
            surf.blit(self.__cols[(self.__changeEffect[0]+1)%len(self.__cols)],(0,0))
    def __renderInventory(self,surf):
        sx,sy = surf.get_size()
        #Upper bar
        pygame.draw.rect(surf,(0,255,0),[10,10,sx-20,120],2)
        pygame.draw.line(surf,(0,255,0),[sx-310,10],[sx-310,130],2)
        pygame.draw.line(surf,(0,255,0),[sx-200,10],[sx-200,130],2)
        surf.blit(self.__LINK["font42"].render("SHIPS",16,(255,255,0)),(sx-300,30))
        surf.blit(self.__LINK["font42"].render("INVENTORY",16,(255,255,0)),(sx-190,30))
        surf.blit(self.__LINK["font64"].render(self.__shipName,16,(255,255,255)),(20,15))
        pygame.draw.polygon(surf,(100,100,100),[ (sx-300,110), (sx-210,110), (sx-255,80) ])
        pygame.draw.polygon(surf,(0,255,0),[ (sx-190,110), (sx-20,110), (sx-105,80) ])
        surf.blit(self.__LINK["font42"].render("DRONES: "+str(len(self.__LINK["drones"]))+"/"+str(self.__maxDrones),16,(0,255,255)),(sx-550,20))
        surf.blit(self.__LINK["font42"].render("UPGRADES: "+str(self.__upgrades)+"/"+str(self.__maxUpgrades),16,(0,255,255)),(sx-550,50))
        surf.blit(self.__LINK["font42"].render("MAX SCRAP: "+str(self.__scrapCopasity),16,(0,255,255)),(sx-550,80))
        surf.blit(self.__LINK["font42"].render("FUEL: "+str(self.__fuelLeft),16,(0,0,255)),(20,60))
        surf.blit(self.__LINK["font42"].render("SCRAP: "+str(int(self.__scrapCollected)),16,(0,0,255)),(20,90))
        #Upgrade managment
        if self.__sels[0]==0: #Ship upgrades menu
            self.__renderShipUpgrades(surf,True)
        else:
            self.__renderShipUpgrades(surf,False)
        if self.__sels[0]==1: #Upgrade creation menu
            self.__renderCreation(surf,True)
        else:
            self.__renderCreation(surf,False)
        if self.__sels[0]==2: #Drone upgrades menu
            self.__renderUpgrades(surf,True)
        else:
            self.__renderUpgrades(surf,False)
    def __renderCreation(self,surf,active=False): #Render upgrade creation menu
        if active: #Tab is active
            mult = 1
        else:
            mult = 0.2
        sx,sy = surf.get_size()
        smult = (abs(math.cos(time.time()*3))/2)+0.5 #Box flashing
        if self.__LINK["hints"] and active:
            if self.__LINK["controller"] is None:
                surf.blit(self.__LINK["font16"].render("Press Return to create selected upgrade",16,(0,255*smult,255*smult)),[180,70])
            else:
                A = self.__LINK["controller"].keyName["select"]
                surf.blit(self.__LINK["font16"].render("Press "+A+" to create selected upgrade",16,(0,255*smult,255*smult)),[180,70])
        pygame.draw.rect(surf,(0,255*mult,0),[320,140,300,sy-150],5)
        surf.blit(self.__LINK["font42"].render("ASSEMBLY",16,(255*mult,255*mult,255*mult)),[380,150])
        pygame.draw.line(surf,(0,255*mult,0),[320,190],[620,190],5)
        for i,a in enumerate(["generator","gather","interface","tow"]): #Render ship upgrades
            tex = ""
            tcol = (255*mult,255*mult,255*mult)
            col = (100*mult,100*mult,100*mult)
            if i==self.__sels[1] and self.__sels[0]==1 and self.__sels[-1]==1: #Slot is selected
                col = (255*smult,0,255*smult)
            pygame.draw.rect(surf,col,[330,200+(i*60),280,50],2)
            surf.blit(self.__LINK["font42"].render(a+" ("+str(PRICE[a])+")",16,tcol),[338,208+(i*60)])
        if self.__sels[-1]==0 and active: #Window is being selected
            pygame.draw.rect(surf,(255*smult,0,255*smult),[320,140,300,sy-150],5)
            pygame.draw.line(surf,(255*smult,0,255*smult),[320,190],[620,190],5)
    def getImage(self,name): #Gets an image, returns a error and defualt surface otherwise
        if name in self.__LINK["content"]: #Return the image
            return self.__LINK["content"][name]
        self.__LINK["errorDisplay"]("missing image '"+name+"'")
        gen = pygame.Surface((140,60))
        font = pygame.font.SysFont("impact",16)
        gen.blit(font.render("Error, missing image",16,(255,255,255)),[0,0])
        return gen
    def __renderUpgrades(self,surf,active=False): #Render drone upgrades menu
        if active: #Tab is active
            mult = 1
        else:
            mult = 0.2
        sx,sy = surf.get_size()
        smult = (abs(math.cos(time.time()*3))/2)+0.5 #Box flashing
        if self.__LINK["hints"] and active:
            if self.__LINK["controller"] is None:
                surf.blit(self.__LINK["font16"].render("Press F to fix selected upgrade/drone",16,(0,255*smult,255*smult)),[180,70])
                surf.blit(self.__LINK["font16"].render("Press D to dismantle selected upgrade/drone",16,(0,255*smult,255*smult)),[180,80])
                surf.blit(self.__LINK["font16"].render("Press Return to move selected upgrade/drone to and from reserve area",16,(0,255*smult,255*smult)),[180,90])
                surf.blit(self.__LINK["font16"].render("Hold Left CNTRL + arrow keys to move drone left or right",16,(0,255*smult,255*smult)),[180,100])
            else:
                F = self.__LINK["controller"].keyName["scem"]
                D = self.__LINK["controller"].keyName["back"]
                A = self.__LINK["controller"].keyName["select"]
                M = self.__LINK["controller"].keyName["qOpen"]
                surf.blit(self.__LINK["font16"].render("Press "+F+" to fix selected upgrade/drone",16,(0,255*smult,255*smult)),[180,70])
                surf.blit(self.__LINK["font16"].render("Press "+D+" to dismantle selected upgrade/drone",16,(0,255*smult,255*smult)),[180,80])
                surf.blit(self.__LINK["font16"].render("Press "+A+" to move selected upgrade/drone to and from reserve area",16,(0,255*smult,255*smult)),[180,90])
                surf.blit(self.__LINK["font16"].render("Hold "+A+" + arrow keys to move drone left or right",16,(0,255*smult,255*smult)),[180,100])
        if active and self.__sels[-1]==0:
            pygame.draw.rect(surf,(255*smult,0,255*smult),[630,140,sx-640,sy-150],5)
            pygame.draw.line(surf,(255*smult,0,255*smult),[630,400],[sx-10,400],5)
        else:
            pygame.draw.rect(surf,(0,255*mult,0),[630,140,sx-640,sy-150],5)
            pygame.draw.line(surf,(0,255*mult,0),[630,400],[sx-10,400],5)
        scroll = 0 #Amount to scroll past in drones
        if ((self.__LINK["shipData"]["maxDrones"]+self.__LINK["shipData"]["maxReserve"])*150)+640>sx-150 and self.__sels[0]==2: #Too many drone slots to fit into screen, go into scroll mode
            if (self.__sels[1]*150)+640>640+((sx-640)/2): #Scroll right
                scroll = int((((self.__sels[1]*150)+640)-(640+((sx-640)/2)))/150)
        MXD,MXR,NumLinks, NL2 = self.__getDroneInfo()
        for i3 in range(scroll,self.__LINK["shipData"]["maxDrones"]+self.__LINK["shipData"]["maxReserve"]): #Render the drones
            i = i3-scroll
            if 640+(i*150)>sx: #Going off the screen, render arrow and stop
                pygame.draw.polygon(surf,(255*mult,255*mult,255*mult),[(sx-30,160),(sx-30,380),(sx-15,270)])
                break
            if i3>=self.__LINK["shipData"]["maxDrones"]:
                if i3==self.__sels[1] and (self.__sels[-1]==1 or self.__sels[-1]==3) and self.__sels[0]==2:
                    pygame.draw.rect(surf,(255*smult,0,255*smult),[640+(i*150),150,140,240],3)
                    pygame.draw.line(surf,(255*smult,0,255*smult),[640+(i*150),260],[780+(i*150),260],3)
                else:
                    pygame.draw.rect(surf,(255*mult,255*mult,0),[640+(i*150),150,140,240],2)
                    pygame.draw.line(surf,(255*mult,255*mult,0),[640+(i*150),260],[780+(i*150),260],2)
            else:
                if i3==self.__sels[1] and (self.__sels[-1]==1 or self.__sels[-1]==3) and self.__sels[0]==2:
                    pygame.draw.rect(surf,(255*smult,0,255*smult),[640+(i*150),150,140,240],3)
                    pygame.draw.line(surf,(255*smult,0,255*smult),[640+(i*150),260],[780+(i*150),260],3)
                else:
                    pygame.draw.rect(surf,(0,255*mult,0),[640+(i*150),150,140,240],2)
                    pygame.draw.line(surf,(0,255*mult,0),[640+(i*150),260],[780+(i*150),260],2)
            if self.__isKeyDown(pygame.K_LCTRL) and i3==self.__sels[1] and self.__sels[-1]==1 and self.__sels[0]==2: #Render swapping arrows
                pygame.draw.polygon(surf,(255,255,255),[ (638+(i*150),190), (638+(i*150),350), (630+(i*150),270) ])
                pygame.draw.polygon(surf,(255,255,255),[ (630+((i+1)*150),190), (630+((i+1)*150),350), (640+((i+1)*150),270) ])
            a = None
            if i3<self.__LINK["shipData"]["maxDrones"] and i3<len(self.__LINK["drones"]):
                a = self.__LINK["drones"][i3]
            elif i3-self.__LINK["shipData"]["maxDrones"]<len(self.__LINK["shipData"]["reserve"]) and i3-self.__LINK["shipData"]["maxDrones"]>=0:
                a = self.__LINK["shipData"]["reserve"][i3-self.__LINK["shipData"]["maxDrones"]]
            if self.__LINK["multi"]==1: #Running as a client
                if i3 in NumLinks:
                    a = 0
                else:
                    a = None
            if not a is None:
                health = 0
                alive = False
                name = ""
                if self.__LINK["multi"]==1: #Running as a client
                    health = self.__LINK["cli"].SYNC["D"+str(NumLinks[i3])]["H"]/self.__LINK["cli"].SYNC["D"+str(NumLinks[i3])]["HM"]
                    alive = self.__LINK["cli"].SYNC["D"+str(NumLinks[i3])]["A"]
                    name = self.__LINK["cli"].SYNC["D"+str(NumLinks[i3])]["N"]
                else:
                    health = a.health/a.settings["maxHealth"]
                    alive = a.alive
                    name = a.settings["name"]
                pygame.draw.rect(surf,(0,100*mult,0),[642+(i*150),152+(108*(1-health)),137,108*health])
                if active:
                    if alive:
                        surf.blit(self.__droneNormal,[650+(i*150),164])
                    else:
                        surf.blit(self.__droneDead,[650+(i*150),164])
                else:
                    if alive:
                        surf.blit(self.__droneNormalDark,[650+(i*150),164])
                    else:
                        surf.blit(self.__droneDeadDark,[650+(i*150),164])
                surf.blit(self.__LINK["font16"].render(name,16,(255*mult,255*mult,255*mult)),(643+(i*150),152))
                #Render drones upgades
                if self.__LINK["multi"]==1: #Running as a client
                    for i2 in range(0,self.__LINK["cli"].SYNC["D"+str(NumLinks[i3])]["US"]):
                        if self.__LINK["cli"].SYNC["D"+str(NumLinks[i3])]["U"+str(i2)]=="": #Upgrade is empty
                            if self.__sels[-1]==2 and self.__sels[1]==i3 and self.__sels[2]==i2 and self.__sels[0]==2:
                                pygame.draw.rect(surf,(255*smult,0,255*smult),[650+(i*150),270+(i2*30),120,25],3)
                            else:
                                pygame.draw.rect(surf,(100*mult,100*mult,100*mult),[650+(i*150),270+(i2*30),120,25],2)
                        else: #Upgrade exists
                            spl = self.__LINK["cli"].SYNC["D"+str(NumLinks[i3])]["U"+str(i2)].split(",")
                            if spl[1]=="0": #Normal
                                col = (255*mult,255*mult,255*mult)
                            elif spl[1]=="1": #Damaged
                                col = (255*mult,255*mult,0)
                            elif spl[1]=="2": #Dead
                                col = (255*mult,0,0)
                            else: #Unknown
                                col = (255*mult,0,255*mult)
                            if self.__sels[-1]==2 and self.__sels[1]==i3 and self.__sels[2]==i2 and self.__sels[0]==2:
                                pygame.draw.rect(surf,(255*smult,0,255*smult),[650+(i*150),270+(i2*30),120,25],3)
                            else:
                                pygame.draw.rect(surf,(255*mult,255*mult,255*mult),[650+(i*150),270+(i2*30),120,25],2)
                            surf.blit(self.__LINK["font24"].render(spl[0],16,col),[655+(i*150),270+(i2*30)])
                else:
                    for i2,b in enumerate(a.settings["upgrades"]):
                        if b[0]=="":
                            if self.__sels[-1]==2 and self.__sels[1]==i3 and self.__sels[2]==i2 and self.__sels[0]==2:
                                pygame.draw.rect(surf,(255*smult,0,255*smult),[650+(i*150),270+(i2*30),120,25],3)
                            else:
                                pygame.draw.rect(surf,(100*mult,100*mult,100*mult),[650+(i*150),270+(i2*30),120,25],2)
                        else:
                            if b[1]==0: #Normal
                                col = (255*mult,255*mult,255*mult)
                            elif b[1]==1: #Damaged
                                col = (255*mult,255*mult,0)
                            elif b[1]==2: #Dead
                                col = (255*mult,0,0)
                            else: #Unkown
                                col = (255*mult,0,255*mult)
                            if self.__sels[-1]==2 and self.__sels[1]==i3 and self.__sels[2]==i2 and self.__sels[0]==2:
                                pygame.draw.rect(surf,(255*smult,0,255*smult),[650+(i*150),270+(i2*30),120,25],3)
                            else:
                                pygame.draw.rect(surf,(255*mult,255*mult,255*mult),[650+(i*150),270+(i2*30),120,25],2)
                            surf.blit(self.__LINK["font24"].render(b[0],16,col),[655+(i*150),270+(i2*30)])
        if scroll!=0: #There are drone slots behind, render arrow to show this.
            pygame.draw.polygon(surf,(255*mult,255*mult,255*mult),[(655,160),(655,380),(640,270)])
        x = 640
        y = 410
        scroll = 0 #Scroll
        if self.__sels[2]>int((sx-655)/110)*(int((sy-425)/30))/2: #Cursor is going off screen, scroll towards
            scroll = int((sy-425)/30)*(int(self.__sels[2]/int((sy-425)/30))-(int((sx-655)/110)/2))
        MX = None
        Nlink = None
        if self.__LINK["multi"]==1: #Running as a client
            MX,Nlink = self.__getInventInfo()
        else:
            MX = len(self.__LINK["shipData"]["invent"])
        for i in range(int(scroll),self.__LINK["shipData"]["maxInvent"]): #Render all upgrades past the bottom scroll point
            if self.__sels[0]==2 and self.__sels[-1]==3 and i==self.__sels[2]: #Box is selected
                pygame.draw.rect(surf,(255*smult,0,255*smult),[x,y,100,25],3)
            else: #Render normaly
                pygame.draw.rect(surf,(100*mult,100*mult,100*mult),[x,y,100,25],2)
            if i<MX: #Upgrade exists, render text
                upg = None
                if self.__LINK["multi"]==1: #Running as a client
                    if i in Nlink:
                        upg = [self.__LINK["cli"].SYNC["U"+str(Nlink[i])]["N"],self.__LINK["cli"].SYNC["U"+str(Nlink[i])]["D"]]
                    else:
                        for i2 in range(i,self.__LINK["shipData"]["maxInvent"]):
                            if i2 in Nlink:
                                upg = [self.__LINK["cli"].SYNC["U"+str(Nlink[i2])]["N"],self.__LINK["cli"].SYNC["U"+str(Nlink[i2])]["D"]]
                                break
                        else:
                            upg = ["Loading...",2]
                else: #Game is running in single player
                    upg = self.__LINK["shipData"]["invent"][i]
                col = (255*mult,255*mult,255*mult)
                if upg[1]==1: #Upgrade is damaged
                    col = (255*mult,255*mult,0)
                elif upg[1]==2: #Upgrade has failed
                    col = (255*mul5,0,0)
                surf.blit(self.__LINK["font16"].render(upg[0],16,col),[x+5,y+5])
            y+=30 #Render next box below
            if y+25>sy-15: #Hit the bottom
                y = 410 #Reset box Y to the top of the screen
                x += 110 #Go to next column
                if x+110>sx: #Hit the end of the screen, render arrow and exit for loop
                    pygame.draw.polygon(surf,(255*mult,255*mult,255*mult),[(sx-30,420),(sx-30,sy-15),(sx-15,(420+sy-15)/2)])
                    break
        if scroll!=0: #There are upgrade slots behind, render arrow to show this.
            pygame.draw.polygon(surf,(255*mult,255*mult,255*mult),[(655,420),(655,sy-15),(640,(420+sy-15)/2)])
    def __renderShipUpgrades(self,surf,active=False): #Render ship upgrades menu
        if active: #Tab is active
            mult = 1
        else:
            mult = 0.2
        smult = (abs(math.cos(time.time()*3))/2)+0.5 #Box flashing
        sx,sy = surf.get_size()
        if self.__LINK["hints"] and active:
            if self.__LINK["controller"] is None:
                surf.blit(self.__LINK["font16"].render("Press F to fix selected upgrade",16,(0,255*smult,255*smult)),[180,70])
                surf.blit(self.__LINK["font16"].render("Press D to dismantle selected upgrade",16,(0,255*smult,255*smult)),[180,80])
                surf.blit(self.__LINK["font16"].render("Press Return to move selected upgrade to and from reserve area",16,(0,255*smult,255*smult)),[180,90])
            else:
                F = self.__LINK["controller"].keyName["scem"]
                D = self.__LINK["controller"].keyName["back"]
                A = self.__LINK["controller"].keyName["select"]
                surf.blit(self.__LINK["font16"].render("Press "+F+" to fix selected upgrade",16,(0,255*smult,255*smult)),[180,70])
                surf.blit(self.__LINK["font16"].render("Press "+D+" to dismantle selected upgrade",16,(0,255*smult,255*smult)),[180,80])
                surf.blit(self.__LINK["font16"].render("Press "+A+" to move selected upgrade to and from reserve area",16,(0,255*smult,255*smult)),[180,90])
        pygame.draw.rect(surf,(0,255*mult,0),[10,140,300,sy-150],5)
        surf.blit(self.__LINK["font42"].render("SHIP UPGRADES",16,(255*mult,255*mult,255*mult)),[35,150])
        pygame.draw.line(surf,(0,255*mult,0),[10,190],[310,190],5)
        MX = None
        Nlink = None
        MX2 = None
        if self.__LINK["multi"]==1:
            MX,MX2,Nlink = self.__getShipInfo()
        else:
            MX = len(self.__LINK["shipData"]["shipUpgs"])
            MX2 = len(self.__LINK["shipData"]["reserveUpgs"])
        for i in range(self.__LINK["shipData"]["maxShipUpgs"]): #Render ship upgrades
            tex = ""
            tcol = (255*mult,255*mult,255*mult)
            if i>=MX: #Upgrade slot is empty
                col = (100*mult,100*mult,100*mult)
            else: #Slot has an upgrade in it
                col = (0,255*mult,0)
                UPG = None
                if self.__LINK["multi"]==1: #Game is running as a client
                    UPG = [self.__LINK["cli"].SYNC["G"+str(Nlink[i])]["N"],self.__LINK["cli"].SYNC["G"+str(Nlink[i])]["D"]]
                else:
                    UPG = self.__LINK["shipData"]["shipUpgs"][i]
                tex = UPG[0]
                if UPG[1]==1:
                    tcol = (255*mult,255*mult,0)
                elif UPG[1]==2:
                    tcol = (255*mult,0,0)
            if i==self.__sels[1] and self.__sels[0]==0 and self.__sels[-1]==1: #Slot is selected
                col = (255*smult,0,255*smult)
            pygame.draw.rect(surf,col,[20,200+(i*60),280,50],2)
            surf.blit(self.__LINK["font42"].render(str(i+1)+". "+tex,16,tcol),[28,208+(i*60)])
        add = (self.__LINK["shipData"]["maxShipUpgs"]*60)+60 #Adding length from the amount of ship upgrades
        surf.blit(self.__LINK["font42"].render("RESERVE",16,(255*mult,255*mult,255*mult)),[35,150+add])
        pygame.draw.line(surf,(0,255*mult,0),[10,190+add],[310,190+add],5)
        scroll = 0 #Amount to scroll past in reserve upgrades
        if (self.__LINK["shipData"]["reserveMax"]*60)+200+add+50>sy-20 and self.__sels[0]==0: #Too many reserve slots to fit into screen, go into scroll mode
            if ((self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"])*60)+200+add+50>sy-20-((sy-(200+add))/2): #Scroll downwards
                scroll = int(((((self.__sels[1]-self.__LINK["shipData"]["maxShipUpgs"])*60)+200+add+50)-(sy-20-((sy-(200+add))/2)))/60)
        if scroll!=0: #There are reserved upgrade slots above, render arrow to show this.
            pygame.draw.polygon(surf,(255*mult,255*mult,255*mult),[(60,200+add+10),(250,200+add+10),(155,200+add-5)])
        for i in range(scroll,self.__LINK["shipData"]["reserveMax"]): #Render reserve upgrade slots
            tex = ""
            tcol = (255*mult,255*mult,255*mult)
            if i>=MX2: #Upgrade slot is empty
                col = (100*mult,100*mult,100*mult)
            else: #Upgrade slot contains an upgrade
                col = (0,255*mult,0)
                UPG = None
                if self.__LINK["multi"]==1: #Game is running as a client
                    UPG = [self.__LINK["cli"].SYNC["G"+str(Nlink[i+self.__LINK["shipData"]["maxShipUpgs"]])]["N"],self.__LINK["cli"].SYNC["G"+str(Nlink[i+self.__LINK["shipData"]["maxShipUpgs"]])]["D"]]
                else:
                    UPG = self.__LINK["shipData"]["reserveUpgs"][i]
                tex = UPG[0]
                if UPG[1]==1:
                    tcol = (255*mult,255*mult,0)
                elif UPG[1]==2:
                    tcol = (255*mult,0,0)
            if i+self.__LINK["shipData"]["maxShipUpgs"]==self.__sels[1] and self.__sels[0]==0 and self.__sels[-1]==1: #Upgrade slot is selected
                col = (255*smult,0,255*smult)
            if 200+((i-scroll)*60)+add+50>sy-20: #Slot is of the screen, dont render and instead draw an arrow to signify theres upgrades below.
                pygame.draw.polygon(surf,(255*mult,255*mult,255*mult),[(60,sy-28),(250,sy-28),(155,sy-15)])
                break
            pygame.draw.rect(surf,col,[20,200+((i-scroll)*60)+add,280,50],2)
            surf.blit(self.__LINK["font42"].render(str(i+1)+". "+tex,16,tcol),[28,208+((i-scroll)*60)+add])
        if self.__sels[-1]==0 and active: #Window is being selected
            pygame.draw.rect(surf,(255*smult,0,255*smult),[10,140,300,sy-150],5)
            pygame.draw.line(surf,(255*smult,0,255*smult),[10,190],[310,190],5)
            pygame.draw.line(surf,(255*smult,0,255*smult),[10,190+add],[310,190+add],5)
    def __renderShips(self,surf): #Render screen
        sx,sy = surf.get_size()
        if self.__displayInfo[0]: #Display info
            surf.blit(self.__displayInfo[1],(self.__displayInfo[2],0))
            #Title
            fren = self.__LINK["font42"].render(self.__displayInfo[4],16,(0,255,0))
            sx,sy = fren.get_size()
            pygame.draw.rect(surf,(0,0,0),[int(self.__displayInfo[3][0]/2)-int(sx/2)-5,int(self.__displayInfo[3][1]/2)-5,sx+10,sy+10])
            pygame.draw.rect(surf,(0,255,0),[int(self.__displayInfo[3][0]/2)-int(sx/2)-5,int(self.__displayInfo[3][1]/2)-5,sx+10,sy+10],2)
            surf.blit(fren,(int(self.__displayInfo[3][0]/2)-int(sx/2),int(self.__displayInfo[3][1]/2)))
            #'Press return to continue' sign at the bottom of the screen
            fren = self.__LINK["font42"].render("Press return to continue",16,(255,255,0))
            sx,sy = fren.get_size()
            pygame.draw.rect(surf,(0,0,0),[int(self.__displayInfo[3][0]/2)-int(sx/2)-5,int(self.__displayInfo[3][1]*0.8)-5,sx+10,sy+10])
            pygame.draw.rect(surf,(0,255,0),[int(self.__displayInfo[3][0]/2)-int(sx/2)-5,int(self.__displayInfo[3][1]*0.8)-5,sx+10,sy+10],2)
            surf.blit(fren,(int(self.__displayInfo[3][0]/2)-int(sx/2),int(self.__displayInfo[3][1]*0.8)))
            for i,a in enumerate(self.__extrInfo):
                surf.blit(self.__LINK["font24"].render(a[0],16,a[1]),[self.__displayInfo[3][0]/8,(self.__displayInfo[3][1]/8)+(i*30)])
            return 0
        #Upper bar
        pygame.draw.rect(surf,(0,255,0),[10,10,sx-20,120],2)
        pygame.draw.line(surf,(0,255,0),[sx-310,10],[sx-310,130],2)
        pygame.draw.line(surf,(0,255,0),[sx-200,10],[sx-200,130],2)
        surf.blit(self.__LINK["font42"].render("SHIPS",16,(255,255,0)),(sx-300,30))
        surf.blit(self.__LINK["font42"].render("INVENTORY",16,(255,255,0)),(sx-190,30))
        surf.blit(self.__LINK["font64"].render(self.__shipName,16,(255,255,255)),(20,15))
        pygame.draw.polygon(surf,(0,255,0),[ (sx-300,110), (sx-210,110), (sx-255,80) ])
        pygame.draw.polygon(surf,(100,100,100),[ (sx-190,110), (sx-20,110), (sx-105,80) ])
        surf.blit(self.__LINK["font42"].render("DRONES: "+str(len(self.__LINK["drones"]))+"/"+str(self.__maxDrones),16,(0,255,255)),(sx-550,20))
        surf.blit(self.__LINK["font42"].render("UPGRADES: "+str(self.__upgrades)+"/"+str(self.__maxUpgrades),16,(0,255,255)),(sx-550,50))
        surf.blit(self.__LINK["font42"].render("MAX SCRAP: "+str(self.__scrapCopasity),16,(0,255,255)),(sx-550,80))
        surf.blit(self.__LINK["font42"].render("FUEL: "+str(self.__fuelLeft),16,(0,0,255)),(20,60))
        surf.blit(self.__LINK["font42"].render("SCRAP: "+str(int(self.__scrapCollected)),16,(0,0,255)),(20,90))
        if self.__LINK["hints"]:
            smult = (abs(math.cos(time.time()*3))/2)+0.5 #Box flashing
            if self.__LINK["controller"] is None:
                surf.blit(self.__LINK["font16"].render("Use left and right arrow keys to select ship",16,(0,255*smult,255*smult)),[20,140])
                surf.blit(self.__LINK["font16"].render("Press return to select ship and open dialog",16,(0,255*smult,255*smult)),[20,150])
                surf.blit(self.__LINK["font16"].render("Use left and right arrow keys to select dialog option",16,(0,255*smult,255*smult)),[20,160])
            else:
                A = self.__LINK["controller"].keyName["select"]
                surf.blit(self.__LINK["font16"].render("Use left and right arrow keys to select ship",16,(0,255*smult,255*smult)),[20,140])
                surf.blit(self.__LINK["font16"].render("Press "+A+" to select ship and open dialog",16,(0,255*smult,255*smult)),[20,150])
                surf.blit(self.__LINK["font16"].render("Use left and right arrow keys to select dialog option",16,(0,255*smult,255*smult)),[20,160])
        #Ship selecting
        pygame.draw.rect(surf,(0,255,255),[(sx/2)-25,sy-60,50,50],2)
        pygame.draw.polygon(surf,(0,255,255),[((sx/2)-20,sy-15),(sx/2,sy-55),((sx/2)+20,sy-15)],2)
        for i,a in enumerate(self.maps):
            bx,by = 20+(i*(sx/len(self.maps))),(sy*0.5)-(math.cos((((i+0.5)/len(self.maps))*math.pi)-(math.pi/2))*sy*0.25)
            if i == self.__sel: #Ship is selected
                if self.__LINK["shipData"]["fuel"]<a[5]:
                    pygame.draw.rect(surf,(255,0,0),[bx,by,120,120],4) #Draw its box red
                else:
                    pygame.draw.rect(surf,(255,255,0),[bx,by,120,120],4) #Draw its box yellow
                ang = math.atan2((sx/2)-(bx+60),(sy-60)-(by+60))+math.pi #Get angle towards ship from the bottom of the screen
                pygame.draw.line(surf,(0,255,0),[sx/2,sy-60],[bx+60-(math.sin(ang)*120),by+60-(math.cos(ang)*120)],12) #Draw a line from the bottom to the ship
                pygame.draw.circle(surf,(0,255,0),[int(bx+60),int(by+60)],120,12) #Draw a circle around the ship
            elif self.__LINK["shipData"]["fuel"]<a[5]:
                pygame.draw.rect(surf,(255,0,0),[bx,by,120,120],2)
            else: #Draw ships rectangle normaly
                pygame.draw.rect(surf,(0,255,0),[bx,by,120,120],2)
            pygame.draw.polygon(surf,(0,255,0),[(bx+60,by),(bx+50,by+60),(bx,by+120),(bx+60,by+70),(bx+120,by+120),(bx+70,by+60)])
            surf.blit(self.__LINK["font24"].render(a[3],16,(255,255,255)),(bx+10,by+130))
            surf.blit(self.__LINK["font24"].render("SCRAP CAPACITY: "+str(a[1]),16,(255,255,255)),(bx+10,by+150))
            surf.blit(self.__LINK["font24"].render("THREAT TYPES: "+str(a[4]),16,(255,255,255)),(bx+10,by+170))
            surf.blit(self.__LINK["font24"].render("FUEL: "+str(a[5]),16,(255,255,255)),(bx+10,by+190))
            surf.blit(self.__LINK["font24"].render("AGE: "+a[2],16,(255,255,255)),(bx+10,by+210))

            

        if self.__loading[0]: #Loading screen
            surf.blit(self.__loading[1],(self.__loading[2],0))
            pygame.draw.rect(surf,(0,0,0),[50,int(self.__loading[5][1]*0.8),self.__loading[5][0]-100,40],4)
            pygame.draw.rect(surf,(0,0,0),[50,int(self.__loading[5][1]*0.8),self.__loading[5][0]-100,40])
            pygame.draw.rect(surf,(255,255,0),[49,int(self.__loading[5][1]*0.8)-1,self.__loading[5][0]-99,41],2)
            pygame.draw.rect(surf,(0,255,0),[50,int(self.__loading[5][1]*0.8),(self.__loading[5][0]-100)*self.__loading[3],40])
            fren = self.__LINK["font42"].render(self.__loading[4],16,(255,255,255))
            sx,sy = fren.get_size()
            surf.blit(fren,(int(self.__loading[5][0]/2)-int(sx/2),int(self.__loading[5][1]*0.8)+50))
