#This file is used to render entities
import pygame, time

class Scematic:
    def __init__(self,LINK,edit=False):
        self.__LINK = LINK
        self.__edit = edit #If the view of this scematic is through an editor (e.g. map editor)
        self.ents = [] #Entities to be rendered
        self.__scaleChange = 0 #Used to detect changes in scale
    def render(self,x,y,scale,surf=None):
        if surf is None:
            surf = self.__LINK["main"]
        if scale != self.__scaleChange: #Resize all images if a scale change is detected.
            for a in self.__LINK["content"]:
                siz = list(self.__LINK["content"][a].get_size())
                self.__LINK["cont"][a] = pygame.transform.scale(self.__LINK["content"][a],(int(siz[0]*scale/10.24),int(siz[1]*scale/10.24)))
            self.__scaleChange = scale+0
        for a in self.ents:
            if a.canShow() or self.__edit:
                a.sRender((a.pos[0]*scale)-x,(a.pos[1]*scale)-y,scale,surf,self.__edit)

def drawDevMesh(x,y,scale,surf,LINK): #Used in development only, this will draw a pixel grid for MESH
    for xp in LINK["mesh"]:
        for yp in LINK["mesh"][xp]:
            pygame.draw.rect(surf,(255,0,255),[(xp*scale*125)-x,(yp*scale*125)-y,125*scale,125*scale],1)
            surf.blit(LINK["font24"].render(str(len(LINK["mesh"][xp][yp])),16,(255,0,255)),[(xp*scale*125)-x,(yp*scale*125)-y])
            mid = [(xp*scale*125)-x+(62*scale),(yp*scale*125)-y+(62*scale)]
            for a in LINK["mesh"][xp][yp]:
                pygame.draw.line(surf, (255,0,255), mid, [(a.pos[0]*scale)-x,(a.pos[1]*scale)-y])

class CommandLine: #A command line interface with tabs
    def __init__(self,LINK,drones=3):
        self.__LINK = LINK
        self.__tabs = [] #Variable to store all the tabs inside of.
        #Syntax:
        #0: Tab name
        #1: Contents
        #2: Damage/colour of tab
        #3: Upgrades
        #4: Is being attacked
        for i in range(drones): #Put the tabs for each drone in.
            self.__tabs.append(["DRONE-"+str(i+1),[],i%3,[],False])
        self.__tabs.append(["SCHEMATIC",[],0,[],False]) #For the ship
        self.activeTab = 0
    def settings(self,Tab,dmg=0,attacked=False,upgrades=None): #Change settings of a tab
        if Tab<0 or Tab>=len(self.__tabs): #Check if tab is valid
            self.__LINK["errorDisplay"]("Command line was asked to edit a tab but it doesen't exist.")
        else:
            self.__tabs[Tab][2] = dmg #Apply damage
            self.__tabs[Tab][4] = attacked == True #Being attacked
            if upgrades!=None: #Check if any upgrades need changing
                self.__tabs[Tab][3] = upgrades
    def addLine(self,line,colour,Tab=-1): #Adds a line with its colour to the command line
        if Tab==-1: #Add command to current tab
            if self.activeTab>=0 and self.activeTab<len(self.__tabs): #Check if current tab is valid
                self.__tabs[self.activeTab][1].append([line,colour])
            else: #Display error
                self.__LINK["errorDisplay"]("Active tab in command line is invalid!")
        elif Tab>=0 and Tab<len(self.__tabs): #Check if given tab is valid
            self.__tabs[Tab][1].append([line,colour])
        else: #Display an error
            self.__LINK["errorDisplay"]("Given tab does not exist "+str(Tab))
    def replaceLast(self,line): #Changes the text at the end of the current tab command line
        if self.activeTab>=0 and self.activeTab<len(self.__tabs): #Check if current tab is valid
            self.__tabs[self.activeTab][1][-1][0] = line
        else: #Display an error
            self.__LINK["errorDisplay"]("Editing tab that doesen't exist "+str(self.activeTab))
    def render(self,x,y,sizex,sizey,surf=None): #Render the command line
        if surf is None: #Get the main surface if none is supplied
            surf = self.__LINK["main"]
        col2 = (0,0,0) #Colour for the boarder of the command line
        for i,a in enumerate(self.__tabs): #Render all tabs
            if i==self.activeTab: #Tab is currently selected
                col = (0,200,0)
                #Set boarder colour to tabs damage status
                if a[2]==0:
                    col2 = (200,200,200)
                elif a[2]==1:
                    col2 = (200,200,0)
                else:
                    col2 = (200,0,0)
            elif a[2]==0: #Normal
                col = (200,200,200)
            elif a[2]==1: #Damaged
                col = (200,200,0)
            elif a[2]==2: #Dead
                col = (200,0,0)
            else: #Error
                col = (0,0,0)
            pygame.draw.rect(surf,(0,0,0),[x+(i*80),y-19,70,20]) #Draw black rectangle to the box isn't see-through
            pygame.draw.rect(surf,col,[x+(i*80),y-19,70,20],2+(round(time.time()-int(time.time()))*int(a[4])*5)) #Draw border of tab
            surf.blit(self.__LINK["font16"].render(a[0],16,(255,255,255)),(x+(i*80)+3,y-15)) #Draw name of tab
        pygame.draw.rect(surf,(0,0,0),[x,y,sizex,sizey]) #Draw a black rectangle so it isn't see-through
        pygame.draw.rect(surf,col2,[x,y,sizex,sizey],2) #Draw boarder for command line
        if self.activeTab>=0 and self.activeTab<len(self.__tabs): #Render command lines text if the tab is valid
            for i,a in enumerate(self.__tabs[self.activeTab][1][-11:]):
                surf.blit(self.__LINK["font24"].render(a[0],16,a[1]),(x+3,y+1+(i*18)))