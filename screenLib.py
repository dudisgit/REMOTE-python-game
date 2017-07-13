#This file is for custom screen widgets that work with pygame
#This will be used in screens.

import pygame, time, sys

if __name__ == "__main__": #If this module is trying to be ran as the main program then execute the correct script
    import main

class Listbox: #An object that houses a list of other widgets in a scrollbar menu
    def __init__(self,x,y,LINK,reslution=None,surface=None):
        self.pos = [x,y] #Position of the listbox
        if reslution is None: #If no reslution is supplied then use the reslution of the screen
            self.bound = LINK["reslution"] #Reslution of the screen
        else:
            self.bound = reslution #Reslution given
        if surface is None: #If no surface is supplied then use the main and default one.
            self.screen = pygame.Surface(self.bound,0,LINK["main"]) #This surface will contain all the items that are added to the listbox.
        else:
            self.screen = pygame.Surface(self.bound,0,surface) #Comment above ^
        self.objs = [] #Objects inside the listbox
        self.__LINK = LINK
        self.__scroll = Scrollbar(self.pos[0]+self.bound[1]-22,y+2,LINK,self.bound[1]-4) #Scrollbar for scrolling through list
        self.__scroll.size = 0 #Size of the scrollbar
        self.__click = False #To detect changes in the mouse button
        self.__lighten = False #Highlighting the box when the mouse hoveres over.
    def addItem(self,itm,*pars): #Add a new widget to the listbox
        self.objs.append(itm(0,len(self.objs)*35,self.__LINK,*pars)) #Add to the list
        self.__scroll.size = (len(self.objs)+1)*35 #Set the size of the scrollbar.
        return len(self.objs)-1 #Return the index of the object
    def loop(self,mouse,kBuf): #Pretty much an event loop, this gets called frequently and will update the widgets if a mouse event occures
        self.__lighten = mouse[1]>self.pos[0] and mouse[2]>self.pos[1] and mouse[1]<self.pos[0]+self.bound[0] and mouse[2]<self.pos[1]+self.bound[1]
        self.__scroll.loop(mouse,kBuf)
        ms = [mouse[0],mouse[1]-self.pos[0],mouse[2]-self.pos[1]]
        if not self.__lighten:
            ms[1] = 0
            ms[2] = 0
        for a in self.objs:
            a.loop(ms,kBuf)
        if len(self.objs)!=0 and self.__lighten and (len(self.objs)+1)*35>self.bound[1]: #Loop only if the listbox contains items
            for event in kBuf: #Capture keyboard events
                if event.type == 6: #Mouse wheel
                    if event.button==4: #Mouse wheel up
                        self.__scroll.scroll -= 50/((len(self.objs)+1)*35)
                        if self.__scroll.scroll<0:
                            self.__scroll.scroll = 0
                    elif event.button==5: #Mouse wheel down
                        self.__scroll.scroll += 50/((len(self.objs)+1)*35)
                        if self.__scroll.scroll>1:
                            self.__scroll.scroll = 1
        elif (len(self.objs)+1)*35<=self.bound[1]:
            self.__scroll.scroll = 0
    def render(self,x=None,y=None,scalex=None,scaley=None,surf=None): #Render the listbox onto the surface
        if x is None:
            x = self.pos[0]
            y = self.pos[1]
            scalex,scaley = 1,1
            surf = self.__LINK["main"]
        if self.__lighten:
            pygame.draw.rect(surf,(120,120,0),[x,y,self.bound[0]*scalex,self.bound[1]*scaley],5)
        else:
            pygame.draw.rect(surf,(120,120,0),[x,y,self.bound[0]*scalex,self.bound[1]*scaley],3)
        siz = (len(self.objs)*35)-self.bound[1] #Total size of all the contents inside
        self.screen.fill((0,0,0)) #Empty the surface
        for i,a in enumerate(self.objs): #Render all the widgets contained
            a.pos[1] = (i*35)-(self.__scroll.scroll*siz)
            a.render(a.pos[0],a.pos[1],scalex,scaley,self.screen)
        surf.blit(self.screen,[x,y]) #Apply the surface to the main surface
        #Edit options and render scrollbar.
        self.__scroll.pos = [x+(self.bound[0]*scalex)-20,y] #Position setting
        self.__scroll.bound[1] = self.bound[1]-4 #Height setting
        self.__scroll.render(x+(self.bound[0]*scalex)-22,y+2,scalex,scaley,surf) #Rendering

