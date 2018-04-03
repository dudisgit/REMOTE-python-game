import pygame, pickle

class Main:
    def __init__(self,LINK):
        self.__LINK = LINK
        self.__opts = ["Exit to main menu","Options","Back"]
        self.__sel = 0
        self.__screen = 0
        self.__allowQuick = False
        self.exit = False
        #0: Main escape menu
        #1: Options (limited)
    def resized(self):
        pass
    def saveSettings(self): #Save user settings
        with open("settings.sav","wb") as file:
            file.write(pickle.dumps([self.__LINK["showFPS"],self.__LINK["particles"],self.__LINK["floorScrap"],self.__LINK["popView"],self.__LINK["simpleModels"],self.__LINK["backgroundStatic"],self.__LINK["hints"],self.__LINK["threading"],self.__LINK["menuFade"]]))
    def loop(self,mouse,kBuf,lag):
        if not self.__LINK["controller"] is None:
            if self.__LINK["controller"].getMenuUpChange():
                if self.__LINK["controller"].getMenuUp():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_UP}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_UP}))
            if self.__LINK["controller"].getMenuDownChange():
                if self.__LINK["controller"].getMenuDown():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_DOWN}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_DOWN}))
            if self.__LINK["controller"].getMenuLeftChange():
                if self.__LINK["controller"].getMenuLeft():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_LEFT}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_LEFT}))
            if self.__LINK["controller"].getMenuRightChange():
                if self.__LINK["controller"].getMenuRight():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_RIGHT}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_RIGHT}))
            if self.__LINK["controller"].selectChange():
                if self.__LINK["controller"].select():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_RETURN}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_RETURN}))
            if self.__LINK["controller"].getMenuChange():
                if self.__LINK["controller"].getMenu():
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,{"key":pygame.K_ESCAPE}))
                else:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP,{"key":pygame.K_ESCAPE}))
            if self.__LINK["controller"].backChange():
                if self.__LINK["controller"].back():
                    self.__sel = 1
                    self.__screen = 0
                    self.__opts = ["Exit to main menu","Options","Back"]
        for event in kBuf:
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    self.__allowQuick = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    self.__sel+=1
                    if self.__sel>=len(self.__opts):
                        self.__sel = 0
                elif event.key == pygame.K_UP:
                    self.__sel-=1
                    if self.__sel<0:
                        self.__sel = len(self.__opts)-1
                elif event.key == pygame.K_ESCAPE:
                    self.exit = self.__allowQuick == True
                elif event.key == pygame.K_RETURN:
                    if self.__screen==0:
                        if self.__sel==0: #Exit to main menu
                            self.exit = True
                            if self.__LINK["multi"]==1:
                                self.__LINK["cli"].close()
                            self.__LINK["loadScreen"]("mainMenu")
                        elif self.__sel==1: #Enter options
                            self.__opts = [[self.__LINK["showFPS"],"FPS counter"],[self.__LINK["particles"],"Particles"],[self.__LINK["floorScrap"],"Floor scrap"],
                                           [self.__LINK["popView"],"pop view (make rooms pop into view, reduced CPU)"],[self.__LINK["viewDistort"],"View distortion effects"],
                                           [self.__LINK["hints"],"Hints"],[self.__LINK["backgroundStatic"],"Background static"],"Back"]
                            self.__screen = 1
                        elif self.__sel==2: #Back to game
                            self.exit = True
                    elif self.__screen==1: #In options menu
                        if type(self.__opts[self.__sel])==list:
                            self.__opts[self.__sel][0] = not self.__opts[self.__sel][0]
                        if self.__sel==0: #Show FPS
                            self.__LINK["showFPS"] = self.__opts[0][0] == True
                        elif self.__sel==1: #Enable particles
                            self.__LINK["particles"] = self.__opts[1][0] == True
                        elif self.__sel==2: #Floor scrap
                            self.__LINK["floorScrap"] = self.__opts[2][0] == True
                        elif self.__sel==3: #popView
                            self.__LINK["popView"] = self.__opts[3][0] == True
                        elif self.__sel==4: #View distortion
                            self.__LINK["viewDistort"] = self.__opts[4][0] == True
                        elif self.__sel==5: #Enable hints
                            self.__LINK["hints"] = self.__opts[5][0] == True
                        elif self.__sel==6: #Background static
                            self.__LINK["backgroundStatic"] = self.__opts[6][0] == True
                        elif self.__sel==7: #Back
                            self.__screen = 0
                            self.__sel = 1
                            self.saveSettings()
                            self.__opts = ["Exit to main menu","Options","Back"]
    def render(self,surf=None):
        if surf is None:
            surf = self.__LINK["main"]
        sx,sy = surf.get_size()
        pygame.draw.rect(surf,(0,0,0),[30,30,sx-60,sy-60])
        pygame.draw.rect(surf,(0,255,0),[30,30,sx-60,sy-60],4)
        titleText = self.__LINK["font42"].render("Escape menu",16,(0,255,0))
        surf.blit(titleText,(40,40))
        bufs = []
        scroll = 0
        if 80+(len(self.__opts)*30)>sy-50: #Too many options to display on screen
            if 80+(self.__sel*30)>sy-50: #Selecting option is going off the screen
                scroll = int(((80+(self.__sel*30))-(sy-50))/30) #Start at a few options before selection
        mWid = 0
        for a in self.__opts[scroll:]:
            if type(a)==list:
                bufs.append(self.__LINK["font24"].render(a[1],16,(50,200,50)))            
                if bufs[-1].get_width()+30>mWid:
                    mWid = bufs[-1].get_width()+30
            else:
                bufs.append(self.__LINK["font24"].render(a,16,(50,200,50)))            
                if bufs[-1].get_width()>mWid:
                    mWid = bufs[-1].get_width()+0
        for i,a in enumerate(self.__opts[scroll:]):
            if 90+(i*30)>sy-30:
                break
            if self.__sel-scroll == i:
                pygame.draw.rect(surf,(0,255,0),[45,80+(i*30),mWid+2,22],2)
            if type(a)==list: #Rendered option is a boolean option
                col = (255,0,255)
                if a[0]:
                    col = (0,255,0)
                else:
                    col = (255,0,0)
                pygame.draw.rect(surf,col,[50,80+(i*30)+6,25,25])
                surf.blit(bufs[i+scroll],(80,80+(i*30)))
            else:
                surf.blit(bufs[i+scroll],(50,80+(i*30)))
