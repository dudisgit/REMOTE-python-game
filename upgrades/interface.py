import upgrades.base as base
import math

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "interface"
        self.caller = ["interface","scan","defence"]
        self.displayName = "Interface" #Name of the upgrade (displayed)
        self.damage = 0 #Damage to the upgrade.
        self.__inUse = False #Is the upgrade in use?
        self.__connectedInterface = None #The interface this upgrade is attached to
        self.hitFunction = self.InterfaceHit
    def commandAllowed(self,com):
        spl = com.split(" ")
        if (spl[0]=="scan" or spl[0]=="defence") and self.__connectedInterface is None: #Requested to do an interface command but it this upgrade is not connected
            return "Upgrade not connected to an interface"
        elif not self.__connectedInterface is None: #An interface is connected to this upgrade
            if com=="scan" and not self.__connectedInterface.settings["scan"]: #Scan the ship
                return "Interface cannot scan"
            if com=="defence" and len(self.__connectedInterface.turrets)==0:
                return "Interface not connected to any defences"
            return True
        else: #No interface attached, find one in this room
            Droom = self.drone.findPosition()
            if Droom==-1: #Outside map
                return False
            elif type(Droom)!=self.getEnt("room"): #Not inside a room
                return "Drone not inside a room"
            else: #Room is valid
                Ents = Droom.EntitiesInside() #Get all entities inside the room
                InterfaceObject = self.getEnt("interface") #Interface reference object
                err = "No interface found inside room"
                for a in Ents: #Go through all entities inside the room
                    if type(a)==InterfaceObject: #Entity is an interface
                        if a.powered: #Is the interface powered
                            if a.alive:
                                return True
                            else:
                                err = "Interface has been destroyed"
                        else:
                            err = "Interface not powered"
                return err
    def InterfaceHit(self,Inter): #Interfcae was hit, connecting...
        if Inter.powered: #Interface is powered still
            self.__connectedInterface = Inter
            self.used = True
            self.LINK["outputCommand"]("Interface has the following commands:",(0,255,0))
            if Inter.settings["scan"]:
                self.LINK["outputCommand"]("  scan - Scan a room",(0,255,0))
            if len(self.__connectedInterface.turrets)!=0:
                self.LINK["outputCommand"]("  defence - turn ship turrets on/off",(0,255,0))
            if not Inter.settings["scan"] and len(self.__connectedInterface.turrets)==0:
                self.LINK["outputCommand"]("  <None found>",(0,255,0))
    def loop(self,lag): #Event loop on this upgrade
        super().loop(lag)
        if not self.__connectedInterface is None: #Upgrade is currently in use and connected to an interface
            dist = math.sqrt( ((self.drone.pos[0]+(self.drone.size[0]/2)-(self.__connectedInterface.pos[0]+(self.__connectedInterface.size[0]/2)))**2) +
                            ((self.drone.pos[1]+(self.drone.size[1]/2)-(self.__connectedInterface.pos[1]+(self.__connectedInterface.size[1]/2)) )**2) )
            if dist>45 or not self.__connectedInterface.powered: #Check distance to interface and disconnect if too far away
                self.__connectedInterface = None
    def doCommand(self,com,usrObj=None): #Runs a command on this upgrade (only if sucsessful)
        spl = com.split(" ")
        if spl[0]=="scan": #Scan all rooms
            self.__connectedInterface.scanShip()
        elif spl[0]=="defence": #Turn defences on/off
            self.__connectedInterface.toggleDefence()
        else: #Connect to the closest interface
            Droom = self.drone.findPosition() #Get the drones room
            Ents = Droom.EntitiesInside() #Get all the entities inside the room the drone is in
            InterfaceObject = self.getEnt("interface") #Interface reference object
            Closest = [-1,None]
            for a in Ents: #Go through all entities inside the room
                if type(a)==InterfaceObject: #Found a interface, heading towards it
                    dist = math.sqrt( ((self.drone.pos[0]+(self.drone.size[0]/2)-(a.pos[0]+(a.size[0]/2)))**2) + 
                        ((self.drone.pos[1]+(self.drone.size[1]/2)-(a.pos[1]+(a.size[1]/2)) )**2) ) #Find distance
                    if Closest[0]==-1 or dist<Closest[0]: #Has distance not been mesured before or distance is less and prevously known
                        Closest[0] = dist+0
                        Closest[1] = a
            self.headTowards(Closest[1]) #Head towards the closest interface
            return "Navigating drone "+str(self.drone.number)+" to interface"