class TextEntry: #Feild to enter text into
    def __init__(self,x,y,LINK,length=50,resize=True,backgroundText="",enterFunc=None):
        self.pos = [x,y] #Position of the text entry
        self.__resize = resize
        self.bound = [length,30] #Box to type into
        self.__length = length
        self.__LINK = LINK #Link pointer
        self.text = "" #Text that is typed
        self.__backText = backgroundText #Background text of the textbox if there is nothing being typed
        self.__call = enterFunc #Function to call when the enter button is hit.
        self.__font = LINK["font24"]
        self.__active = False #Is the textbox active?
        self.__lighten = False
        self.__click = False
        self.__caps = False #Capital or not
        self.__capL = False #Caps lock
        self.__loop = [-1,0] #Charicter that is being held down
        self.__blink = [False,time.time()+0.3] #Time taken to blink the cursor
    def loop(self,mouse,kBuf): #Called continuesly
        self.__lighten = mouse[1]>self.pos[0] and mouse[2]>self.pos[1] and mouse[1]<self.pos[0]+self.bound[0] and mouse[2]<self.pos[1]+self.bound[1]
        if mouse[0]!=self.__click: #A mouse click event was detected
            self.__click = mouse[0] == True
            if mouse[0]: #Mouse was clicked down
                self.__active = self.__lighten == True
        if self.__active: #Text entry is selected and active
            for event in kBuf:
                if event.type == pygame.KEYDOWN: #A key was pressed down
                    if event.key >= 32 and event.key < 126: #The key is a charicter
                        if (self.__caps or self.__capL) and not (self.__caps and self.__capL):
                            self.text += chr(event.key).upper()
                        else:
                            self.text += chr(event.key)
                        self.__loop[0] = ord(self.text[-1])
                        self.__loop[1] = time.time()+0.5
                    elif event.key == pygame.K_BACKSPACE: #Backspace
                        self.text = self.text[:-1]
                        self.__loop[0] = pygame.K_BACKSPACE + 0
                        self.__loop[1] = time.time()+0.5
                    elif event.key == pygame.K_CAPSLOCK: #Caps lock
                        self.__capL = not self.__capL
                    elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT: #Right or left shift was pressed
                        self.__caps = True
                    elif event.key == pygame.K_RETURN: #Enter button was pressed
                        self.__active = False
                        try: #Try to call the function
                            if not self.__call is None: #See if it exists yet.
                                self.__call(self.__LINK,self.text)
                        except:
                            if self.__LINK["DEV"]: #Raise the error
                                raise
                            else: #Report error to games error handler
                                self.__LINK["errorDisplay"]("text feild '"+self.__backText+"' encountered an error while running the function",sys.exc_info())
                elif event.type == pygame.KEYUP: #A key was let go
                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT: #Left or right shift
                        self.__caps = False
                    elif event.key == self.__loop[0]: #Any key that was being held down
                        self.__loop[0] = -1
            if time.time()>self.__loop[1] and self.__loop[0]!=-1: #Spam the key if the user is holding it down for a certain time
                if self.__loop[0] == pygame.K_BACKSPACE: #User is holding down backspace
                    self.text = self.text[:-1]
                else:
                    self.text+=chr(self.__loop[0])
                self.__loop[1] = time.time()+0.05
    def render(self,x=None,y=None,scalex=None,scaley=None,surf=None): #Render the text box
        if x is None:
            x = self.pos[0]
            y = self.pos[1]
            scalex,scaley = 1,1
            surf = self.__LINK["main"]
        if len(self.text)==0: #Put background text on if no text is given
            tex = self.__font.render(self.__backText+"  ",18,(120,120,120))
        else:
            tex = self.__font.render(self.text+"  ",18,(255,255,255))
        if self.__resize: #Resize the box if enabled
            self.bound[0] = tex.get_size()[0]+10
            if self.bound[0]<self.__length:
                self.bound[0]=self.__length+0
        pygame.draw.rect(surf,(50,50,50),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley])
        if self.__lighten and not self.__active:
            pygame.draw.rect(surf,(0,255,0),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],5)
        elif self.__active:
            pygame.draw.rect(surf,(0,255,255),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],5)
        else:
            pygame.draw.rect(surf,(0,180,0),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],3)
        if self.__active: #Apply a blinker to the end of the text
            if time.time()>self.__blink[1]:
                self.__blink[1] = time.time()+0.2
                self.__blink[0] = not self.__blink[0]
            if self.__blink[0] and len(self.text)!=0: #Add to the end of the text
                pygame.draw.rect(surf,(255,255,255),[x+tex.get_size()[0]-5,y+((self.bound[1]*scaley)/6)+1,10,18])
            elif self.__blink[0]: #Put at the begining of the text
                pygame.draw.rect(surf,(255,255,255),[x+5,y+((self.bound[1]*scaley)/6)+1,10,18])
        surf.blit(tex,(x+5,y+((self.bound[1]*scaley)/6)))

