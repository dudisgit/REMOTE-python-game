import upgrades.base as base

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "sensor" #Name of the upgrade
        self.caller = ["sensor"] #Commands this upgade takes
        self.displayName = "Sensor 30/30" #Name of the upgrade (displayed)
        self.damage = 0 #Damage to the upgrade.
        self.sensors = 30 #Amount of lures left
        if LINK["multi"]==2 and ID!=-1: #Is server
            LINK["serv"].SYNC["u"+str(ID)] = {}
    def commandAllowed(self,com):
        Droom = self.drone.findPosition()
        if Droom==-1: #Outside map
            return False
        elif type(Droom)!=self.getEnt("room"): #Not in a room
            return "Drone is not inside a room"
        elif self.sensors<=0: #Ran out of sensors
            return "No sensors left"
        else:
            return True
    def upgradeDelete(self):
        self.LINK["serv"].SYNC.pop("u"+str(self.ID))
    def clientLoop(self,lag):
        self.sensors = self.LINK["cli"].SYNC["u"+str(self.ID)]["N"]
        self.displayName = "Sensor "+str(self.sensors)+"/30"
    def saveData(self):
        return [self.sensors]
    def openData(self,lis):
        self.sensors = lis[0]
        self.displayName = "Sensor "+str(self.sensors)+"/30"
    def loop(self,lag):
        if self.LINK["multi"] == 2: #Is server
            if not "u"+str(self.ID) in self.LINK["serv"].SYNC:
                self.LINK["serv"].SYNC["u"+str(self.ID)] = {}
            self.LINK["serv"].SYNC["u"+str(self.ID)]["N"] = self.sensors
        self.displayName = "Sensor "+str(self.sensors)+"/30"
    def doCommand(self,text,usrObj=None):
        self.used = True
        self.LINK["create"]("sensor",self.drone.pos) #Spawn a sensor entity
        self.sensors-=1 #Decrement sensor count
        return "Placed sensor"