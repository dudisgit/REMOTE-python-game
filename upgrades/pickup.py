import upgrades.base as base
import pygame, time, math

WIDTH = 180
HEIGHT = 110

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "pickup"
        self.displayName = "DONT SPAWN" #Name of the upgrade (displayed)
        self.damage = 0 #Damage to the upgrade.
        self.caller = ["pickup"] #Commands this upgrade accepts
        self.hitFunction = self.hitItem #Function to call when the item has been reached
    def commandAllowed(self,com): #Returns true if this command is allowed in the upgrade
        Droom = self.drone.findPosition() #Find the drones position
        if Droom==-1: #Drone is not in anything
            return False
        elif type(Droom)!=self.getEnt("room"): #Drone is not inside a room
            return "Drone is not inside a room"
        else: #Check if there is anything to pickup in the room
            Ents = Droom.EntitiesInside() #Get all entities insdie the room
            Finding = [self.getEnt("lure")] #What entities are we looking for
            Err = "Nothing to pickup."
            for a in Ents: #Find any drones in the room with this one
                if type(a) in Finding and a.alive: #Matching and alive
                    if self.drone.hasUpgrade(a.SaveFile()[0]): #Our drone has the specific upgrade to pickup this item
                        return True
                    else:
                        Err = "Cannot pick up item, incorrect upgrades"
                elif type(a) in Finding: #Upgrade is not alive
                    Err = "Item has been destroyed"
            return Err
    def hitItem(self,itm): #Has reached item
        if type(itm)==self.getEnt("lure"):
            noAdd = False
            for a in self.drone.upgrades: #Go through all the drones upgrade and find matching upgrade
                if a.name=="lure": #Found lure upgrade
                    if a.lures<4: #Upgrade is not allredey full
                        a.lures += 1
                        break
            else: #Nothing was picked up
                noAdd = True
                self.LINK["outputCommand"]("Couldn't carry any more lures!",(255,255,0))
            if not noAdd: #Lure was added back into the upgrade
                itm.REQUEST_DELETE = True
                self.LINK["outputCommand"]("Picked up lure",(0,255,0))
    def loop(self,lag): #Event loop on this upgrade
        super().loop(lag)
    def doCommand(self,com,usrObj=None): #Runs a command on this upgrade (only if sucsessful)
        Droom = self.drone.findPosition() #Get the room the drone is inside of
        Ents = Droom.EntitiesInside() #Get all the entities in the room
        Finding = [self.getEnt("lure")] #Entities we are looking for
        Closest = [-1,None] #The closest item
        for a in Ents: #Find the closest item to the current drone
            if type(a) in Finding and a.alive: #Entity is an item and is alive
                dist = math.sqrt( ((self.drone.pos[0]+(self.drone.size[0]/2)-(a.pos[0]+(a.size[0]/2)))**2) + 
                    ((self.drone.pos[1]+(self.drone.size[1]/2)-(a.pos[1]+(a.size[1]/2)) )**2) ) #Find distance
                if Closest[0]==-1 or dist<Closest[0]: #Has distance not been mesured before or distance is less and prevously known
                    Closest[0] = dist+0
                    Closest[1] = a
        self.headTowards(Closest[1],35) #Head towards item
