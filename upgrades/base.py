#This is the base class, it is used by all other upgrades
#this should NOT be used as an upgrade but a class for other upgrades to inherit.

import math

ACTIVATION_DIST = 40 #Distance from an object in order to be attached to it (e.g. generator or interface)

def nothing(*args): #Does nothing
    pass

class Main:
    def __init__(self,LINK,ID=-1):
        LINK["errorDisplay"]("Base upgrade was imported, please do not import this as a upgrade")
        self.init(LINK)
        self.ID = ID
    def commandAllowed(self,com): #Returns true if this command is allowed in the upgrade
        spl = com.split(" ")
        return spl[0] in self.caller
    def upgradeDelete(self): #Called when this upgrade is deleted in multiplayer mode
        pass
    def doCommand(self,com,useObj=None): #Runs a command on this upgrade (only if sucsessful)
        pass
    def moved(self,newDrone): #Upgrade was swapped for anouther in the game
        pass
    def clientCall(self,*args): #Upgrade was called by a server to run client-side
        pass
    def getEnt(self,name): #Returns the entity with the name
        if name in self.LINK["ents"]: #Does the entity exist?
            return self.LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.LINK["errorDisplay"]("Tried to get entity but doesen't exist '"+name+"'")
        return self.LINK["null"]
    def headTowards(self,Ent,hitDist=ACTIVATION_DIST): #Makes the drone head towards an object, this can be canceled when the drone navigation is taken over
        self.drone.stopNavigation(0) #Stop the drone from moving other paths
        self.__activationDist = hitDist+0
        self.__targetEnt = Ent
        self.drone.paths.append([2,[ [Ent.pos[0]+(Ent.size[0]/2), Ent.pos[1]+(Ent.size[1]/2) , Ent]]])
    def clientLoop(self,lag): #A clientside loop (if multiplayer is enabled)
        pass
    def loop(self,lag): #Called continuesly to loop through upgrades
        if not self.__targetEnt is None: #Upgrade is directing the drone to an entity
            hasPath = False
            for a in self.drone.paths: #Check if the path towards the entity still exists
                if a[0]==0 and a[1][0][2]==self.__targetEnt:
                    hasPath = True
                    break
            dist = math.sqrt( ((self.drone.pos[0]+(self.drone.size[0]/2)-(self.__targetEnt.pos[0]+(self.__targetEnt.size[0]/2)))**2) +
                            ((self.drone.pos[1]+(self.drone.size[1]/2)-(self.__targetEnt.pos[1]+(self.__targetEnt.size[1]/2)) )**2) )
            if not hasPath or dist<=self.__activationDist: #Path has finished or been canceled
                if dist<=self.__activationDist: #Has reached the generator without being canceled
                    self.drone.stopNavigation() #Stop the drone from moving other paths
                    self.__activationDist = -1
                    self.hitFunction(self.__targetEnt)
                    if self.__activationDist==-1:
                        self.__targetEnt = None
    def init(self,LINK): #Init for the upgrade
        self.LINK = LINK
        self.drone = None #Drone this upgrade is linked to
        self.hitFunction = nothing #Function to call once the object this drone is heading towards has been hit
        self.__targetEnt = None #Entity the drone is heading towards
        self.used = False #Has the upgrade been used yet?
        self.__activationDist = ACTIVATION_DIST+0
        self.name = "NO NAME" #Name of the upgrade
        self.displayName = "NO NAME"
        self.damage = 0 #Damage to the upgrade
        self.droneUpgrade = True #Is a drone upgrade
        self.caller = [] #List to refeerence commands that can be called to this upgrade
