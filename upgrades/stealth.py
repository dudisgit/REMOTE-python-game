import upgrades.base as base
import time

DECREMENT_RATE = 1.2 #Seconds to wait until decreasing the stealth percentage

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "stealth"
        self.displayName = "Stealth 100%" #Name of the upgrade (displayed)
        self.damage = 0 #Damage to the upgrade.
        self.caller = ["stealth"]
        self.__value = 100 #Stealth percentage
        self.__decrementTime = time.time()+DECREMENT_RATE
        self.__active = False #Is the stealth upgrade active or not
        if LINK["multi"]==2 and ID!=-1: #Is server
            LINK["serv"].SYNC["u"+str(ID)] = {}
    def commandAllowed(self,com): #Returns true if this command is allowed to run on the upgrade
        if self.__value<=0: #No stealth percentage left
            return "Stealth percentage is 0"
        return True
    def moved(self,newDrone): #Upgrade was swapped to anouther drone
        if self.__active: #Upgrade is still active
            self.__active = False
            self.drone.stealth = False
    def upgradeDelete(self):
        self.LINK["serv"].SYNC.pop("u"+str(self.ID))
    def clientLoop(self,lag): #Called only by a client when in multiplayer mode
        self.__value = self.LINK["cli"].SYNC["u"+str(self.ID)]["p"]
        self.__active = self.LINK["cli"].SYNC["u"+str(self.ID)]["A"]
        if self.__active: #Upgrade is active
            self.drone.stealth = True
        else:
            self.drone.stealth = False
        self.displayName = "Stealth "+str(int(self.__value))+"%"
    def loop(self,lag): #Function is called continuesly
        if self.__active: #Upgade is on
            if time.time()>self.__decrementTime: #Decrease stealth percentage
                self.__decrementTime = time.time()+DECREMENT_RATE
                self.__value -= lag
                if self.drone.colision: #Drone has colided with a wall
                    self.__value -= lag*8
            if self.__value<=0: #Stealth percentage has ran out
                self.__value = 0
                self.__active = False
                self.drone.stealth = False
                self.LINK["outputCommand"]("Stealth has ended on drone "+str(self.drone.number),(255,255,0))
        elif self.__value < 100: #Charge stealth percentage back up
            if time.time()>self.__decrementTime: #Incrase stealth percentage
                self.__decrementTime = time.time()+DECREMENT_RATE
                self.__value += lag
            if self.__value>100: #At max
                self.__value = 100
        if self.LINK["multi"] == 2: #Is server
            self.LINK["serv"].SYNC["u"+str(self.ID)]["p"] = int(self.__value)
            self.LINK["serv"].SYNC["u"+str(self.ID)]["A"] = self.__active
        self.displayName = "Stealth "+str(int(self.__value))+"%"
    def doCommand(self,com,usrObj=None): #Execute pry command
        if self.__active: #Upgrade is active, turning off
            self.__active = False
            self.drone.stealth = False
            return "Stealth de-activated"
        else: #Upgrade is de-activated, turning on
            self.__active = True
            self.drone.stealth = True
            return "Stealth activated"