class Label:
    def __init__(self,x,y,LINK,text="Label"):
        self.pos = [x,y] #Position of the label
        self.bound = [10,30] #Boundry box
        self.__font = LINK["font24"] #Font of the text
        self.__LINK = LINK
        self.__flash = 0 #Flash timer to flash the text if requested by anouther function
        self.text = text #Text to display
    def loop(self,mouse,kBuf): #Looped continuesly
        pass
    def flickr(self): #Makes the label flicker for 2 seconds
        self.__flash = time.time()+2
    def render(self,x=None,y=None,scalex=None,scaley=None,surf=None): #Render the widget
        if x is None:
            x = self.pos[0]
            y = self.pos[1]
            scalex,scaley = 1,1
            surf = self.__LINK["main"]
        tex = self.__font.render(self.text,18,(255,255,255)) #Place the text in a surface
        self.bound[0] = tex.get_size()[0]+10
        if self.bound[0]<20: #If the length of the text is below normal then add a small amount so the box is still visible
            self.bound[0]=20
        if self.__flash > time.time() and round((self.__flash-time.time())*8)%2==0:
            pygame.draw.rect(surf,(255,255,0),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],5)
        else:
            pygame.draw.rect(surf,(200,200,0),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],3)
        surf.blit(tex,(x+5,y+((self.bound[1]*scaley)/6)))

