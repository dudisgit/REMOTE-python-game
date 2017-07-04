#Map editor module
import pygame

ZOOM_SPEED = 1.2
BLOCK_SIZE = 50

class DumpButton: #Used for entity selecting buttons to have functions to call to
    def __init__(self,backLink,name):
        self.__back = backLink
        self.__name = name
    def call(self,LINK):
        self.__back.addItem(self.__name)

class Main:
    def __init__(self,LINK):
        self.__LINK = LINK
        self.__ents = [LINK["ents"]["room"].Main(BLOCK_SIZE,BLOCK_SIZE,LINK)] #All entities in the screen
        self.__renderFunc = LINK["render"].Scematic(LINK,True) #Class to render entities
        self.__reslution = LINK["reslution"] #Reslution of the editor
        self.__renderFunc.ents = self.__ents #Make sure the rendering class gets updates from this one through a pointer
        self.__entSelect = LINK["screenLib"].Listbox(10,self.__reslution[1]-300,LINK,[160,290]) #Entity selecting window
        self.__buttonObjs = [] #Used to store button classes inside
        for a in LINK["ents"]: #Fill the entity selecting window with items
            if a!="base": #This entity is restricted and is not allowed to be spawned
                self.__buttonObjs.append(DumpButton(self,a+"")) #Give the button a class to call to
                self.__entSelect.addItem(LINK["screenLib"].Button,a,self.__buttonObjs[-1].call) #Add the new button
        self.__label = LINK["screenLib"].Label(10,self.__reslution[1]-340,LINK,"Spawning menu") #Label to describe entity selecting window
        self.__fileMenu = LINK["screenLib"].Button(10,self.__reslution[1]-380,LINK,"File") #File menu
        self.__mouseStart = [0,0] #Used for detecting distances between mosue and the object being selected.
        self.__scroll = [0,0] #Scroll amount through the map
        self.__action = [-1,[]] #Action taking place, e.g. moving an object
        #Types of actions:
        #   1 - Creating a new object
        #   2 - Linking an object to anouther
        self.__click = False #For detecting changes in mouse clicks
        self.__active = -1 #The item that is currently active.
        self.__activeDrag = -1 #The item that is currently (probebly) being dragged
        self.__roomScale = False #If the item is currently being resized (room only)
        self.__scrolling = False #If the user is currently scrolling accross the map
        self.__scrollClick = False #Detects changes in right click or middle button
        self.__mouseSave = [0,0] #Used to save the mouse position for rendering
        self.__zoom = 1 #Zoom amount
    def linkItem(self,item,linkName): #Links one item to anouther if they have the same connection type
        if self.__action[0]==-1:
            self.__action[0] = 2
            self.__action[1] = [item,linkName]
    def addItem(self,name): #Adds a new item to the map
        if self.__action[0]==-1: #No actions are being done
            self.__action[0] = 1
            self.__ents.append(self.__LINK["ents"][name].Main(0,0,self.__LINK))
            self.__action[1] = [self.__ents[-1]]
    def findEnt(self,posx,posy): #Returns the entitie at the position [posx,posy]
        #This will select rooms last!
        rEnt = -1 #Room entity
        for i,a in enumerate(self.__ents):
            if posx>a.pos[0] and posy>a.pos[1] and posx<a.pos[0]+a.size[0] and posy<a.pos[1]+a.size[1]:
                if type(a)==self.getEnt("room"): #If the entity is a room
                    rEnt = i+0
                else:
                    return i
        if rEnt!=-1: #If no other choice but a room is found then return the room
            return rEnt
        return False
    def getEnt(self,name): #Returns the entity with the name
        if name in self.__LINK["ents"]: #Does the entity exist?
            return self.__LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.__LINK["errorDisplay"]("Tried to create entity but doesen't exist '"+name+"'")
        return self.__LINK["null"]
    def loop(self,mouse,kBuf): #Event loop for screen
        self.__mouseSave = [mouse[1],mouse[2]] #Saves the mouse cursor position for use with rendering
        self.__entSelect.loop(mouse,kBuf) #Event loop for entity selecting window
        self.__fileMenu.loop(mouse,kBuf) #Event loop for file button
        rem = [] #A list that gets filled with entities that want to delete themselves
        for a in self.__ents: #Loop through all entities and check if they want to delete themselved
            if a.REQUEST_DELETE:
                rem.append(a)
        if len(rem)!=0: #Make sure nothing is selected when deleting occoures
            if self.__active != -1:
                self.__ents[self.__active].rightUnload()
                self.__active = -1
            if self.__activeDrag != -1:
                self.__activeDrag = -1
        for a in rem: #Remove the items that want to be deleted
            self.__ents.remove(a)
        snap = [round(mouse[1]/BLOCK_SIZE/self.__zoom)*BLOCK_SIZE*self.__zoom,round(mouse[2]/BLOCK_SIZE/self.__zoom)*BLOCK_SIZE*self.__zoom] #Snap position of the mouse
        insideSelect = mouse[2]>self.__reslution[1]-300 and mouse[2]<self.__reslution[1]-10 and mouse[1]>10 and mouse[1]<170 #Inside the entity selecting window
        if self.__scrollClick != (mouse[3] or mouse[4]): #Used for detecting if the interface should scroll or not
            self.__scrollClick = (mouse[3] or mouse[4])
            if self.__scrollClick:
                ent = self.findEnt((mouse[1]+self.__scroll[0])/self.__zoom,(mouse[2]+self.__scroll[1])/self.__zoom) #Find what entity the mouse is inside
                if type(ent) == bool and self.__activeDrag == -1: #Not inside one, must be trying to scroll
                    if not insideSelect:
                        self.__mouseStart = [mouse[1]+0,mouse[2]+0]
                        self.__scrolling = True
                else: #Open a context menu on the entity
                    if self.__active !=-1: #Unload the last context menu if it has allredey been opened
                        self.__ents[self.__active].rightUnload()
                    self.__active = ent + 0
                    self.__ents[ent].rightInit(self.__LINK["main"])
            else:
                self.__scrolling = False
        if self.__active != -1:
            self.__ents[self.__active].rightLoop(mouse,kBuf)
        if self.__scrolling: #User is scrolling
            self.__scroll[0]-=mouse[1]-self.__mouseStart[0]
            self.__scroll[1]-=mouse[2]-self.__mouseStart[1]
            self.__mouseStart = [mouse[1]+0,mouse[2]+0]
        for event in kBuf: #Keyboard event loop
            if event.type == 6 and not insideSelect: #Scrollwheel
                if event.button == 4: #Mouse wheel up
                    self.__zoom *= ZOOM_SPEED
                    if self.__zoom > 10:
                        self.__zoom = 10
                elif event.button == 5: #Mouse wheel down
                    self.__zoom /= ZOOM_SPEED
                    if self.__zoom<0.1:
                        self.__zoom = 0.1
        if self.__click != mouse[0]: #Mouse click was changed
            self.__click = mouse[0] == True
            if mouse[0]: #Mouse down
                if self.__action[0] != -1:
                    if self.__action[0] == 1: #Add new entity
                        for a in self.__ents: #Check all objects for colosions
                            a.editMove(self.__ents)
                    elif self.__action[0] == 2: #Link an entity
                        ent = self.findEnt((mouse[1]+self.__scroll[0])/self.__zoom,(mouse[2]+self.__scroll[1])/self.__zoom)
                        if type(ent)!=bool: #Found an entity
                            if self.__action[1][1] in self.__ents[ent].linkable: #Entity has the correct link type
                                if self.__action[1][1] in self.__action[1][0].settings: #Error checking entities settings
                                    if not self.__ents[ent] in self.__action[1][0].settings[self.__action[1][1]]: #Is entity allredey linked?
                                        self.__action[1][0].settings[self.__action[1][1]].append(self.__ents[ent])
                                else:
                                    self.__LINK["errorDisplay"]("Entity '"+str(self.__action[1][0])+"' does not have the link setting of '"+self.__action[1][1]+"'")
                    self.__action[0] = -1
                    self.__action[1] = []
                else: #Detect if the user is trying to drag anouther entity around
                    mPos = [(mouse[1]+self.__scroll[0])/self.__zoom,(mouse[2]+self.__scroll[1])/self.__zoom] #Mouse position local to entity positions
                    itm = self.findEnt(mPos[0],mPos[1])
                    self.__roomScale = False
                    if type(itm) == int: #Found an entity
                        self.__activeDrag = itm+0
                        self.__mouseStart = [mouse[1]-(self.__ents[itm].pos[0]*self.__zoom)+self.__scroll[0],mouse[2]-(self.__ents[itm].pos[1]*self.__zoom)+self.__scroll[1]]
                        if type(self.__ents[itm]) == self.getEnt("room"): #Is a room
                            if mPos[0]>self.__ents[itm].pos[0]+self.__ents[itm].size[0]-25 and mPos[1]>self.__ents[itm].pos[1]+self.__ents[itm].size[1]-25:
                                #This will run if the user is trying to resize a room
                                self.__roomScale = True
                        if self.__active != -1 and self.__active != self.__activeDrag: #Close the context menu if clicking on the wrong menu
                            self.__ents[self.__active].rightUnload()
                            self.__active = -1
            else:
                self.__roomScale = False
                if self.__activeDrag != -1: #Finished dragging an object
                    self.__activeDrag = -1
                    for a in self.__ents: #Check all objects for colosions
                        a.editMove(self.__ents)
        if self.__activeDrag != -1: #An object is being dragged
            if self.__roomScale: #If it is a room being resized
                self.__ents[self.__activeDrag].size = [round((mouse[1]+self.__scroll[0])/self.__zoom/BLOCK_SIZE)*BLOCK_SIZE,
                                                round((mouse[2]+self.__scroll[1])/self.__zoom/BLOCK_SIZE)*BLOCK_SIZE]
                self.__ents[self.__activeDrag].size[0] -= self.__ents[self.__activeDrag].pos[0]
                self.__ents[self.__activeDrag].size[1] -= self.__ents[self.__activeDrag].pos[1]
                #Check size and make sure the designer isn't resizing the room below 0
                if self.__ents[self.__activeDrag].size[0]<=0:
                    self.__ents[self.__activeDrag].size[0] = 50
                if self.__ents[self.__activeDrag].size[1]<=0:
                    self.__ents[self.__activeDrag].size[1] = 50
            else: #Move the entity normaly
                self.__ents[self.__activeDrag].pos = [round((mouse[1]-self.__mouseStart[0]+self.__scroll[0])/self.__zoom/BLOCK_SIZE)*BLOCK_SIZE,
                                                round((mouse[2]-self.__mouseStart[1]+self.__scroll[1])/self.__zoom/BLOCK_SIZE)*BLOCK_SIZE]
            self.__ents[self.__activeDrag].editMove(self.__ents) #Check for colosions
        if self.__action[0] != -1: #An action is being taken out
            if self.__action[0] == 1: #Adding new item
                self.__action[1][0].pos = [round((mouse[1]+self.__scroll[0])/self.__zoom/BLOCK_SIZE)*BLOCK_SIZE,
                                            round((mouse[2]+self.__scroll[1])/self.__zoom/BLOCK_SIZE)*BLOCK_SIZE]
                self.__action[1][0].editMove(self.__ents)
    def render(self,surf=None): #Renders everything
        if surf is None:
            surf = self.__LINK["main"]
        pygame.draw.line(surf,(255,255,0),[-self.__scroll[0]-(10*self.__zoom),-self.__scroll[1]],[-self.__scroll[0]+(10*self.__zoom),-self.__scroll[1]])
        pygame.draw.line(surf,(255,255,0),[-self.__scroll[0],-self.__scroll[1]-(10*self.__zoom)],[-self.__scroll[0],-self.__scroll[1]+(10*self.__zoom)])
        self.__renderFunc.render(self.__scroll[0],self.__scroll[1],self.__zoom)
        if self.__action[0] != -1:
            if self.__action[0] == 2: #Render the wire when linking two entiteis
                pygame.draw.line(surf,(255,0,255),[((self.__action[1][0].pos[0]+(self.__action[1][0].size[0]/2))*self.__zoom)-self.__scroll[0],
                                                    ((self.__action[1][0].pos[1]+(self.__action[1][0].size[1]/2))*self.__zoom)-self.__scroll[1]],self.__mouseSave,4)
                ent = self.findEnt((self.__mouseSave[0]+self.__scroll[0])/self.__zoom,(self.__mouseSave[1]+self.__scroll[1])/self.__zoom)
                if type(ent)!=bool: #Found an entity
                    if self.__action[1][1] in self.__ents[ent].linkable: #Entity is compatible
                        pygame.draw.circle(surf,(255,0,255),self.__mouseSave,8)
                        pygame.draw.rect(surf,(255,0,255),[(self.__ents[ent].pos[0]*self.__zoom)-self.__scroll[0],(self.__ents[ent].pos[1]*self.__zoom)-self.__scroll[1],
                                                            self.__ents[ent].size[0]*self.__zoom,self.__ents[ent].size[1]*self.__zoom],3)
        if self.__active != -1: #Render context menu if it is open
            self.__ents[self.__active].rightRender(((self.__ents[self.__active].pos[0]+(self.__ents[self.__active].size[0]/2))*self.__zoom)-self.__scroll[0],
                                                    ((self.__ents[self.__active].pos[1]+self.__ents[self.__active].size[1])*self.__zoom)-self.__scroll[1],surf)
        self.__entSelect.render(self.__entSelect.pos[0],self.__entSelect.pos[1],1,1,surf)
        self.__label.render(self.__label.pos[0],self.__label.pos[1],1,1,surf)
        self.__fileMenu.render(self.__fileMenu.pos[0],self.__fileMenu.pos[1],1,1,surf)
