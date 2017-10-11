import upgrades.base as base
import random,time

SPREAD_PROBABILITY = 30 #Percentage chance that the scan will spread to other rooms
UPDATE_RATE = 10 #Scan rooms 10 times a second for NPC's

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID #ID of this upgrade
        self.name = "motion" #Name of the upgrade
        self.displayName = "Motion 50/50" #Name of the upgrade (displayed)
        self.damage = 0 #Damage to the upgrade.
        self.caller = ["motion"] #Commands that this upgrade will accept
        self.scansLeft = 50 #50 Scans left
        self.__scanAgain = time.time()
        self.__inUse = False #Is the motion upgrade in use?
        self.__scanRooms = [] #Rooms to scan for threats
        self.__scanChange = [] #Detects changes in the current scan
        self.__savePos = [0,0] #Saved drone position
        if LINK["multi"]==2 and ID!=-1: #Is server
            LINK["serv"].SYNC["u"+str(ID)] = {}
    def commandAllowed(self,com): #Return true if this upgrade is allowed to run
        Droom = self.drone.findPosition() #Get the position of this upgrades drone
        if Droom==-1: #Outside map
            return False
        elif type(Droom)!=self.getEnt("room"): #Not inside a room
            return "Cannot scan when not inside a room"
        elif self.__inUse: #Allredey being used
            return "Allredey scanning rooms"
        elif self.scansLeft<=0: #Ran out of scans to scan a room
            return "Ran out of scans"
        return True #Sucsessful
    def upgradeDelete(self):
        self.LINK["serv"].SYNC.pop("u"+str(self.ID))
    def clientLoop(self,lag): #Loop to call when a client runs an upgrade
        self.scansLeft = self.LINK["cli"].SYNC["u"+str(self.ID)]["N"]
        self.displayName = "Motion "+str(self.scansLeft)+"/50"
    def loop(self,lag): #Constant event loop
        if self.LINK["multi"] == 2: #Is server
            self.LINK["serv"].SYNC["u"+str(self.ID)]["N"] = self.scansLeft
        if self.__inUse: #Is this upgrade currently being used
            if time.time()>self.__scanAgain: #Scan all rooms for NPCs
                for i,a in enumerate(self.__scanRooms): #Loop through all connected rooms
                    if a.settings["scanable"]: #Check if the room is scannable
                        Ents = a.EntitiesInside() #Get all the entities inside the room
                        for b in Ents: #Loop through all the entities inside the room
                            if b.isNPC and b.alive: #Check if the entity is an NPC
                                a.SCAN = 3 #Bad
                                break
                        else:
                            a.SCAN = 1 #Safe
                    else:
                        a.SCAN = 2 #Error scanning
                    if self.__scanChange[i] == -1: #First scan
                        self.__scanChange[i] = a.SCAN+0
                    elif self.__scanChange[i] != a.SCAN: #Scan has changed state
                        self.__scanChange[i] = a.SCAN+0
                        print("CHANGE")
                        if a.SCAN==3: #Bad
                            self.LINK["outputCommand"]("Motion triggered in R"+str(a.number),(255,0,0))
                        elif a.SCAN==1: #Safe
                            self.LINK["outputCommand"]("Motion un-triggered in R"+str(a.number),(255,255,0))
                self.__scanAgain = time.time()+(1/UPDATE_RATE)
            if [int(self.drone.pos[0]),int(self.drone.pos[1])]!=self.__savePos: #Has the drone moved from when the upgrade was first turned on?
                self.__inUse = False
                for a in self.__scanRooms: #Go through every room and disable their scan lines
                    a.SCAN = 0
                self.__scanRooms = []
    def __getRooms(self,rm): #Loops through a room and adds all its naybors to a list (recursive)
        self.__scanRooms.append(rm)
        for a in rm.doors: #Loop through all the doors of the room
            if not a.room1 is None and not a.room2 is None: #Is the door valid?
                if not a.room1 in self.__scanRooms: #Find a door that hasn't been checked allredey
                    if random.randint(0,100)<SPREAD_PROBABILITY: #Rare chance of spreading, increasing the size of the scan
                        self.__getRooms(a.room1)
                    else:
                        self.__scanRooms.append(a.room1)
                elif not a.room2 in self.__scanRooms:
                    if random.randint(0,100)<SPREAD_PROBABILITY: #Rare chance of spreading, increasing the size of the scan
                        self.__getRooms(a.room2)
                    else:
                        self.__scanRooms.append(a.room2)
    def doCommand(self,com,usrObj=None):
        Droom = self.drone.findPosition() #Get the position of the drone
        self.__scanRooms = []
        self.__getRooms(Droom) #Get all the rooms this upgrade should scan
        self.__scanChange = [-1]*len(self.__scanRooms)
        self.__inUse = True #Upgrade is in use
        self.__savePos = [int(self.drone.pos[0])+0,int(self.drone.pos[1])+0] #Used to disable the upgrade if the drone is moved
        self.scansLeft -= 1 #Decrease the amount of scans left
        self.displayName = "Motion "+str(self.scansLeft)+"/50"
        return "Scanning "+str(len(self.__scanRooms))+" rooms"