class ComboBox:
    def __init__(self,x,y,LINK,length=200,items=[],changeCall=None):
        self.pos = [x,y] #Position of the combo box
        self.bound = [length,30] #Boundary box of the combo box
        self.__LINK = LINK
        self.items = items #The items inside the combo box (list of strings)
        self.__call = changeCall #Function to call if a different item is selected
        self.__font = LINK["font24"]
        self.__lighten = False #Used to show a small details when hovered over
        self.__click = False #Used to detect mouse click changes
        self.__selectChange = 0 #To detect changes in the select variable
        self.__loop = [-1,0] #Used for spamming buttons when held down
        self.select = 0 #The selected item
        self.__active = False #If the combo box is currently selected
    def loop(self,mouse,kBuf): #Called continuesly
        self.__lighten = mouse[1]>self.pos[0] and mouse[2]>self.pos[1] and mouse[1]<self.pos[0]+self.bound[0] and mouse[2]<self.pos[1]+self.bound[1]
        if mouse[0]!=self.__click:
            self.__click = mouse[0] == True
            if mouse[0]:
                if self.__active == self.__lighten and self.__lighten:
                    if mouse[2]>self.pos[1]+(self.bound[1]/2):
                        self.select += 1
                        if self.select >= len(self.items):
                            self.select = len(self.items)-1
                    else:
                        self.select -= 1
                        if self.select<0:
                            self.select = 0
                self.__active = self.__lighten == True
        if self.__active and len(self.items)!=0:
            for event in kBuf: #Deal with keyboard events
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP: #Go one item up
                        self.select -= 1
                        if self.select<0:
                            self.select = 0
                    elif event.key == pygame.K_DOWN: #Go one item down
                        self.select += 1
                        if self.select >= len(self.items):
                            self.select = len(self.items)-1
                    self.__loop = [event.key+0,time.time()+0.5]
                elif event.type == pygame.KEYUP: #Used to reset __loop to stop spamming if the user lets go of the key.
                    if event.key == self.__loop[0]:
                        self.__loop = [-1,0]
        if self.__loop[0]!=-1 and time.time()>self.__loop[1]: #Spam keys when avalible
            if self.__loop[0] == pygame.K_UP:
                self.select -= 1
                if self.select<0:
                    self.select = 0
            elif self.__loop[0] == pygame.K_DOWN:
                self.select += 1
                if self.select >= len(self.items):
                    self.select = len(self.items)-1
            self.__loop[1] = time.time()+0.1
        if self.__selectChange != self.select: #Detect a change in the selected item and send that to the binded function
            self.__selectChange = self.select + 0
            try: #Try to call the function
                if not self.__call is None: #See if it exists yet.
                    self.__call(self.__LINK,self.items[self.select])
            except:
                if self.__LINK["DEV"]: #Raise the error
                    raise
                else: #Report error to games error handler
                    self.__LINK["errorDisplay"]("combo box '"+self.items[self.select]+"' encountered an error while running the function",sys.exc_info())
    def render(self,x=None,y=None,scalex=None,scaley=None,surf=None): #Render the widget
        if x is None:
            x = self.pos[0]
            y = self.pos[1]
            scalex,scaley = 1,1
            surf = self.__LINK["main"]
        if len(self.items)==0: #No items inside the combo box, display default text
            tex = self.__font.render("Combo",18,(255,255,255))
        else:
            tex = self.__font.render(self.items[self.select],18,(255,255,255))
        pygame.draw.rect(surf,(75,75,0),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley]) #A background rectangle
        #Outline rectangles
        if self.__lighten and not self.__active:
            pygame.draw.rect(surf,(0,255,0),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],5)
        elif self.__active:
            pygame.draw.rect(surf,(0,255,255),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],5)
        else:
            pygame.draw.rect(surf,(0,180,0),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],3)
        #Arrows
        mid = (self.bound[1]*scaley)/2
        if self.__active or self.__lighten:
            col1,col2 = (255,255,255),(255,255,255)
        else:
            col1,col2 = (120,120,120),(120,120,120)
        if self.select==0 and len(self.items)!=0:
            col1 = (60,60,60)
        if self.select==len(self.items)-1:
            col2 = (60,60,60)
        pygame.draw.polygon(surf,col1,[[x+(self.bound[0]*scalex)-26,y+mid-2],
                                                [x+(self.bound[0]*scalex)-16,y+mid-10],
                                                [x+(self.bound[0]*scalex)-6,y+mid-2]])
        pygame.draw.polygon(surf,col2,[[x+(self.bound[0]*scalex)-26,y+mid+2],
                                                [x+(self.bound[0]*scalex)-16,y+mid+10],
                                                [x+(self.bound[0]*scalex)-6,y+mid+2]])
        surf.blit(tex,(x+5,y+((self.bound[1]*scaley)/6)))

