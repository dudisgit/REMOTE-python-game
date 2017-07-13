import upgrades.base as base

class Main(base.Main):
    def __init__(self,LINK):
        self.init(LINK)
        self.name = "Stealth"
        self.damage = 0 #Damage to the upgrade.
