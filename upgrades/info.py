import upgrades.base as base
import pygame, time, math

WIDTH = 180
HEIGHT = 110

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "info"
        self.__print = False
        self.displayName = "DONT SPAWN" #Name of the upgrade (displayed)
        self.damage = 0 #Damage to the upgrade.
        self.caller = ["info"] #Commands this upgrade accepts
    def commandAllowed(self,com): #Returns true if this command is allowed in the upgrade
        Droom = self.drone.findPosition() #Find the drones position
        if Droom==-1: #Drone is not in anything
            return False
        elif type(Droom)!=self.getEnt("room"): #Drone is not inside a room
            return "Drone is not inside a room"
        else: #Check if there is anything to pickup in the room
            return True
    def loop(self,lag):
        if self.__print:
            self.detectAll()
            self.__print = False
    def doCommand(self,com,usrObj=None): #Runs a command on this upgrade (only if sucsessful)
        self.__print = True
    def detectAll(self): #Print everything
        Droom = self.drone.findPosition() #Get the room the drone is inside of
        Ents = Droom.EntitiesInside() #Get all the entities in the room
        Finding = [self.getEnt("ShipUpgrade"),self.getEnt("interface"),self.getEnt("fuel"),self.getEnt("turret")]
        self.LINK["outputCommand"]("Object info in "+Droom.reference()+"...",(0,255,0),False)
        found = 0
        for a in Ents: #Go through all entities in the room
            if type(a) in Finding: #Entity is an item
                found += 1
                if type(a)==self.getEnt("ShipUpgrade"): #Ship upgrade
                    self.LINK["outputCommand"]("  Ship upgrade - "+a.upg_typ,(0,255,0),False)
                elif type(a)==self.getEnt("interface"): #Interface
                    TPS = ""
                    if a.settings["scan"]:
                        TPS+="Scan "
                    if len(a.turrets)!=0:
                        TPS+="Defence "
                    if TPS=="":
                        TPS = "Nothing"
                    self.LINK["outputCommand"]("  Interface - "+TPS,(0,255,0),False)
                elif type(a)==self.getEnt("fuel"): #Fuel port
                    if a.used:
                        self.LINK["outputCommand"]("  Fuel - Used",(0,255,0),False)
                    else:
                        self.LINK["outputCommand"]("  Fuel - Un-used",(0,255,0),False)
                elif type(a)==self.getEnt("turret"): #Defence turret
                    if a.alive:
                        self.LINK["outputCommand"]("  Defence - Alive",(0,255,0),False)
                    else:
                        self.LINK["outputCommand"]("  Defence - Destroyed",(0,255,0),False)
        if found==0: #Nothing of interest
            self.LINK["outputCommand"]("None",(0,255,0),False)
        else:
            self.LINK["outputCommand"](str(found)+" objects",(0,255,0),False)
