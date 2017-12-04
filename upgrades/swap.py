import upgrades.base as base
import pygame, time, math, random

WIDTH = 180
HEIGHT = 110

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "swap"
        self.displayName = "DONT SPAWN" #Name of the upgrade (displayed)
        self.damage = 0 #Damage to the upgrade.
        self.caller = ["swap"] #Commands this upgrade accepts
        self.__activeDrone = None #Drone we are currently swapping with
        self.__controllerChange = {"x":False,"y":False,"b":False,"a":False,"sel":False,"start":False,"lt":False,"rt":False,"up":False,"down":False,"left":False,"right":False} #Used to detect changed in controller button sates
        self.__select = [0,0,-1] #Selecting box
        self.__usrCall = None #Used who called this command (multiplayer only)
        self.__intro = 0 #Introduction effect
        self.hitFunction = self.hitDrone #Function to call when this upgrade is moved
    def commandAllowed(self,com): #Returns true if this command is allowed in the upgrade
        Droom = self.drone.findPosition() #Find the drones position
        if Droom==-1: #Drone is not in anything
            return False
        elif not self.__activeDrone is None: #Upgrade allredey in use (this will only be called in multiplayer)
            return "Allredey swapping with anouther drone"
        else: #Check if there are any drones in the room
            Ents = Droom.EntitiesInside()
            DroneObject = self.getEnt("drone")
            for a in Ents: #Find any drones in the room with this one
                if type(a)==DroneObject and a!=self.drone:
                    return True
            return "No drone in room to swap with"
    def controller_key(self,typ): #Returns wether a button is pressed
        if self.LINK["controller"] is None:
            return False
        if typ=="up": #Up button
            return self.LINK["controller"].get_axis(1)<-0.5
        elif typ=="down": #Down button
            return self.LINK["controller"].get_axis(1)>0.5
        elif typ=="left": #Left button
            return self.LINK["controller"].get_axis(0)<-0.5
        elif typ=="right": #Right button
            return self.LINK["controller"].get_axis(0)>0.5
        elif typ=="x": #X button
            return self.LINK["controller"].get_button(0)
        elif typ=="y": #Y button
            return self.LINK["controller"].get_button(3)
        elif typ=="b": #B button
            return self.LINK["controller"].get_button(2)
        elif typ=="a": #A button
            return self.LINK["controller"].get_button(1)
        elif typ=="lt": #Left trigger
            return self.LINK["controller"].get_button(4)
        elif typ=="rt": #Right trigger
            return self.LINK["controller"].get_button(5)
        elif typ=="sel": #Select button
            return self.LINK["controller"].get_button(8)
        elif typ=="start": #Start button
            return self.LINK["controller"].get_button(9)
        return False
    def force_loop(self,mouse,kBuf,lag): #Used to loop controll
        if self.__intro>0:
            self.__intro-=lag
            if self.__intro<0:
                self.__intro=0
        if self.__controllerChange["up"]!=self.controller_key("up"):
            self.__controllerChange["up"] = self.controller_key("up")
            if self.controller_key("up"):
                if self.__select[2]!=-2 and self.__select[0]==1: #Both upgrade boxes are full, swap mode
                    self.__select[2]-=1
                    if self.__select[2]<0:
                        self.__select[2] = len(self.__activeDrone.upgrades)-1
                else: #Use a normal cursor
                    self.__select[1]-=1
                    if self.__select[1]<0:
                        if self.__select[0]==0:
                            self.__select[1] = len(self.drone.upgrades)-1
                        else:
                            self.__select[1] = len(self.__activeDrone.upgrades)-1
        if self.__controllerChange["down"]!=self.controller_key("down"):
            self.__controllerChange["down"] = self.controller_key("down")
            if self.controller_key("down"):
                if self.__select[2]!=-2 and self.__select[0]==1: #Both upgrade boxes are full, swap mode
                    self.__select[2]+=1
                    if self.__select[2]>=len(self.__activeDrone.upgrades):
                            self.__select[2] = 0
                else: #Use a normal cursor
                    self.__select[1]+=1
                    if self.__select[0]==0:
                        if self.__select[1]>=len(self.drone.upgrades):
                            self.__select[1] = 0
                    else:
                        if self.__select[1]>=len(self.__activeDrone.upgrades):
                            self.__select[1] = 0
        if self.controller_key("left"):
            self.__select[0] = 0
            while self.__select[1]>=len(self.drone.upgrades):
                self.__select[1] -= 1
        if self.controller_key("right"):
            self.__select[0] = 1
            while self.__select[1]>=len(self.__activeDrone.upgrades):
                self.__select[1] -= 1
        if self.controller_key("b"):
            self.LINK["force"].remove([self,self.force_loop,self.force_render])
            self.__activeDrone = None
        RET = False
        if self.controller_key("x")!=self.__controllerChange["x"]:
            self.__controllerChange["x"] = self.controller_key("x")
            if self.controller_key("x"):
                print("swap")
                RET = True
        for event in kBuf: #Process keyboard events
            if event.type == pygame.KEYDOWN: #Key was pressed down
                if event.key == self.LINK["controll"]["escape"]: #Exit out of swap menu
                    self.LINK["force"].remove([self,self.force_loop,self.force_render])
                    self.__activeDrone = None
                elif event.key == self.LINK["controll"]["up"]: #Up arrow
                    if self.__select[2]!=-2 and self.__select[0]==1: #Both upgrade boxes are full, swap mode
                        self.__select[2]-=1
                        if self.__select[2]<0:
                            self.__select[2] = len(self.__activeDrone.upgrades)-1
                    else: #Use a normal cursor
                        self.__select[1]-=1
                        if self.__select[1]<0:
                            if self.__select[0]==0:
                                self.__select[1] = len(self.drone.upgrades)-1
                            else:
                                self.__select[1] = len(self.__activeDrone.upgrades)-1
                elif event.key == self.LINK["controll"]["down"]: #Down arrow
                    if self.__select[2]!=-2 and self.__select[0]==1: #Both upgrade boxes are full, swap mode
                        self.__select[2]+=1
                        if self.__select[2]>=len(self.__activeDrone.upgrades):
                                self.__select[2] = 0
                    else: #Use a normal cursor
                        self.__select[1]+=1
                        if self.__select[0]==0:
                            if self.__select[1]>=len(self.drone.upgrades):
                                self.__select[1] = 0
                        else:
                            if self.__select[1]>=len(self.__activeDrone.upgrades):
                                self.__select[1] = 0
                elif event.key == self.LINK["controll"]["left"]: #Switch to the left hand side
                    self.__select[0] = 0
                    while self.__select[1]>=len(self.drone.upgrades):
                        self.__select[1] -= 1
                elif event.key == self.LINK["controll"]["right"] or self.controller_key("right"): #Switch to the right hand side
                    self.__select[0] = 1
                    while self.__select[1]>=len(self.__activeDrone.upgrades):
                        self.__select[1] -= 1
                elif event.key == pygame.K_RETURN: #Swap an upgrade, (return key pressed)
                    RET = True
        if RET:
            if self.__select[0]==0: #Cursor on the left hand side
                if self.__select[1]>=0 and self.__select[1]<len(self.drone.upgrades): #Selecting cursor is in range
                    if len(self.__activeDrone.upgrades)!=len(self.__activeDrone.settings["upgrades"]): #Right hand side is not full
                        if self.LINK["multi"]==1: #Is a client
                            self.LINK["cli"].sendTrigger("mvu",self.drone.ID,self.__activeDrone.ID,self.__select[1]) #Send a trigger to the server to move the upgrade
                        else:
                            self.moveTo(self.drone.upgrades.pop(self.__select[1]),self.__activeDrone) #Move the upgrade
            else: #Cursor is on the right hand side
                if self.__select[1]>=0 and self.__select[1]<len(self.__activeDrone.upgrades): #Selecting cursor is in range
                    if len(self.drone.upgrades)!=len(self.drone.settings["upgrades"]): #Left hand side is not full
                        if self.LINK["multi"]==1: #Is a client
                            self.LINK["cli"].sendTrigger("mvu",self.__activeDrone.ID,self.drone.ID,self.__select[1]) #Send a trigger to the server to move the upgrade
                        else:
                            self.moveTo(self.__activeDrone.upgrades.pop(self.__select[1]),self.drone) #Move the upgrade
            if self.__select[2]!=-2: #Swap the upgrades because both sides are full
                if self.__select[1]>=0 and self.__select[1]<len(self.drone.upgrades) and self.__select[2]>=0 and self.__select[2]<len(self.__activeDrone.upgrades): #Everything in range
                    if self.LINK["multi"]==1: #Is a client
                        self.LINK["cli"].sendTrigger("sup",self.drone.ID,self.__activeDrone.ID,self.__select[1],self.__select[2]) #Send a trigger to the server to swap the upgrades
                    else:
                        tmp = self.drone.upgrades.pop(self.__select[1])
                        self.moveTo(self.__activeDrone.upgrades.pop(self.__select[2]),self.drone,self.__select[1])
                        self.moveTo(tmp,self.__activeDrone,self.__select[2])
    def moveTo(self,Upg,Dr,sp=-1): #Moves an upgrade to a drone
        if sp==-1: #Add to the end
            Dr.upgrades.append(Upg)
        else: #Add to a specific place in the list
            Dr.upgrades.insert(sp,Upg)
        Upg.moved(Dr) #Call the function telling the upgrade it was moved (used to disable any jobs it is doing while its being swapped)
        Upg.drone = Dr #Set the upgrades new drone
        self.drone.unloadUpgrades() #Used for saving
        if self.__activeDrone is None: #If the upgrade is not currently active then reload the upgrades from the drone passed in paramiters
            Dr.unloadUpgrades()
            #This is normaly to fix bugs with client and server bugs when executing this function
        else:
            self.__activeDrone.unloadUpgrades() #Used for saving
    def force_render(self,surf,size): #Renders the swap menu
        pygame.draw.rect(surf,(0,0,0),[int(size[0]/2)-WIDTH,size[1]-HEIGHT-20,WIDTH*2,HEIGHT])
        pygame.draw.rect(surf,(0,255,0),[int(size[0]/2)-WIDTH,size[1]-HEIGHT-20,WIDTH*2,HEIGHT],2)
        X = int(size[0]/2)-WIDTH #X position of the left side of the window
        Y = size[1]-HEIGHT-20 #Y position of the top side of the window
        X += random.randint(-round(self.__intro),round(self.__intro))
        if self.__select[0]==0: #Selecting cursor is on the left hand side
            pygame.draw.rect(surf,(0,255,0),[X+2,Y+2,WIDTH-3,HEIGHT-3],5)
        else: #Selecting cursor is on the right hand side
            pygame.draw.rect(surf,(0,255,0),[X+WIDTH+2,Y+2,WIDTH-3,HEIGHT-3],5)
        surf.blit(self.LINK["font24"].render(self.drone.settings["name"]+" (YOU)",16,(255,255,255)),[X+2,Y-20])
        surf.blit(self.LINK["font24"].render(self.__activeDrone.settings["name"],16,(255,255,255)),[X+WIDTH+2,Y-20])
        perc = (time.time()-int(time.time()))*2 #Flash effect
        if perc>1:
            perc = 2-perc
        for i in range(len(self.drone.settings["upgrades"])): #Show all drone 1's upgrades
            if i>=len(self.drone.upgrades): #Empty upgrade slot
                surf.blit(self.LINK["font24"].render("...",16,(70,70,70)),[X+10,Y+10+(i*24)])
            else: #Display upgrade name with correct colour
                a = self.drone.upgrades[i]
                if a.damage==0: #Working fine
                    if a.used: #Has been used
                        col = (0,255,0)
                    else: #Brand new
                        col = (255,255,255)
                elif a.damage==1: #Upgrade is damaged
                    col = (255,255,0)
                elif a.damage==2: #Upgrade is damaged beyond repair
                    col = (255,0,0)
                else: #Error colour
                    col = (255,0,255)
                if (self.__select[0]==0 or self.__select[2]!=-2) and self.__select[1]==i: #Draw cursor box
                    col = (int(col[0]*perc),int(col[1]*perc),int(col[2]*perc))
                    pygame.draw.rect(surf,(0,int(128*perc)+128,0),[X+7,Y+10+(i*24),WIDTH-14,20],4)
                surf.blit(self.LINK["font24"].render(a.name,16,col),[X+10,Y+10+(i*24)])
        for i in range(len(self.__activeDrone.settings["upgrades"])): #Show all if drone 2's upgrades
            if i>=len(self.__activeDrone.upgrades): #Empty upgrade slot
                surf.blit(self.LINK["font24"].render("...",16,(70,70,70)),[X+WIDTH+20,Y+10+(i*24)])
            else: #Display upgrade name with correct colour
                a = self.__activeDrone.upgrades[i]
                if a.damage==0: #Working fine
                    if a.used: #Has been used
                        col = (0,255,0)
                    else: #Brand new
                        col = (255,255,255)
                elif a.damage==1: #Upgrade is damaged
                    col = (255,255,0)
                elif a.damage==2: #Upgrade is damaged beyond repair
                    col = (255,0,0)
                else: #Error colour
                    col = (255,0,255)
                if (self.__select[0]==1 and self.__select[1]==i and self.__select[2]==-2) or self.__select[2]==i: #Show cursor box
                    col = (int(col[0]*perc),int(col[1]*perc),int(col[2]*perc))
                    pygame.draw.rect(surf,(0,int(128*perc)+128,0),[X+WIDTH+7,Y+10+(i*24),WIDTH-14,20],4)
                surf.blit(self.LINK["font24"].render(a.name,16,col),[X+WIDTH+20,Y+10+(i*24)])
    def clientCall(self,droneID,Index=None,index2=None): #Upgrade was called to work client-side from server
        if droneID=="S": # Stop this upgrade (client-side)
            if [self,self.force_loop,self.force_render] in self.LINK["force"]:
                self.LINK["force"].remove([self,self.force_loop,self.force_render])
                self.__activeDrone = None
        elif not Index is None: #Upgrade was swapped
            if index2 is None: #A single upgrade was moved
                self.moveTo(self.drone.upgrades.pop(Index),self.LINK["IDs"][droneID])
            else: #Two upgrades where swapped
                DRONE_2 = self.LINK["IDs"][droneID]
                upg = self.drone.upgrades.pop(Index)
                DRONE_2.PERM_UPG[0].moveTo(DRONE_2.upgrades.pop(index2),self.drone,Index)
                self.moveTo(upg,DRONE_2,index2)
        else: #Run the upgrade client-side (opens window for interaction)
            self.__activeDrone = self.LINK["IDs"][droneID]
            self.__intro = 10
            self.__controllerChange["x"] = True
            self.__select = [0,0,-2]
            if len(self.__activeDrone.upgrades)==len(self.__activeDrone.settings["upgrades"]) and len(self.drone.upgrades)==len(self.drone.settings["upgrades"]):
                self.__select[2] = 0 #Both upgrade slots on drones are full, entering swap mode.
            self.LINK["force"].append([self,self.force_loop,self.force_render]) #Make this upgrade take controll of the interface
    def hitDrone(self,drOb): #Drone has reached destination
        self.__activeDrone = drOb
        if self.LINK["multi"]==2: #Is a server
            self.__usrCall.sendTrigger("cupg",self.drone.ID,"swap",drOb.ID) #Send a trigger to the client who called this to open their swapping menu
        else: #Is single player
            self.__select = [0,0,-2]
            self.__controllerChange["x"] = True
            if len(self.__activeDrone.upgrades)==len(self.__activeDrone.settings["upgrades"]) and len(self.drone.upgrades)==len(self.drone.settings["upgrades"]):
                self.__select[2] = 0 #Both upgrade slots on drones are full, entering swap mode.
            self.LINK["force"].append([self,self.force_loop,self.force_render]) #Make this upgrade take controll of the interface
    def loop(self,lag): #Event loop on this upgrade
        super().loop(lag)
        if not self.__activeDrone is None:
            dist = math.sqrt( ((self.drone.pos[0]+(self.drone.size[0]/2)-(self.__activeDrone.pos[0]+(self.__activeDrone.size[0]/2)))**2) + 
                    ((self.drone.pos[1]+(self.drone.size[1]/2)-(self.__activeDrone.pos[1]+(self.__activeDrone.size[1]/2)) )**2) ) #Find distance
            if dist>40: #If drone is too far away then disconnect the swap menu
                if self.LINK["multi"]==2: #Is a server
                    self.__usrCall.sendTrigger("cupg",self.drone.ID,"swap","S") #Make the client exit their swapping menu
                else:
                    self.LINK["force"].remove([self,self.force_loop,self.force_render])
                self.__activeDrone = None
    def doCommand(self,com,usrObj=None): #Runs a command on this upgrade (only if sucsessful)
        Droom = self.drone.findPosition()
        Ents = Droom.EntitiesInside()
        DroneObject = self.getEnt("drone")
        Closest = [-1,None] #The closest drone
        for a in Ents: #Find the closest drone to the current drone
            if type(a)==DroneObject and a!=self.drone: #Entity is drone
                dist = math.sqrt( ((self.drone.pos[0]+(self.drone.size[0]/2)-(a.pos[0]+(a.size[0]/2)))**2) + 
                    ((self.drone.pos[1]+(self.drone.size[1]/2)-(a.pos[1]+(a.size[1]/2)) )**2) ) #Find distance
                if Closest[0]==-1 or dist<Closest[0]: #Has distance not been mesured before or distance is less and prevously known
                    Closest[0] = dist+0
                    Closest[1] = a
        self.__usrCall = usrObj
        self.__intro = 10
        self.headTowards(Closest[1],35) #Head towards drone
