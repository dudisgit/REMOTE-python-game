import upgrades.base as base

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "lure" #Name of the upgrade
        self.caller = ["lure"] #Commands this upgade takes
        self.displayName = "Lure 4/4" #Name of the upgrade (displayed)
        self.damage = 0 #Damage to the upgrade.
        self.lures = 4 #Amount of lures left
        if LINK["multi"]==2 and ID!=-1: #Is server
            LINK["serv"].SYNC["u"+str(ID)] = {}
    def commandAllowed(self,com):
        Droom = self.drone.findPosition()
        if Droom==-1: #Outside map
            return False
        elif type(Droom)!=self.getEnt("room"): #Not in a room
            return "Drone is not inside a room"
        elif self.lures<=0: #Ran out of lures
            return "No lures left"
        else:
            return True
    def upgradeDelete(self):
        self.LINK["serv"].SYNC.pop("u"+str(self.ID))
    def clientLoop(self,lag):
        self.lures = self.LINK["cli"].SYNC["u"+str(self.ID)]["N"]
        self.displayName = "Lure "+str(self.lures)+"/4"
    def saveData(self):
        return [self.lures+0]
    def openData(self,lis):
        self.lures = lis[0]
        self.displayName = "Lure "+str(self.lures)+"/4"
    def loop(self,lag):
        if self.LINK["multi"] == 2: #Is server
            self.LINK["serv"].SYNC["u"+str(self.ID)]["N"] = self.lures
        self.displayName = "Lure "+str(self.lures)+"/4"
    def doCommand(self,text,usrObj=None):
        self.used = True
        self.LINK["create"]("lure",self.drone.pos) #Spawn a lure entity
        self.lures-=1 #Decrement lure count