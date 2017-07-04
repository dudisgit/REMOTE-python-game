#This file is the base entitie that all other entites inheret to.
import pygame

def nothing(*args): #Does nothing
    pass

class Main(object):
    def __init__(self,x,y,LINK):
        LINK["errorDisplay"]("Base entitie was created but shouldn't be. This class is for inheriting uses only!")
    def init(self,x,y,LINK): #Called to initialize variables
        self.pos = [x,y] #Position of the entity
        self.size = [50,50] #Size of the entity
        self.settings = {} #Settings of the entity, this is a vital part since this is what is saved to the file along with position and size.
        self.linkable = [] #A list containing items describing what entity can link to this one.
        self.REQUEST_DELETE = False #If the entity is requesting to be deleted
        self.LINK = LINK #Cannot make it __LINK because the class it is inhertited by will not be able to access it.
    def getEnt(self,name): #Returns the entity with the name
        if name in self.LINK["ents"]: #Does the entity exist?
            return self.LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.LINK["errorDisplay"]("Tried to create entity but doesen't exist '"+name+"'")
        return self.LINK["null"]
    def insideRoom(self,ents,pos=None,size=None): #Returns the room if this entity is inside one.
        if pos is None:
            pos = self.pos
        if size is None:
            size = self.size
        for a in ents:
            if type(a) == self.getEnt("room"):
                #Checks all 4 corners of the entity to check if it is inside this one
                ins = pos[0] > a.pos[0] and pos[1] >= a.pos[1] and pos[0] < a.pos[0]+a.size[0] and pos[1] < a.pos[1]+a.size[1] #Top left
                ins2 = pos[0]+size[0] > a.pos[0] and pos[1] > a.pos[1] and pos[0]+size[0] < a.pos[0]+a.size[0] and pos[1] < a.pos[1]+a.size[1] #Bottom right
                ins3 = pos[0] > a.pos[0]+a.size[0] and pos[1]+size[1] > a.pos[1] and pos[0] < a.pos[0]+a.size[0] and pos[1]+size[1] < a.pos[1]+a.size[1] #Top right
                ins4 = pos[0]+size[0] > a.pos[0] and pos[1]+size[1] > a.pos[1] and pos[0]+size[0] < a.pos[0]+a.size[0] and pos[1]+size[1] < a.pos[1]+a.size[1] #Bottom left
                if ins or ins2 or ins3 or ins4:
                    return a
        return False
    def getImage(self,name): #Gets an image, returns a error and defualt surface otherwise
        if name in self.LINK["cont"]:
            return self.LINK["cont"][name]
        self.LINK["errorDisplay"]("missing image '"+name+"'")
        gen = pygame.Surface((512,512))
        font = pygame.font.SysFont("impact",16)
        gen.blit(font.render("Error, missing image",16,(255,255,255)),[0,0])
        return gen
    def findInside(self,ents,exceptions = []): #Retruns all the entities inside this one
        res = []
        for a in ents:
            #Checks all 4 corners of the entity to check if it is inside this one
            ins = a.pos[0] >= self.pos[0] and a.pos[1] >= self.pos[1] and a.pos[0] < self.pos[0]+self.size[0] and a.pos[1] < self.pos[1]+self.size[1] #Top left
            ins2 = a.pos[0]+a.size[0] > self.pos[0] and a.pos[1]+a.size[1] > self.pos[1] and a.pos[0]+a.size[0] < self.pos[0]+self.size[0] and a.pos[1]+a.size[1] < self.pos[1]+self.size[1] #Bottom right
            ins3 = a.pos[0]+a.size[0] > self.pos[0] and a.pos[1] >= self.pos[1] and a.pos[0]+a.size[0] < self.pos[0]+self.size[0] and a.pos[1] < self.pos[1]+self.size[1] #Top right
            ins4 = a.pos[0] >= self.pos[0] and a.pos[1]+a.size[1] > self.pos[1] and a.pos[0] < self.pos[0]+self.size[0] and a.pos[1]+a.size[1] < self.pos[1]+self.size[1] #Bottom left
            if (ins or ins2 or ins3 or ins4) and not a in exceptions:
                res.append(a)
        return res
    def findInsideOrNextTo(self,ents,exceptions = []): #Retruns all the entities inside and next to this one (next as in touching)
        res = []
        for a in ents:
            #Checks all 4 corners of the entity to check if it is inside or next to this one
            ins = a.pos[0] >= self.pos[0] and a.pos[1] >= self.pos[1] and a.pos[0] <= self.pos[0]+self.size[0] and a.pos[1] <= self.pos[1]+self.size[1] #Top left
            ins2 = a.pos[0]+a.size[0] >= self.pos[0] and a.pos[1]+a.size[1] >= self.pos[1] and a.pos[0]+a.size[0] <= self.pos[0]+self.size[0] and a.pos[1]+a.size[1] <= self.pos[1]+self.size[1] #Bottom right
            ins3 = a.pos[0]+a.size[0] >= self.pos[0] and a.pos[1] >= self.pos[1] and a.pos[0]+a.size[0] <= self.pos[0]+self.size[0] and a.pos[1] <= self.pos[1]+self.size[1] #Top right
            ins4 = a.pos[0] >= self.pos[0] and a.pos[1]+a.size[1] >= self.pos[1] and a.pos[0] <= self.pos[0]+self.size[0] and a.pos[1]+a.size[1] <= self.pos[1]+self.size[1] #Bottom left
            if (ins or ins2 or ins3 or ins4) and not a in exceptions:
                res.append(a)
        return res
    def canShow(self): #Return wether the entitie should show on a scematic view in the game (doesen't apply to map editor)
        return self.__sShow == True
    def delete(self): #Deletes the entity.
        self.REQUEST_DELETE = True

