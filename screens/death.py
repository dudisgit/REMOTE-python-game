import pygame, time

class Main:
    def __init__(self,LINK,reason=0):
        #Death reasons:
        #0: Unknown
        #1: Out of fuel
        #2: All drones are dead
        self.__LINK = LINK
        self.__reason = reason #Reason for death
        self.__title = "GAME OVER" #Title text
        self.__titleAdd = 0 #Title text seeing
        self.__titleTime = time.time()+0.1 #Title timing 
        self.__boxAdd = 0 #Box size adding
        self.__boxTime = time.time()+0.1 #Box timing
        if reason==0: #Unkown death
            self.__text = "Unknown cause of stranding"
        elif reason==1: #No fuel left
            self.__text = "Ran out of fuel"
        elif reason==2: #No drones
            self.__text = "No drones left to scavenge ships"
        if self.__LINK["multi"]==1: #Game is running as a client
            self.__LINK["cli"].close()
            self.__LINK["multi"] = 0
    def loop(self,mouse,kBuf,lag):
        if time.time()>self.__titleTime and not self.__titleTime==-1: #Increase the text count on the title
            self.__titleAdd+=1
            if self.__titleAdd==len(self.__title): #Finished title
                self.__titleTime = -1
            else:
                self.__titleTime = time.time()+0.1
        elif self.__titleTime==-1 and not self.__boxTime==-1 and time.time()>self.__boxTime: #Increase box size on reason
            self.__boxAdd += 1
            if self.__boxAdd>20: #Finished box
                self.__boxTime = -1
            else:
                self.__boxTime = time.time()+0.05
        if not self.__LINK["controller"] is None:
            if self.__LINK["controller"].selectChange():
                if self.__LINK["controller"].select():
                    self.__LINK["loadScreen"]("mainMenu")
        for event in kBuf: #Go through keyboard events
            if event.type == pygame.KEYDOWN: #User pressed a button
                if event.key == pygame.K_RETURN: #Return key was pressed
                    self.__LINK["loadScreen"]("mainMenu")
    def render(self,surf=None): #Render screen
        if surf is None:
            surf = self.__LINK["main"]
        sx,sy = surf.get_size()
        if ((time.time()-int(time.time()))*4)%1>0.5: #Render title normaly
            surf.blit(self.__LINK["font128"].render(self.__title[:self.__titleAdd],16,(255,255,255)),[(sx/2)-300,100])
        else: #Render title with underscore at end
            surf.blit(self.__LINK["font128"].render(self.__title[:self.__titleAdd]+"_",16,(255,255,255)),[(sx/2)-300,100])
        if self.__titleTime==-1: #Finished title
            surf.blit(self.__LINK["font42"].render("Reason",16,(255,255,0)),[(sx/2)-50,230])
            if self.__boxTime==-1: #Finished all animations
                pygame.draw.rect(surf,(0,0,0),[(sx/2)-300,300,self.__boxAdd*30,80])
                pygame.draw.rect(surf,(255,255,0),[(sx/2)-300,300,self.__boxAdd*30,80],4)
                tex = self.__LINK["font42"].render(self.__text,16,(255,255,255))
                sx2,sy2 = tex.get_size()
                surf.blit(tex,[(sx/2)-(sx2/2),320]) #Render reason
                surf.blit(self.__LINK["font42"].render("Overall score: "+str(self.__LINK["shipData"]["maxScore"]),16,(255,255,0)),[(sx/2)-125,400])
                if self.__LINK["controller"] is None:
                    surf.blit(self.__LINK["font42"].render("Press return to continue",16,(255,255,0)),[(sx/2)-180,450])
                else:
                    A = self.__LINK["controller"].keyName["select"]
                    surf.blit(self.__LINK["font42"].render("Press "+A+" to continue",16,(255,255,0)),[(sx/2)-180,450])
            else: #Draw reason box building.
                pygame.draw.rect(surf,(0,255,0),[(sx/2)-350,300,self.__boxAdd*30,80])