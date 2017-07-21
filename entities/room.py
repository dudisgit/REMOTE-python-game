#Do not run this file, it is a module!
import pygame
import entities.base as base

class Main(base.Main):
    def __init__(self,x,y,LINK,ID,number=-1):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.number = number #The room number this room is.
        self.settings["radiation"] = False
        self.settings["power"] = [] #List of generators room is linked to
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the room is inside anouther room
        self.hintMessage = "A room is a space the drone can move about in, you can resize it using the slanted line at the bottom right"
    def __ChangeRadiation(self,LINK,state): #switches radiation on/off
        self.settings["radiation"] = state == True
    def __LinkTo(self,LINK): #"Link to" button was pressed
        LINK["currentScreen"].linkItem(self,"power") #A bit bodgy but this can only be called in the map designer.
    def __UnlinkAll(self,LINK): #Deletes all links on this entity
        self.settings["power"] = []
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        pows = []
        for i,a in enumerate(self.settings["power"]):
            try:
                pows.append(a.ID)
            except:
                self.LINK["errorDisplay"]("Saving power link "+str(i)+"(index) in room "+str(self.ID)+"(ID) failed.")
        return ["room",self.ID,self.pos,self.size,self.settings["radiation"],pows]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.size = data[3]
        self.settings["radiation"] = data[4]
        for a in data[5]:
            if a in idRef:
                self.settings["power"].append(idRef[a])
            else:
                self.LINK["errorDisplay"]("Loading power link "+str(a)+"(ID) failed in room "+str(self.ID)+"(ID).")
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,145)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check1 = self.LINK["screenLib"].CheckButton(5,40,self.LINK,"Radiation leak",self.settings["radiation"],self.__ChangeRadiation) #Radiation checkbox
        self.__but2 = self.LINK["screenLib"].Button(5,75,self.LINK,"Link to",self.__LinkTo)
        self.__but3 = self.LINK["screenLib"].Button(5,110,self.LINK,"Unlink all",self.__UnlinkAll)
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__but2.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__but3.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
    def rightRender(self,x,y,surf): #Render the context menu
        windowPos = [x,y+50] #Window position
        #The 4 IF statments below will make sure the context menu is allways on the screen, even if this entity is not.
        if windowPos[0]<300:
            windowPos[0] = 300
        if windowPos[0]>self.LINK["reslution"][0]-150:
            windowPos[0] = self.LINK["reslution"][0]-150
        if windowPos[1]<10:
            windowPos[1] = 10
        if windowPos[1]>self.LINK["reslution"][1]-150:
            windowPos[1] = self.LINK["reslution"][1]-150
        self.__surface.fill((0,0,0)) #Empty the context menu surface
        self.__but1.render(self.__but1.pos[0],self.__but1.pos[1],1,1,self.__surface) #Render delete button
        self.__check1.render(self.__check1.pos[0],self.__check1.pos[1],1,1,self.__surface) #Render checkbutton
        self.__but2.render(self.__but2.pos[0],self.__but2.pos[1],1,1,self.__surface) #Render link button
        self.__but3.render(self.__but3.pos[0],self.__but3.pos[1],1,1,self.__surface) #Render unlink button
        surfSize = self.__surface.get_size() #Get the size of the context menu
        self.__lastRenderPos = [windowPos[0]-int(surfSize[0]/2),windowPos[1]] #Used for event loops
        pygame.draw.polygon(surf,(0,255,0),[ [windowPos[0]-int(surfSize[0]/3),windowPos[1]],
                                             [x,y],
                                             [windowPos[0]+int(surfSize[0]/3),windowPos[1]] ],2) #This is the triangle pointing from the menu to the entity
        pygame.draw.rect(self.__surface,(0,255,0),[1,1,208,surfSize[1]-3],2) #Outline rectangle
        surf.blit(self.__surface,self.__lastRenderPos) #Draw all results to the screen
    def rightUnload(self): #This delets the pygame surface and widget classes. This is mainly so theirs no memory leaks.
        self.__surface = None
        self.HINT = False
        self.__but1 = None
        self.__but2 = None
        self.__but3 = None
        self.__check1 = None
    def editMove(self,ents): #Room is being moved
        ins = self.findInsideOrNextTo(ents,[self])
        for ent in ins:
            if type(ent)==Main:
                self.__inRoom = True
                break
        else:
            self.__inRoom = False
    def giveError(self,ents): #Scans and gives an error out
        ins = self.findInsideOrNextTo(ents,[self])
        for ent in ins:
            if type(ent)==Main:
                return "Room colide"
        if len(self.settings["power"])==0:
            return "No power (room)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if self.settings["radiation"] and edit:
            for i in range(-int(self.size[1]/25)+1,int(self.size[0]/25)):
                if i<0:
                    ad1 = abs(i)*25*scale
                else:
                    ad1 = 0
                if i>int(self.size[0]/25)-int(self.size[1]/25):
                    ad2 = abs(i-(int(self.size[0]/25)-int(self.size[1]/25)))*25*scale
                else:
                    ad2 = 0
                pygame.draw.line(surf,(200,0,0),[x+(i*25*scale)+ad1,y+ad1],[x+(((i*25)+self.size[1])*scale)-ad2,y+(self.size[1]*scale)-ad2])
        if self.__inRoom: #If inside a room in the map editor, used to raise error
            pygame.draw.rect(surf,(200,0,0),[x,y,self.size[0]*scale,self.size[1]*scale],int(5*scale))
        else:
            pygame.draw.rect(surf,(200,200,200),[x,y,self.size[0]*scale,self.size[1]*scale],int(5*scale))
        if edit:
            pygame.draw.line(surf,(255,255,255),[x+(self.size[0]*scale),y+((self.size[1]-25)*scale)],[x+((self.size[0]-25)*scale),y+(self.size[1]*scale)],int(5*scale))
            scrolPos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Calculate the scroll position
            rem = [] #Items to remove because they where deleted
            for a in self.settings["power"]: #Loop through power wires
                pygame.draw.line(surf,(100,0,100),[x+(self.size[0]*0.5*scale),y+(self.size[1]*0.5*scale)],
                                                    [((a.pos[0]+(a.size[0]/2))*scale)-scrolPos[0],((a.pos[1]+(a.size[1]/2))*scale)-scrolPos[1]],3)
                if a.REQUEST_DELETE: #Entity is has been deleted (this entity is keeping it alive with its pointer)
                    rem.append(a)
            for a in rem: #Remote entities that have been deleted
                self.settings["power"].remove(a)
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