class Scrollbar:
    def __init__(self,x,y,LINK,length=400,callFunc=None):
        self.pos = [x,y] #Position of the scrollbar
        self.bound = [20,length] #Boundary box of the scrollbar
        self.__length = length #Length of the scrollbar
        self.__LINK = LINK
        self.__call = callFunc
        self.__click = False #To detect mouse click changes
        self.scroll = 0 #Percentage scroll (fraction)
        self.size = 600 #Size of the item the scrollbar is linked to
        self.__lighten = False #Used to show minimal detail when hovered over
        self.__active = False #If the scrollbar is being dragged
        self.__grabPos = 0 #Y coordinate of the grab position when initaly dragging the bar
        self.__lighten1 = False #Lighten for top arrow
        self.__lighten2 = False #Lighten for bottom arrow
        self.__lighten3 = False #Lighten for behind the scrollbar
        self.__loop = 0 #Used for buttons on the scrollbar that loop when held, e.g. arrows either side
    def loop(self,mouse,kBuf): #Called continuesly
        self.__lighten = mouse[1]>self.pos[0] and mouse[2]>self.pos[1] and mouse[1]<self.pos[0]+self.bound[0] and mouse[2]<self.pos[1]+self.bound[1]
        scrBef = self.scroll+0 #Variable used to detect scroll changes
        if mouse[0]!=self.__click:
            self.__click = mouse[0] == True
            if mouse[0] and self.__lighten and self.size>self.__length-40: #Mouse is pressed and mouse is inside the hitbox
                siz = (self.__length/self.size)*(self.__length-40) #Size of the scrollbar in pixels
                spos = (self.__length-40-siz)*self.scroll #Scrollbar position
                self.__active = self.__lighten and mouse[2]>spos+self.pos[1]+20 and mouse[2]<spos+self.pos[1]+20+siz
                if self.__active: #Scrollbar dragger is touched
                    self.__grabPos = mouse[2] - (spos+self.pos[1]+20) #Get the grab position in relation to the scrollbar dragger
                elif mouse[2]>self.pos[1]+20 and mouse[2]<self.pos[1]+self.__length-20: #Area outisde the scrollbar dragger but not on the arrow buttons
                    self.__lighten3 = True
                    self.__loop = time.time()+0.5
                    if mouse[2]<self.pos[1]+spos: #Mouse is below scrollbar dragger
                        self.scroll -= (self.__length/2)/self.size #Half the scrollbar size
                        if self.scroll < 0:
                            self.scroll = 0
                    else: #Mouse is above scrollbar dragger
                        self.scroll += (self.__length/2)/self.size #Half the scrollbar size
                        if self.scroll > 1:
                            self.scroll = 1
                if mouse[2]<self.pos[1]+20: #Jump up
                    self.scroll -= 40/self.size #40 pixels
                    if self.scroll < 0:
                        self.scroll = 0
                    self.__lighten1 = True
                    self.__loop = time.time()+0.5
                if mouse[2]>self.pos[1]+self.__length-20: #Jump down
                    self.scroll += 40/self.size #40 pixels
                    if self.scroll > 1:
                        self.scroll = 1
                    self.__lighten2 = True
                    self.__loop = time.time()+0.5
            else: #Reset everything so nothing is still active
                self.__active = False
                self.__lighten1 = False
                self.__lighten2 = False
                self.__lighten3 = False
        if self.__active: #Scrollbar is being dragged
            mpos = mouse[2]-self.__grabPos-self.pos[1]-20 #Local position of the mouse to the scrollbar
            siz = (self.__length/self.size)*(self.__length-40) #Size of the scrollbar dragger
            self.scroll = mpos/(self.__length-40-siz) #Fraction of the scrollbar
            if self.scroll<0:
                self.scroll = 0
            elif self.scroll>1:
                self.scroll = 1
        if time.time()>self.__loop and (self.__lighten1 or self.__lighten2 or self.__lighten3): #Spam buttons if being held
            if self.__lighten1:
                self.scroll -= 40/self.size #40 pixels
                if self.scroll < 0:
                    self.scroll = 0
            elif self.__lighten2:
                self.scroll += 40/self.size #40 pixels
                if self.scroll > 1:
                    self.scroll = 1
            elif self.__lighten3: #Move half the scrollbar size if mouse is above or below the scrollbar dragger
                siz = (self.__length/self.size)*(self.__length-40)
                spos = (self.__length-40-siz)*self.scroll #Scrollbar position
                if mouse[2]<self.pos[1]+spos:
                    self.scroll -= (self.__length/2)/self.size #Half the scrollbar size
                    if self.scroll < 0:
                        self.scroll = 0
                elif mouse[2]>self.pos[1]+spos+siz:
                    self.scroll += (self.__length/2)/self.size #Half the scrollbar size
                    if self.scroll > 1:
                        self.scroll = 1
            self.__loop = time.time()+0.1
        if scrBef != self.scroll:
            try: #Try to call the function
                if not self.__call is None: #See if it exists yet.
                    self.__call(self.__LINK,self.scroll)
            except:
                if self.__LINK["DEV"]: #Raise the error
                    raise
                else: #Report error to games error handler
                    self.__LINK["errorDisplay"]("scrollbar encountered an error while running the function",sys.exc_info())
    def render(self,x=None,y=None,scalex=None,scaley=None,surf=None): #Render the widget
        if x is None:
            x = self.pos[0]
            y = self.pos[1]
            scalex,scaley = 1,1
            surf = self.__LINK["main"]
        if self.__lighten1: #Top arrow
            pygame.draw.rect(surf,(0,75,0),[x,y,20,20])
        else:
            pygame.draw.rect(surf,(0,100,0),[x,y,20,20])
        if self.__lighten2: #Bottom arrow
            pygame.draw.rect(surf,(0,75,0),[x,y+(self.bound[1]*scaley)-20,20,20])
        else:
            pygame.draw.rect(surf,(0,100,0),[x,y+(self.bound[1]*scaley)-20,20,20])
        if self.__lighten3:#Behind the scrollbar dragger
            pygame.draw.rect(surf,(125,125,0),[x,y+20,20,(self.bound[1]*scaley)-40])
        else:
            pygame.draw.rect(surf,(150,150,0),[x,y+20,20,(self.bound[1]*scaley)-40])
        if self.size>self.__length-40: #Draw only if it is possible
            siz = (self.__length/self.size)*(self.__length-40) #Size of the scrollbar dragger
            spos = (self.__length-40-siz)*self.scroll #Scrollbar position
            if self.__active: #Scrollbar dragger
                pygame.draw.rect(surf,(20,20,0),[x,y+20+spos,20,siz])
            else:
                pygame.draw.rect(surf,(50,50,0),[x,y+20+spos,20,siz])
            #Draw the scrollbar draggers lines.
            pygame.draw.line(surf,(150,150,150),[x,y+10+spos+(siz/2)],[x+20,y+10+spos+(siz/2)],4)
            pygame.draw.line(surf,(150,150,150),[x,y+30+spos+(siz/2)],[x+20,y+30+spos+(siz/2)],4)
        #Draw the arrows
        pygame.draw.polygon(surf,(0,255,0),[[x+(self.bound[0]*scalex)-20,y+20],
                                                [x+(self.bound[0]*scalex)-10,y],
                                                [x+(self.bound[0]*scalex)-1,y+20]])
        pygame.draw.polygon(surf,(0,255,0),[[x+(self.bound[0]*scalex)-20,y+self.bound[1]-20],
                                                [x+(self.bound[0]*scalex)-10,y+self.bound[1]-1],
                                                [x+(self.bound[0]*scalex)-1,y+self.bound[1]-20]])

