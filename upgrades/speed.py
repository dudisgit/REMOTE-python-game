import upgrades.base as base

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "speed"
        self.displayName = "Speed" #Name of the upgrade (displayed)
        self.used = True
        self.__noSet = False
        self.__changeDrone = None
        self.damage = 0 #Damage to the upgrade.
    def moved(self,newD): #Changing drone
        if self.damage!=2:
            self.drone.speed -= 1 #Decrease prevous drone speed
            self.__changeDrone = newD.ID + 0
            newD.speed += 1 #Increase new drone speed
    def loop(self,lag): #Loop ran single player or server side
        if not self.__noSet and not self.drone is None and not self.damage==2: #Drone hasn't been sped up before
            self.drone.speed += 1
            self.__changeDrone = self.drone.ID+0
            self.__noSet = True
    def clientLoop(self,lag): #Loop ran client side
        if self.__changeDrone!=self.drone.ID and not self.damage==2: #Drone attachment has changed, changing speed...
            if not self.__changeDrone is None:
                self.LINK["IDs"][self.__changeDrone].speed -= 1
            self.drone.speed += 1
            self.__changeDrone = self.drone.ID+0