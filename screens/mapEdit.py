#Map editor module
import pygame, math, time, sys, pickle

ZOOM_SPEED = 1.2 #Zooming speed
BLOCK_SIZE = 50 #Very important you don't change this.

class DumpButton: #Used for entity selecting buttons to have functions to call to
    def __init__(self,backLink,name):
        self.__back = backLink
        self.__name = name
    def call(self,LINK):
        self.__back.addItem(self.__name)
    def call2(self,LINK):
        self.__back.setMapName(self.__name)

class Main:
    def __init__(self,LINK):
        self.__LINK = LINK
        self.__ents = [] #All entities in the screen
        self.__renderFunc = LINK["render"].Scematic(LINK,True) #Class to render entities
        self.__reslution = LINK["reslution"] #Reslution of the editor
        self.__renderFunc.ents = self.__ents #Make sure the rendering class gets updates from this one through a pointer
        self.__entSelect = LINK["screenLib"].Listbox(10,self.__reslution[1]-300,LINK,[160,290]) #Entity selecting window
        self.__buttonObjs = [] #Used to store button classes inside
        LINK["multi"] = -1 #Say to all entities that they are in a map editor
        if len(LINK["ents"])==0:
            LINK["errorDisplay"]("No entities exist")
        for a in LINK["ents"]: #Fill the entity selecting window with items
            if not a in ["base","ship","lure","sensor"]: #This entity is restricted and is not allowed to be spawned
                self.__buttonObjs.append(DumpButton(self,a+"")) #Give the button a class to call to
                self.__entSelect.addItem(LINK["screenLib"].Button,a,self.__buttonObjs[-1].call) #Add the new button
        self.__label = LINK["screenLib"].Label(10,self.__reslution[1]-340,LINK,"Spawning menu") #Label to describe entity selecting window
        self.__fileMenu = LINK["screenLib"].Button(10,self.__reslution[1]-380,LINK,"File",self.FileMenuInit) #File menu
        self.__mouseStart = [0,0] #Used for detecting distances between mosue and the object being selected.
        self.__scroll = [0,0] #Scroll amount through the map
        self.__action = [-1,[]] #Action taking place, e.g. moving an object
        self.__AddedEnts = [] #Used to give hints when adding entities
        if LINK["hints"]:
            self.__Hinting = 0 #Start of hinting
        else:
            self.__Hinting = 4 #End of hinting
        #Types of actions:
        #   1 - Creating a new object
        #   2 - Linking an object to anouther
        self.__click = False #For detecting changes in mouse clicks
        self.__active = -1 #The item that is currently active.
        self.__activeDrag = -1 #The item that is currently (probebly) being dragged
        self.__roomScale = False #If the item is currently being resized (room only)
        self.__scrolling = False #If the user is currently scrolling accross the map
        self.__scrollClick = False #Detects changes in right click or middle button
        self.__FileMenu = False #Inside the file menu
        self.__dialog = [] #File menu dialog
        self.__changes = False #Changes where applied to the map
        self.__GlobalID = 0 #A global ID given to all entities, this helps with linking them together.
        self.__mouseSave = [0,0] #Used to save the mouse position for rendering
        self.__zoom = 1 #Zoom amount
        self.FileMenuReset() #Set the scroll to the centre of the screen
    def setMapName(self,name): #Loads map <name> into the text feild
        self.__NameInput.text = name+""
    def noDefault(self): #Makes all airlocks 'defualt' False
        for a in self.__ents:
            if type(a)==self.getEnt("airlock"):
                a.settings["default"] = False
    def renderHint(self,surf,message,pos): #Render a hint box
        screenRes = self.__LINK["reslution"] #Screen reslution
        boxPos = [pos[0]+10,pos[1]+10] #Position of the box
        boxWidth = screenRes[0]/2 #Width of the box will be half the screen width
        boxHeight = 0
        mes = message.split(" ") #Split the message up by spaces
        font = self.__LINK["font24"] #Font to use when rendering
        adding = "" #Text being added to that line
        drawWord = [] #Store all the text in a list to be rendered
        for word in mes: #Loop through all text samples and build a list of strings that are cut off when they get to the end and start on the next element
            if font.size(adding+word)[0] > boxWidth or "\n" in word: #Length would be above the length of the box or the message requested a new line using "\n"
                drawWord.append(adding+"")
                if "\n" in word: #Remove the "\n"
                    spl = word.split("\n")
                    if "" in spl:
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
        boxHeight+=20
        boxPos[1] = pos[1]-boxHeight-10 #Re-calculate the box position depening on the text height
        pygame.draw.rect(surf,(0,0,0),[boxPos[0]-4,boxPos[1]-4,boxWidth,boxHeight+8]) #Black box background
        mult = abs(math.cos(time.time()*3)) #Box flashing
        pygame.draw.rect(surf,(255*mult,255*mult,0),[boxPos[0]-4,boxPos[1]-4,boxWidth,boxHeight+8],3) #Flashing box
        surf.blit(font.render("Press enter or space to continue",16,(255*mult,255*mult,0)),[boxPos[0],boxPos[1]+boxHeight-16])
        for i,a in enumerate(drawWord): #Draw all the text calculated above
            surf.blit(font.render(a,16,(0,255,0)),[boxPos[0],boxPos[1]+(i*20)])
    def linkItem(self,item,linkName): #Links one item to anouther if they have the same connection type
        if self.__action[0]==-1:
            self.__action[0] = 2
            self.__action[1] = [item,linkName]
    def addItem(self,name): #Adds a new item to the map
        if not name in self.__LINK["ents"]:
            self.__LINK["errorDisplay"]("Tried to add an entity but it doesen't exist.")
        if self.__action[0]==-1: #No actions are being done
            self.__action[0] = 1
            self.__ents.append(self.__LINK["ents"][name].Main(0,0,self.__LINK,self.__GlobalID+0))
            self.__LINK["log"]("Created new entity '"+name+"'")
            self.__GlobalID += 1
            self.__action[1] = [self.__ents[-1]]
            if not name in self.__AddedEnts:
                self.__AddedEnts.append(name+"")
                self.__ents[-1].HINT = self.__LINK["hints"]==True
            self.__changes = True
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
    def loop(self,mouse,kBuf,lag): #Event loop for screen
        for a in kBuf:
            if a.type == pygame.QUIT and self.__changes:
                self.saveAs("MapEdit unsaved changes when closed backup.map")
        if self.__Hinting != 4: #In hint
            for a in kBuf:
                if a.type == pygame.KEYDOWN:
                    if a.key == pygame.K_SPACE or a.key == pygame.K_RETURN:
                        self.__Hinting += 1
                        break
            if self.__Hinting == 4:
                self.__LINK["log"]("Finished hints")
            return 0
        if self.__FileMenu: #In file menu
            if self.__FileMenu:
                self.__ResetButton.loop(mouse,kBuf)
            if self.__FileMenu:
                self.__BackButton.loop(mouse,kBuf)
            if self.__FileMenu:
                self.__MenuButton.loop(mouse,kBuf)
            if len(self.__dialog)!=0: #A dialog is open
                sx,sy = self.__dialog[0].get_size() #Get size of dialog box
                sx2,sy2 = self.__LINK["main"].get_size() #Get size of screen
                bmouse = [mouse[0],mouse[1]-((sx2/2)-(sx/2)),mouse[2]-((sy2/2)-(sy/2))]+mouse[3:] #Get mouse position local to dialog window
                for a in self.__dialog[1:]: #Event loop for dialogs widgets
                    a.loop(bmouse,kBuf)
            elif self.__FileMenu: #Disable looping for map selecting
                self.__MapSelect.loop(mouse,kBuf)
                self.__SaveButton.loop(mouse,kBuf)
                self.__NameInput.loop(mouse,kBuf)
                self.__LoadButton.loop(mouse,kBuf)
            return 0
        self.__mouseSave = [mouse[1],mouse[2]] #Saves the mouse cursor position for use with rendering
        self.__entSelect.loop(mouse,kBuf) #Event loop for entity selecting window
        self.__fileMenu.loop(mouse,kBuf) #Event loop for file button
        rem = [] #A list that gets filled with entities that want to delete themselves
        for a in self.__ents: #Loop through all entities and check if they want to delete themselved
            if a.REQUEST_DELETE:
                rem.append(a)
        if len(rem)!=0: #Make sure nothing is selected when deleting occoures
            if self.__active != -1:
                try:
                    self.__ents[self.__active].rightUnload()
                except:
                    self.__LINK["errorDisplay"]("Failed to run unload function when closing menu",sys.exc_info())
                self.__active = -1
            if self.__activeDrag != -1:
                self.__activeDrag = -1
        if self.__active != -1:
            dat = self.__ents[self.__active].rightPos()
            outside = not (mouse[1]>dat[0] and mouse[2]>dat[1] and mouse[1]<dat[0]+dat[2] and mouse[2]<dat[1]+dat[3])
        else:
            outside = True #Outside the context/options box
        for a in rem: #Remove the items that want to be deleted
            self.__ents.remove(a)
        snap = [round(mouse[1]/BLOCK_SIZE/self.__zoom)*BLOCK_SIZE*self.__zoom,round(mouse[2]/BLOCK_SIZE/self.__zoom)*BLOCK_SIZE*self.__zoom] #Snap position of the mouse
        insideSelect = mouse[2]>self.__reslution[1]-300 and mouse[2]<self.__reslution[1]-10 and mouse[1]>10 and mouse[1]<170 #Inside the entity selecting window
        if self.__scrollClick != (mouse[3] or mouse[4]): #Used for detecting if the interface should scroll or not
            self.__scrollClick = (mouse[3] or mouse[4])
            if self.__scrollClick:
                ent = self.findEnt((mouse[1]+self.__scroll[0])/self.__zoom,(mouse[2]+self.__scroll[1])/self.__zoom) #Find what entity the mouse is inside
                if outside:
                    if (ent != self.__active or type(ent)==bool) and self.__active != -1 and mouse[4]:
                        try:
                            self.__ents[self.__active].rightUnload()
                        except:
                            self.__LINK["errorDisplay"]("Failed to run unload function when closing menu",sys.exc_info())
                        self.__active = -1
                    if (type(ent) == bool or mouse[3]) and self.__activeDrag == -1: #Not inside one, must be trying to scroll
                        if not insideSelect:
                            self.__mouseStart = [mouse[1]+0,mouse[2]+0]
                            self.__scrolling = True
                    elif mouse[4]: #Open a context menu on the entity
                        if self.__active !=-1: #Unload the last context menu if it has allredey been opened
                            try:
                                self.__ents[self.__active].rightUnload()
                            except:
                                self.__LINK["errorDisplay"]("Failed to run unload function when closing menu",sys.exc_info())
                        self.__active = ent + 0
                        self.__LINK["log"]("Opening context/options menu on entitiy "+str(self.__ents[ent])+" ID: "+str(self.__ents[ent].ID))
                        try:
                            self.__ents[ent].rightInit(self.__LINK["main"])
                            self.__changes = True
                        except:
                            self.__LINK["errorDisplay"]("Failed to run open menu",sys.exc_info())
                            self.__active = -1
            else:
                self.__scrolling = False
        if self.__active != -1:
            try:
                self.__ents[self.__active].rightLoop(mouse,kBuf)
            except:
                self.__LINK["errorDisplay"]("Failed to run event loop on menu",sys.exc_info())
                self.__active = -1
        if self.__scrolling: #User is scrolling
            self.__scroll[0]-=mouse[1]-self.__mouseStart[0]
            self.__scroll[1]-=mouse[2]-self.__mouseStart[1]
            self.__mouseStart = [mouse[1]+0,mouse[2]+0]
        for event in kBuf: #Keyboard event loop
            if event.type == pygame.KEYDOWN:
                if event.key == self.__LINK["controll"]["resetScroll"] and self.__active == -1: #Shortcut key to reset scroll position
                    self.FileMenuReset()
            if event.type == 6 and not insideSelect: #Scrollwheel
                siz = [self.__scroll[0]*self.__zoom,self.__scroll[1]*self.__zoom,self.__zoom+0]
                if event.button == 4: #Mouse wheel up
                    self.__zoom *= ZOOM_SPEED
                    if self.__zoom > 3:
                        self.__zoom = 3
                    else:
                        self.__scroll[0] = ((self.__scroll[0]+mouse[1])*ZOOM_SPEED) - mouse[1]
                        self.__scroll[1] = ((self.__scroll[1]+mouse[2])*ZOOM_SPEED) - mouse[2]
                elif event.button == 5: #Mouse wheel down
                    self.__zoom /= ZOOM_SPEED
                    self.__scroll[0] = ((self.__scroll[0]+mouse[1])/ZOOM_SPEED) - mouse[1]
                    self.__scroll[1] = ((self.__scroll[1]+mouse[2])/ZOOM_SPEED) - mouse[2]
                    if self.__zoom<0.2:
                        self.__zoom = 0.2
        if self.__click != mouse[0]: #Mouse click was changed
            self.__click = mouse[0] == True
            if mouse[0]: #Mouse down
                if self.__action[0] != -1:
                    if self.__action[0] == 1: #Add new entity
                        for a in self.__ents: #Check all objects for colosions
                            a.editMove(self.__ents)
                        if self.__active != -1:
                            self.__ents[self.__active].rightUnload()
                        self.__active = self.__ents.index(self.__action[1][0])
                        self.__action[1][0].rightInit(self.__LINK["main"])
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
                elif outside: #Detect if the user is trying to drag anouther entity around
                    mPos = [(mouse[1]+self.__scroll[0])/self.__zoom,(mouse[2]+self.__scroll[1])/self.__zoom] #Mouse position local to entity positions
                    itm = self.findEnt(mPos[0],mPos[1])
                    if (itm != self.__active or type(itm)==bool) and self.__active != -1:
                        try:
                            self.__ents[self.__active].rightUnload()
                        except:
                            self.__LINK["errorDisplay"]("Failed to run unload function when closing menu",sys.exc_info())
                        self.__active = -1
                    self.__roomScale = False
                    if type(itm) == int: #Found an entity
                        self.__changes = True
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
    def FileMenuReset(self,*args): #Reset scroll position
        sx,sy = self.__LINK["main"].get_size() #Get the size of the screen
        self.__scroll = [-sx/2,-sy/2]
        self.FileMenuEnd()
    def saveAs(self,name): #Saves a file as a name
        Build = [self.__GlobalID+0]
        errs = []
        hasEntrance = False
        for a in self.__ents:
            try:
                Build.append(a.SaveFile())
            except:
                self.__LINK["errorDisplay"]("Error when saving entitiy ",a,sys.exc_info())
            try:
                err = a.giveError(self.__ents)
            except:
                self.__LINK["errorDisplay"]("Error when gathering entitiy errors in entitiy ",a,sys.exc_info())
                err = "Script error"
            if type(err) == str and not err in errs:
                errs.append(err+"")
            if type(a)==self.getEnt("airlock"):
                if a.settings["default"]:
                    hasEntrance = True
        if not hasEntrance:
            errs.append("No default airlock")
        try:
            file = open("maps/"+name,"wb")
        except:
            self.__LINK["errorDisplay"]("Failed to save file!",sys.exc_info())
            return 0
        file.write(pickle.dumps(Build))
        file.close()
        self.__LINK["log"]("Saved file "+name+" sucsessfuly!")
        if self.__FileMenu:
            if len(errs)!=0:
                self.__WarnLabel.text = "Saved but with errors: "+str(errs)
                self.__WarnLabel.flickr()
            else:
                self.__WarnLabel.text = "Saved file sucsessfuly"
            for a in self.__ents: #Check all objects for colosions
                a.editMove(self.__ents)
    def openAs(self,name): #Opens a file as a name
        try:
            file = open("maps/"+name,"rb")
        except:
            self.__LINK["errorDisplay"]("Failed to open file!",sys.exc_info())
            return 0
        try:
            data = pickle.loads(file.read())
        except:
            self.__LINK["errorDisplay"]("Failed to pickle load file")
            file.close()
            return 0
        self.__GlobalID = data[0]+0
        self.__ents = []
        idRef = {}
        for a in data[1:]:
            self.__ents.append(self.getEnt(a[0])(a[2][0],a[2][1],self.__LINK,a[1]+0))
            idRef[a[1]+0] = self.__ents[-1]
        for i,a in enumerate(data[1:]):
            try:
                self.__ents[i].LoadFile(a,idRef)
            except:
                self.__LINK["errorDisplay"]("Error when loading entity ",a,sys.exc_info())
        self.__renderFunc.ents = self.__ents #Make sure the rendering class gets updates from this one through a pointer
        file.close()
        self.__LINK["log"]("Opened file sucsessfuly!")
        if self.__FileMenu:
            self.__WarnLabel.text = "Opened file sucsessfuly"
        for a in self.__ents: #Check all objects for colosions
            a.editMove(self.__ents)
        self.__changes = False
    def FileMenuEnd(self,*args): #End the file menu
        self.__LoadButton = None
        self.__SaveButton = None
        self.__BackButton = None
        self.__ResetButton = None
        self.__MenuButton = None
        self.__NameInput = None
        self.__MapSelect = None
        self.__WarnLabel = None
        self.__MapDump = []
        self.__FileMenu = False
        self.__LINK["log"]("Closed file menu")
    def SaveFileButton(self,*args):
        text = self.__NameInput.text
        if "\\" in text or "/" in text:
            self.__WarnLabel.text = "File name contains invalid characters!"
            self.__WarnLabel.flickr()
            text = ""
        else:
            if "." in text:
                if text.count(".")!=1:
                    self.__WarnLabel.text = "Invalid number of dots ('.')"
                    self.__WarnLabel.flickr()
                    text = ""
            elif len(text)==0:
                self.__WarnLabel.text = "No name was entered"
                self.__WarnLabel.flickr()
                text = ""
            else:
                text = text+".map"
        if len(text)!=0:
            if text in self.__LINK["maps"]:
                self.__openDialog("The file already exists, overwrite?",self.__dialogSave)
            else:
                try:
                    self.saveAs(text)
                    self.__changes = False
                except:
                    self.__LINK["errorDisplay"]("Failed to run save function",sys.exc_info())
                if not text in self.__LINK["maps"]:
                    self.__LINK["maps"].append(text+"")
    def __dialogSave(self,*ev): #Dialog is will call this function if the file will be overwritten
        try:
            self.saveAs(self.__NameInput.text)
        except:
            self.__LINK["errorDisplay"]("Failed to run save function",sys.exc_info())
        self.__closeDialog()
    def __dialogOpen(self,*ev): #Dialog will call this function if the map will be disregarded when opeing anouther
        try:
            self.openAs(self.__NameInput.text)
        except:
            self.__LINK["errorDisplay"]("Failed to run open function",sys.exc_info())
        self.__closeDialog()
        self.FileMenuEnd()
    def __openDialog(self,quest,call,width=400): #Opens the overwrite dialog
        self.__dialog = []
        self.__dialog.append(pygame.Surface((width,80)))
        self.__dialog.append(self.__LINK["screenLib"].Label(0,0,self.__LINK,quest))
        self.__dialog.append(self.__LINK["screenLib"].Button(10,40,self.__LINK,"Yes",call))
        self.__dialog.append(self.__LINK["screenLib"].Button(width-50,40,self.__LINK,"No",self.__closeDialog))
    def __closeDialog(self,*ev): #Closes the dialog
        self.__dialog = []
    def OpenFileButton(self,*args):
        text = self.__NameInput.text
        if "\\" in text or "/" in text:
            self.__WarnLabel.text = "File name contains invalid characters!"
            self.__WarnLabel.flickr()
            text = ""
        else:
            if "." in text:
                if text.count(".")!=1:
                    self.__WarnLabel.text = "Invalid number of dots ('.')"
                    self.__WarnLabel.flickr()
                    text = ""
            else:
                text = text+".map"
        if len(text)!=0:
            if not text in self.__LINK["maps"]:
                self.__WarnLabel.text = "Map does not exist, if you dragged it in then restart the game!"
                self.__WarnLabel.flickr()
                text=""
        if len(text)!=0:
            if self.__changes: #Changes detected
                self.__openDialog("Disregard changes on current map?",self.__dialogOpen)
            else:
                try:
                    self.openAs(text)
                except:
                    self.__LINK["errorDisplay"]("Failed to run open function",sys.exc_info())
                self.FileMenuEnd()
    def __BackToMenu(self,*ev):
        self.__LINK["loadScreen"]("mainMenu")
    def FileMenuInit(self,*args): #Initialize file menu
        if self.__active != -1:
            self.__ents[self.__active].rightUnload()
            self.__active = -1
        self.__FileMenu = True
        self.__LoadButton = self.__LINK["screenLib"].Button(10,10,self.__LINK,"Open",self.OpenFileButton)
        self.__SaveButton = self.__LINK["screenLib"].Button(80,10,self.__LINK,"Save",self.SaveFileButton)
        self.__ResetButton = self.__LINK["screenLib"].Button(150,10,self.__LINK,"Reset scroll position",self.FileMenuReset)
        self.__BackButton = self.__LINK["screenLib"].Button(400,10,self.__LINK,"Back to editor",self.FileMenuEnd)
        self.__MenuButton = self.__LINK["screenLib"].Button(570,10,self.__LINK,"Back to main menu",self.__BackToMenu)
        self.__NameInput = self.__LINK["screenLib"].TextEntry(10,50,self.__LINK,self.__reslution[0]-25,False,"File name")
        self.__MapSelect = self.__LINK["screenLib"].Listbox(10,130,self.__LINK,[self.__reslution[0]-25,self.__reslution[1]-145])
        self.__WarnLabel = self.__LINK["screenLib"].Label(10,90,self.__LINK,"File menu")
        self.__MapDump = []
        for a in self.__LINK["maps"]:
            self.__MapDump.append(DumpButton(self,a))
            self.__MapSelect.addItem(self.__LINK["screenLib"].Button,a,self.__MapDump[-1].call2)
        self.__LINK["log"]("Opened file menu")
    def renderFileMenu(self,surf): #Render the file menu
        self.__LoadButton.render(self.__LoadButton.pos[0],self.__LoadButton.pos[1],1,1,surf)
        self.__SaveButton.render(self.__SaveButton.pos[0],self.__SaveButton.pos[1],1,1,surf)
        self.__NameInput.render(self.__NameInput.pos[0],self.__NameInput.pos[1],1,1,surf)
        self.__ResetButton.render(self.__ResetButton.pos[0],self.__ResetButton.pos[1],1,1,surf)
        self.__MapSelect.render(self.__MapSelect.pos[0],self.__MapSelect.pos[1],1,1,surf)
        self.__BackButton.render(self.__BackButton.pos[0],self.__BackButton.pos[1],1,1,surf)
        self.__MenuButton.render(self.__MenuButton.pos[0],self.__MenuButton.pos[1],1,1,surf)
        self.__WarnLabel.render(self.__WarnLabel.pos[0],self.__WarnLabel.pos[1],1,1,surf)
        if len(self.__dialog)!=0:
            self.__dialog[0].fill((50,50,50))
            for a in self.__dialog[1:]:
                a.render(a.pos[0],a.pos[1],1,1,self.__dialog[0])
            sx,sy = self.__dialog[0].get_size()
            sx2,sy2 = surf.get_size()
            surf.blit(self.__dialog[0],(int((sx2/2)-(sx/2)),int((sy2/2)-(sy/2))))
    def render(self,surf=None): #Renders everything
        if surf is None:
            surf = self.__LINK["main"]
        if self.__FileMenu:
            self.renderFileMenu(surf)
            return 0
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
        if self.__Hinting == 0: #Render file menu hint
            self.renderHint(surf,"This is the file menu, click it to save, open, exit and reset scrolling position",[self.__fileMenu.pos[0]+60,self.__fileMenu.pos[1]+20])
        elif self.__Hinting == 1: #Render entity adding hint
            self.renderHint(surf,"You can add new entities using this menu here, click on an entity and click where you want it",[self.__entSelect.pos[0]+120,self.__entSelect.pos[1]+120])
        elif self.__Hinting == 2: #Render controlls hint
            self.renderHint(surf,"You can move and resize objects using the left mouse button. \nRight click to open the context/options menu of an entity, to close simply click (mouse 1) on another entity. \nHold mouse 2 (right click) to scroll around. \nPress backspace to reset scroll position.",[self.__reslution[0]/3,180])
        elif self.__Hinting == 3: #Hints hint
            self.renderHint(surf,"Most objects you spawn will want to be inside of rooms. Objects that don't are rooms, doors, and airlocks. Entities that encounter errors will be highlighted RED \nWhen spawning entities for the first time, you will get a hint box. To close this simply open the objects context/option menu by right clicking on it.",[self.__reslution[0]/3,240])
