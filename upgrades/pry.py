import upgrades.base as base
import math

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "pry"
        self.caller = ["pry"]
        self.displayName = "Pry" #Name of the upgrade (displayed)
        self.damage = 0 #Damage to the upgrade.
        self.hitFunction = self.hitDoor
    def commandAllowed(self,com): #Returns true if this command is allowed to run on the upgrade
        Droom = self.drone.findPosition() #Get the drones position
        if Droom==-1: #Drone is outside map
            return False
        elif type(Droom)!=self.getEnt("room"): #Drone is not inside a room
            return "Drone must be inside a room"
        else: #Drone is inside room
            for a in Droom.doors: #Go through every door of the room
                if not a.settings["open"] and type(a)==self.getEnt("door") and (not a.powered or not a.alive): #Door is open and is not an airlock
                    return True
            return "No doors that arn't open/powered"
    def hitDoor(self,door): #Drone has reached door
        door.pry() #Pry open the door
        if door.alive:
            self.LINK["outputCommand"]("Pried open D"+str(door.number),(255,255,0),False)
        else:
            self.LINK["outputCommand"]("Pried open D"+str(door.number)+" but was destroyed during pry",(255,0,0),False)
    def doCommand(self,com,usrObj=None): #Execute pry command
        Droom = self.drone.findPosition() #Get drones position
        self.used = True
        closest = [None,-1] #Closest door
        for a in Droom.doors: #Go through all the doors in the room and find the closest door to the drone
            if type(a)==self.getEnt("door") and not a.settings["open"] and (not a.powered or not a.alive): #Door is not an airlock and is open
                dist = math.sqrt( ((self.drone.pos[0]+(self.drone.size[0]/2)-(a.pos[0]+(a.size[0]/2)))**2) +
                        ((self.drone.pos[1]+(self.drone.size[1]/2)-(a.pos[1]+(a.size[1]/2)) )**2) ) #Distance between the drone and the scrap
                if dist<closest[1] or closest[1]==-1: #Distance is closer than previous or it has never been set
                    closest[0] = a
                    closest[1] = dist+0
        self.headTowards(closest[0],55) #Head towards the door
        return "Navigating drone to D"+str(closest[0].number)