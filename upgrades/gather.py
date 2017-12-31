import upgrades.base as base
import math, time, random

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID #ID of the upgrade
        self.name = "gather" #Name of the upgrade
        self.caller = ["gather"] #Command to expect when this upgrade is called
        self.displayName = "Gather" #Name of the upgrade (displayed)
        self.hitFunction = self.scrapHit #Function to call when scrap has been hit
        self.__single = False #Was the upgrade called to gather all scrap?
        self.damage = 0 #Damage to the upgrade.
    def commandAllowed(self,com): #Will return true if the upgrade is allowed
        spl = com.split(" ")
        if len(spl)>1: #Is there a paramiter
            if spl[1]!="all" and spl[1]!="":
                return "Invalid paramiters entered"
        Droom = self.drone.findPosition() #Get the room the drone is in
        if Droom==-1: #Outside map
            return False
        elif type(Droom)!=self.getEnt("room"): #Return an error message if the drones position is not in a room
            return "Not inside a room"
        else: #Inside a room
            Ents = Droom.EntitiesInside() #Get all the entities inside the room
            ScrapObject = self.getEnt("scrap") #Scrap reference object
            FuelObject = self.getEnt("fuel") #Fuel reference object
            err = "No scrap in room"
            for a in Ents: #Loop through all the entities in the room
                if type(a)==ScrapObject or type(a)==FuelObject: #Entity is scrap
                    if type(a)==FuelObject:
                        if a.used:
                            err = "Fuel port allredey used"
                        else:
                            return True
                    else:
                        return True
            return err
    def scrapHit(self,scrap): #Function to call when a scrap as been hit
        if type(scrap)==self.getEnt("fuel"):
            scrap.used = True
            self.drone.pause = time.time()+1.5
            self.LINK["outputCommand"]("Gathering fuel...",(0,255,0),False,self.drone) #Send command message that the upgrade collected scrap
            self.LINK["fuelCollected"] += random.randint(1,5) #Increment scrap amount
        else:
            scrap.REQUEST_DELETE = True #Delete the scrap
            self.LINK["outputCommand"]("Collected scrap",(0,255,0),False) #Send command message that the upgrade collected scrap
            self.LINK["scrapCollected"] += 1 #Increment scrap amount
        if not self.__single: #Collect multiple scrap
            self.__goTowardsClosestScrap([scrap])
    def __goTowardsClosestScrap(self,ignore=[]): #Goes towards the closest scrap in the room
        Droom = self.drone.findPosition() #Get the room the drones in
        if Droom!=-1 and type(Droom)==self.getEnt("room"): #Not outside map and inside an room
            Ents = Droom.EntitiesInside() #Get all the entities inside the room
            ScrapObject = self.getEnt("scrap") #Scrap reference object
            FuelObject = self.getEnt("fuel") #Fuel reference object
            closest = [None,-1] #Closest scrap
            for a in Ents: #Go through all the entities in the room and find the closest scrap to the drone
                if (type(a)==ScrapObject or type(a)==FuelObject) and not a in ignore: #Entity is type scrap and is not in the ignore list
                    dist = math.sqrt( ((self.drone.pos[0]+(self.drone.size[0]/2)-(a.pos[0]+(a.size[0]/2)))**2) +
                            ((self.drone.pos[1]+(self.drone.size[1]/2)-(a.pos[1]+(a.size[1]/2)) )**2) ) #Distance between the drone and the scrap
                    no = False
                    if type(a)==FuelObject: #Object is a fuel port
                        if a.used: #Fuel port allredey used
                            no = True
                    if (dist<closest[1] or closest[1]==-1) and not no: #Distance is closer than previous or it has never been set
                        closest[0] = a
                        closest[1] = dist+0
            if not closest[0] is None: #Found closest scrap, else false
                self.headTowards(closest[0],30)
    def doCommand(self,com,usrObj=None): #Execute the command
        self.used = True #Upgrade has been used before
        spl = com.split(" ")
        if len(spl)>1:
            self.__single = spl[1]!="all"
        else:
            self.__single = True
        self.__goTowardsClosestScrap() #Collect the nearest scrap