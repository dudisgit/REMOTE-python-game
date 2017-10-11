import upgrades.base as base

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "surveyor"
        self.displayName = "Surveyor" #Name of the upgrade (displayed)
        self.droneUpgrade = False
        self.damage = 0 #Damage to the upgrade.