class CheckButton:
    def __init__(self,x,y,LINK,text="Check button",on=False,func=None):
        self.pos = [x,y]
        self.bound = [len(text)*10,30]
        self.active = on
        self.__LINK = LINK
        self.__font = LINK["font24"]
        self.__text = text
        self.__call = func
        self.__click = False
        self.__lighten = False
    def loop(self,mouse,kBuf): #Called continuesly
        self.__lighten = mouse[1]>self.pos[0] and mouse[2]>self.pos[1] and mouse[1]<self.pos[0]+self.bound[0] and mouse[2]<self.pos[1]+self.bound[1]
        if mouse[0]!=self.__click:
            self.__click = mouse[0] == True
            if mouse[0]:
                if self.__lighten:
                    self.active = not self.active
                    try: #Try to call the function
                        if not self.__call is None: #See if it exists yet.
                            self.__call(self.__LINK,self.active)
                    except:
                        if self.__LINK["DEV"]: #Raise the error
                            raise
                        else: #Report error to games error handler
                            self.__LINK["errorDisplay"]("checkbutton '"+self.__text+"' encountered an error while running the function",sys.exc_info())
            else:
                pass
    def render(self,x=None,y=None,scalex=None,scaley=None,surf=None): #Render the widget
        if x is None:
            x = self.pos[0]
            y = self.pos[1]
            scalex,scaley = 1,1
            surf = self.__LINK["main"]
        tex = self.__font.render(self.__text,18,(255,255,255))
        self.bound[0] = tex.get_size()[0]+40
        if self.bound[0]<20:
            self.bound[0]=20
        if self.__lighten:
            pygame.draw.rect(surf,(0,255,0),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],5)
        else:
            pygame.draw.rect(surf,(0,180,0),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],3)
        if self.active:
            pygame.draw.rect(surf,(0,255,0),[x+6,y+6,18,18])
        else:
            pygame.draw.rect(surf,(255,0,0),[x+6,y+6,18,18])
        surf.blit(tex,(x+35,y+((self.bound[1]*scaley)/6)))

