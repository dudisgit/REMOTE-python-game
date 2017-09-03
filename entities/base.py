#This file is the base entitie that all other entites inheret to.
import pygame,time,math

MESH_BLOCK_SIZE = 125 #Size of a single mesh block (game.py)
ROOM_BORDER = 15 # Width of a boarder in a room
DOOR_BORDER = 15 #Border of a door

def nothing(*args): #Does nothing
    pass

class Main(object):
    def __init__(self,x,y,LINK,ID):
        LINK["errorDisplay"]("Base entitie was created but shouldn't be. This class is for inheriting uses only!")
        self.init(x,y,LINK)
        self.ID = ID
    def init(self,x,y,LINK): #Called to initialize variables
        self.pos = [x,y] #Position of the entity
        self.size = [50,50] #Size of the entity
        self.angle = 0 #Angle of the entitity
        self.overide = False #If this entitiy should overwrite the SYNC settings (multipalyer)
        self.alive = True #Is the entitiy alive (Should only be used for destructable entities)
        self.settings = {} #Settings of the entity, this is a vital part since this is what is saved to the file along with position and size.
        self.linkable = [] #A list containing items describing what entity can link to this one.
        self.REQUEST_DELETE = False #If the entity is requesting to be deleted
        self.colisionType = 0 #Type of colision, 0 = Off, 1 = Circle, 2 = Box
        self.LINK = LINK #Cannot make it __LINK because the class it is inhertited by will not be able to access it.
        self.HINT = False #Hint what the object does
        self.hintMessage = "NO HINT" #Hinting message
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
                ins = pos[0] >= a.pos[0] and pos[1] >= a.pos[1] and pos[0] < a.pos[0]+a.size[0] and pos[1] < a.pos[1]+a.size[1] #Top left
                ins2 = pos[0]+size[0] > a.pos[0] and pos[1] > a.pos[1] and pos[0]+size[0] < a.pos[0]+a.size[0] and pos[1] < a.pos[1]+a.size[1] #Bottom right
                ins3 = pos[0] > a.pos[0]+a.size[0] and pos[1]+size[1] > a.pos[1] and pos[0] < a.pos[0]+a.size[0] and pos[1]+size[1] < a.pos[1]+a.size[1] #Top right
                ins4 = pos[0]+size[0] > a.pos[0] and pos[1]+size[1] > a.pos[1] and pos[0]+size[0] < a.pos[0]+a.size[0] and pos[1]+size[1] < a.pos[1]+a.size[1] #Bottom left
                if ins or ins2 or ins3 or ins4:
                    return a
        return False
    def getImage(self,name): #Gets an image, returns a error and defualt surface otherwise
        if name in self.LINK["cont"]: #Return the image
            return self.LINK["cont"][name]
        self.LINK["errorDisplay"]("missing image '"+name+"'")
        gen = pygame.Surface((140,60))
        font = pygame.font.SysFont("impact",16)
        gen.blit(font.render("Error, missing image",16,(255,255,255)),[0,0])
        return gen
    def __doPhysEnt(self,ENT,lag,opts): #Applys physics againsed one specific entity
        if ENT==self: #Exits to stop coliding with itself
            return opts
        res = opts
        if type(ENT)==self.getEnt("room") and not "d" in opts: #Possibly coliding with a rooms walls
            if self.pos[0]>ENT.pos[0] and self.pos[1]>ENT.pos[1] and self.pos[0]<ENT.pos[0]+ENT.size[0] and self.pos[1]<ENT.pos[1]+ENT.size[1]: #Is inside the room
                bpos = [self.pos[0]+0,self.pos[1]+0] #Before position
                if self.pos[0]<ENT.pos[0]+ROOM_BORDER:
                    self.pos[0] = ENT.pos[0]+ROOM_BORDER
                if self.pos[1]<ENT.pos[1]+ROOM_BORDER:
                    self.pos[1] = ENT.pos[1]+ROOM_BORDER
                if self.pos[0]>ENT.pos[0]+ENT.size[0]-ROOM_BORDER:
                    self.pos[0] = ENT.pos[0]+ENT.size[0]-ROOM_BORDER
                if self.pos[1]>ENT.pos[1]+ENT.size[1]-ROOM_BORDER:
                    self.pos[1] = ENT.pos[1]+ENT.size[1]-ROOM_BORDER
                if self.pos!=bpos: #Add before position to a variable incase a door is in the entities path
                    if not "a" in opts:
                        res = "a"+str(bpos[0])+","+str(bpos[1])
        elif type(ENT)==self.getEnt("door") or type(ENT)==self.getEnt("airlock"): #Possibly coloding with a doors walls
            if type(ENT)==self.getEnt("airlock"):
                lr = ENT.settings["dir"]>=2 #Left to right orientation
            else:
                lr = ENT.settings["lr"] == True
            if "a" in opts: #Get the drones last position before it colided with a rooms walls
                spl = opts.split(",")
                bpos = [float(spl[0][1:]),float(spl[1])]
            else: #Get the drones position normaly
                bpos = self.pos
            if lr: #Right to left
                if (bpos[1]>=ENT.pos[1] and bpos[1]<=ENT.pos[1]+ENT.size[1] and bpos[0]>ENT.pos[0] and bpos[0]<ENT.pos[0]+ENT.size[0]) or (bpos[1]>=ENT.pos[1]+DOOR_BORDER and bpos[1]<=ENT.pos[1]+ENT.size[1]-DOOR_BORDER and bpos[0]>ENT.pos[0]-ROOM_BORDER and bpos[0]<ENT.pos[0]+ENT.size[0]+ROOM_BORDER):
                    if "a" in opts: #Tell other rooms that they cannot colide with this entity
                        self.pos = bpos.copy()
                        res = "d"
                    #Colide with doors walls
                    if self.pos[1]<ENT.pos[1]+DOOR_BORDER:
                        self.pos[1] = ENT.pos[1]+DOOR_BORDER
                    if self.pos[1]>ENT.pos[1]+ENT.size[1]-DOOR_BORDER:
                        self.pos[1] = ENT.pos[1]+ENT.size[1]-DOOR_BORDER
            else: #Up to down
                if (bpos[0]>=ENT.pos[0] and bpos[0]<=ENT.pos[0]+ENT.size[0] and bpos[1]>ENT.pos[1] and bpos[1]<ENT.pos[1]+ENT.size[1]) or (bpos[0]>=ENT.pos[0]+DOOR_BORDER and bpos[0]<=ENT.pos[0]+ENT.size[0]-DOOR_BORDER and bpos[1]>ENT.pos[1]-ROOM_BORDER and bpos[1]<ENT.pos[1]+ENT.size[1]+ROOM_BORDER):
                    if "a" in opts: #Tell other rooms that they cannot colide with this entity
                        self.pos = bpos.copy()
                        res = "d"
                    #Colide with doors walls
                    if self.pos[0]<ENT.pos[0]+DOOR_BORDER:
                        self.pos[0] = ENT.pos[0]+DOOR_BORDER
                    if self.pos[0]>ENT.pos[0]+ENT.size[0]-DOOR_BORDER:
                        self.pos[0] = ENT.pos[0]+ENT.size[0]-DOOR_BORDER
        elif ENT.colisionType!=0: #Is this entity is colidable
            if ENT.colisionType==1: #Circle
                dist = math.sqrt(( (self.pos[0]-ENT.pos[0])**2 ) + ( (self.pos[1]-ENT.pos[1])**2 ))
                if dist<30: #Is coliding
                    ang = math.atan2((self.pos[0]-ENT.pos[0]),(self.pos[1]-ENT.pos[1]))
                    self.pos = [ENT.pos[0]+(math.sin(ang)*30),ENT.pos[1]+(math.cos(ang)*30)]
            else: #Box colision
                if self.pos[0]>ENT.pos[0] and self.pos[0]<ENT.pos[0]+ENT.size[0] and self.pos[1]>ENT.pos[1] and self.pos[1]<ENT.pos[1]+ENT.size[1]:
                    ang = math.atan2((self.pos[0]-(ENT.pos[0]+(ENT.size[0]/2))),(self.pos[1]-(ENT.pos[1]+(ENT.size[1]/2))))
                    self.pos = [self.pos[0]+(math.sin(ang)*4*lag),self.pos[1]+(math.cos(ang)*4*lag)]
        return res

    def applyPhysics(self,lag=1): #Applys the physics to this entity
        bpos = [self.pos[0]+0,self.pos[1]+0]
        opts = ""
        for x in range(int(self.pos[0]/MESH_BLOCK_SIZE)-1,int(self.pos[0]/MESH_BLOCK_SIZE)+int(self.size[0]/MESH_BLOCK_SIZE)+1): #Loop through a 3x3 square in MESH to find coliding entities
            if x in self.LINK["mesh"]: #X column exists
                for y in range(int(self.pos[1]/MESH_BLOCK_SIZE)-1,int(self.pos[1]/MESH_BLOCK_SIZE)+int(self.size[1]/MESH_BLOCK_SIZE)+1):
                    if y in self.LINK["mesh"][x]: #Y column exists
                        for ENT in self.LINK["mesh"][x][y]: #Loop through every entitiy of this block
                            opts=self.__doPhysEnt(ENT,lag,opts) #Check if this entitiy is coliding with the specific other entity
        self.changeMesh(bpos) #Change the position of the MESH so its accurate with the current entity
    def changeMesh(self,before): #Moves the entity into a different mesh
        if round(before[0]/MESH_BLOCK_SIZE)!=round(self.pos[0]/MESH_BLOCK_SIZE) or round(before[1]/MESH_BLOCK_SIZE)!=round(self.pos[1]/MESH_BLOCK_SIZE): #Move the mesh
            for x in range(round(before[0]/MESH_BLOCK_SIZE)-1,round(before[0]/MESH_BLOCK_SIZE)+round(self.size[0]/MESH_BLOCK_SIZE)+1): #Delete this entity from the MESH before
                if x in self.LINK["mesh"]:
                    for y in range(round(before[1]/MESH_BLOCK_SIZE)-1,round(before[1]/MESH_BLOCK_SIZE)+round(self.size[1]/MESH_BLOCK_SIZE)+1):
                        if y in self.LINK["mesh"][x]:
                            if self in self.LINK["mesh"][x][y]:
                                self.LINK["mesh"][x][y].remove(self)
            for x in range(round(self.pos[0]/MESH_BLOCK_SIZE)-1,round(self.pos[0]/MESH_BLOCK_SIZE)+round(self.size[0]/MESH_BLOCK_SIZE)+1): #Add this entity to the MESH after it has moved (3x3 square)
                if not x in self.LINK["mesh"]:
                    self.LINK["mesh"][x] = {}
                for y in range(round(self.pos[1]/MESH_BLOCK_SIZE)-1,round(self.pos[1]/MESH_BLOCK_SIZE)+round(self.size[1]/MESH_BLOCK_SIZE)+1):
                    if not y in self.LINK["mesh"][x]:
                        self.LINK["mesh"][x][y] = []
                    self.LINK["mesh"][x][y].append(self)
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
    def renderHint(self,surf,message,pos): #Render a hint box
        screenRes = self.LINK["reslution"] #Screen reslution
        boxPos = [pos[0]+10,pos[1]+10] #Position of the box
        boxWidth = screenRes[0]/2 #Width of the box will be half the screen width
        boxHeight = 0
        mes = message.split(" ") #Split the message up by spaces
        charLength = 10 #Length of 1 charicter (constant)
        font = self.LINK["font24"] #Font to use when rendering
        adding = "" #Text being added to that line
        drawWord = [] #Store all the text in a list to be rendered
        for word in mes: #Loop through all text samples and build a list of strings that are cut off when they get to the end and start on the next element
            if (len(adding)+len(word))*charLength > boxWidth or "\n" in word: #Length would be above the length of the box or the message requested a new line using "\n"
                drawWord.append(adding+"")
                if "\n" in word: #Remove the "\n"
                    spl = word.split("\n")
                    spl.remove("")
                    adding = spl[0]+" "
                else:
                    adding = word+" "
                boxHeight += 20
            else:
                adding += word+" "
        if len(adding)!=0: #If any are left then add them onto the end
            drawWord.append(adding+"")
            boxHeight+=20
        boxPos[1] = pos[1]-boxHeight-10 #Re-calculate the box position depening on the text height
        pygame.draw.rect(surf,(0,0,0),[boxPos[0]-4,boxPos[1]-4,boxWidth,boxHeight+8]) #Black box background
        mult = abs(math.cos(time.time()*3)) #Box flashing
        pygame.draw.rect(surf,(255*mult,255*mult,0),[boxPos[0]-4,boxPos[1]-4,boxWidth,boxHeight+8],3) #Flashing box
        for i,a in enumerate(drawWord): #Draw all the text calculated above
            surf.blit(font.render(a,16,(0,255,0)),[boxPos[0],boxPos[1]+(i*20)])
    def rightPos(self): #Returns the last position and size of the box
        if self.__surface is None:
            return [0,0,0,0]
        return [self.__lastRenderPos[0]+0,self.__lastRenderPos[1]+0]+list(self.__surface.get_size())
    def canShow(self): #Return wether the entitie should show on a scematic view in the game (doesen't apply to map editor)
        return self.__sShow == True
    def drawRotate(self,applySurf,x,y,surf,angle): #This function will rotate a surface round its center and draw it to the screen.
        siz = list(surf.get_size())
        sub = [abs(math.sin(angle/90*math.pi)*siz[0]/5),abs(math.sin(angle/90*math.pi)*siz[1]/5)]
        applySurf.blit(pygame.transform.rotate(surf,angle),(x-sub[0],y-sub[1]))
    def delete(self): #Deletes the entity.
        self.REQUEST_DELETE = True

