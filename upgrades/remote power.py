import upgrades.base as base

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "remote power"
        self.caller = ["remote"]
        self.displayName = "Remote power" #Name of the upgrade (displayed)
        self.droneUpgrade = False
        self.__connected = None
        self.__used = False #Has the upgrade been used before
        self.damage = 0 #Damage to the upgrade.
    def commandAllowed(self,com): #Is the command allowed
        spl = com.split(" ")
        if len(spl)>1: #Number or paramiters is correct
            if spl[1] in self.LINK["IDref"]: #Is a valid entity
                E = self.LINK["IDref"][spl[1]]
                if type(E)==self.getEnt("room"): #Is the entity a room
                    if not E.discovered2:
                        return "No such room"
                    if not self.__connected is None: #Is this upgrade allredey powering a generator
                        if self.__connected == E: #Is the room specified the same as the one allredey connected
                            return True
                        else: #Different, report problem
                            return self.__connected.reference()+" is still connected"
                    Ents = E.EntitiesInside() #Get all entities inside the room
                    GeneratorObject = self.getEnt("generator") #Used as a reference to a generator object
                    Err = "No generator inside room"
                    for a in Ents: #Go through every entity inside the room
                        if type(a)==GeneratorObject: #Entity is a generator
                            if a.alive: #Entity is alive
                                if a.active: #Generator is allredey being powered by something
                                    Err = "Generator already powered"
                                else:
                                    return True
                            else:
                                Err = "Generator is destroyed"
                    return Err
                else:
                    return "Expected a ROOM"
            else:
                return "No such room"
        return "Incorrect parameters"
    def doCommand(self,com,usrObj=None): #Execute the upgrade (as in run)
        self.__used = True #Upgrade has been used from now on
        self.used = True
        if self.__connected is None: #Is not connected to a power outlet
            spl = com.split(" ")
            E = self.LINK["IDref"][spl[1]] #Room entity
            Ents = E.EntitiesInside() #Get all entiteis inside the room
            self.__connected = E
            GeneratorObject = self.getEnt("generator") #Reference object to a generator
            for a in Ents: #Loop through all the entities of the room
                if type(a)==GeneratorObject and a.alive: #Entity is a generator and is alive
                    a.active = True
                    break
            return "Powering generator in "+E.reference()
        else: #Allredey powering a generator
            Ents = self.__connected.EntitiesInside() #Get all the entities in the room
            GeneratorObject = self.getEnt("generator") #Reference object to a generator
            for a in Ents: #Loop through all entities inside the room
                if type(a)==GeneratorObject: #Entity is a generator and is alive
                    a.active = False #Turn the generator off
                    self.__connected = None #Disconnect the remote upgrade from this one
                    break
            return "Generator de-activated"
