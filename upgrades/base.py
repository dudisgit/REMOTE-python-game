#This is the base class, it is used by all other upgrades to
#this should NOT be used as an upgrade but a thing for other upgrades to inherit.

class Main:
    def __init__(self,LINK):
        LINK["errorDisplay"]("Base upgrade was imported, please do not import this as a upgrade")
        self.init(LINK)
    def init(self,LINK): #Init for the upgrade
        self.LINK = LINK
        self.drone = None #Drone this upgrade is linked to
        self.used = False #Has the upgrade been used yet?
        self.name = "NO NAME" #Name of the upgrade
        self.damage = 0 #Damage to the upgrade
        self.droneUpgrade = True #Is a drone upgrade