class Button:
    def __init__(self,x,y,LINK,text="Button",func=None):
        self.__LINK = LINK
        self.pos = [x,y] #Position of the button
        self.bound = [(len(text)*10)+20,30] #Bounding box of the button, this can be used for detecting clicks.
        self.__text = text #Text displayed on the button
        self.__call = func #Function to call
        self.__font = LINK["font24"]
        self.__lighten = False
        self.__click = False #Detecting changes in clicking
        self.__holding = False #If the button is being held down
    def loop(self,mouse,kBuf): #Called continuesly
        self.__lighten = mouse[1]>self.pos[0] and mouse[2]>self.pos[1] and mouse[1]<self.pos[0]+self.bound[0] and mouse[2]<self.pos[1]+self.bound[1]
        if mouse[0]!=self.__click:
            self.__click = mouse[0] == True
            if mouse[0]:
                self.__holding = self.__lighten == True
            elif self.__holding and self.__lighten:
                self.__holding = False
                try:
                    if not self.__call is None:
                        self.__call(self.__LINK)
                    else:
                        self.__LINK["errorDisplay"]("button '"+self.__text+"' is not bound to any functions!")
                except:
                    if self.__LINK["DEV"]:
                        raise
                    else:
                        self.__LINK["errorDisplay"]("button '"+self.__text+"' encountered an error while running the function",sys.exc_info())
            else:
                self.__holding = False
    def render(self,x=None,y=None,scalex=None,scaley=None,surf=None): #Render the widget
        if x is None:
            x = self.pos[0]
            y = self.pos[1]
            scalex,scaley = 1,1
            surf = self.__LINK["main"]
        tex = self.__font.render(self.__text,18,(255,255,255))
        self.bound[0] = tex.get_size()[0]+10
        if self.bound[0]<20:
            self.bound[0]=20
        if (self.__lighten and not self.__holding) or (not self.__lighten and self.__holding):
            pygame.draw.rect(surf,(0,255,0),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],5)
        elif self.__holding:
            pygame.draw.rect(surf,(0,255,255),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],5)
        else:
            pygame.draw.rect(surf,(0,180,0),[x,y]+[self.bound[0]*scalex,self.bound[1]*scaley],3)
        surf.blit(tex,(x+5,y+((self.bound[1]*scaley)/6)))
