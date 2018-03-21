import upgrades.base as base

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "overload"
        self.caller = ["overload"]
        self.displayName = "Overload" #Name of the upgrade (displayed)
        self.droneUpgrade = False
        self.damage = 0 #Damage to the upgrade.
        self.__used = False
    def commandAllowed(self,com):
        spl = com.split(" ")
        if len(spl)>1: #Number or paramiters is correct
            if spl[1] in self.LINK["IDref"]: #Is a valid entity
                E = self.LINK["IDref"][spl[1]]
                if type(E)==self.getEnt("room"): #Is the entity a room
                    return True
                else:
                    return "Expected a ROOM"
            else:
                return "No such room"
        return "Incorrect parameters"
    def doCommand(self,com,usrObj=None):
        self.__used = True
        self.used = True
        E = self.LINK["IDref"][com.split(" ")[1]] #Room entity
        Ents = E.EntitiesInside() #Get all entities inside the room
        KillObjs = [self.getEnt("android"),self.getEnt("interface"),self.getEnt("generator"),self.getEnt("sensor"),self.getEnt("turret"),self.getEnt("drone")]
        for a in Ents: #Loop through all entities in the room
            if type(a) in KillObjs and a.alive: #Entity is electrical and must be destroyed
                a.alive = False
                if type(a)==self.getEnt("interface"):
                    self.LINK["outputCommand"]("Interface in "+a.findPosition().reference()+" was destroyed",(255,0,0),False)
                elif type(a)==self.getEnt("generator"):
                    self.LINK["outputCommand"]("Generator in "+a.findPosition().reference()+" was destroyed",(255,0,0),False)
                elif type(a)==self.getEnt("turret"):
                    self.LINK["outputCommand"]("Defence in "+a.findPosition().reference()+" was destroyed",(255,0,0),False)
                elif type(a)==self.getEnt("sensor"):
                    self.LINK["outputCommand"]("Sensor in "+a.findPosition().reference()+" was destroyed",(255,0,0),False)
                elif type(a)==self.getEnt("drone"):
                    self.LINK["outputCommand"]("Drone "+str(a.number)+" was destroyed",(255,0,0),False)
        return "Overloaded R"+str(E.number)