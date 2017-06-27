#This file is for custom screen widgets that work with pygame
#This will be used in screens.

import pygame, time

class Screen: #Screen object to cast all widgets onto, this will will move objects into correct place when resized
    def __init__(self,LINK,reslution=None):
        if reslution is None:
            self.res = LINK["reslution"] #Reslution of the screen
        else:
            self.res = reslution #Reslution of the screen
        self.__objs = {} #Objects inside the screen
        self.__count = 0 #Count index of the widget
        self.__LINK = LINK
        self.__mouseChange = False #Mouse click on/off
        self.__activeWidget = -1 #Widget index of the active widget being interfaced with
    def addItem(self,itm,posx,posy,*pars): #Add a new widget to the screen
        self.__objs[self.__count] = itm(posx,posy,self.__LINK,*pars) #Add to the dictionary
        self.__count += 1
        return self.__count-1 #Return index of widget
    def itemConfig(self,index,*pars): #Configure an item in the dictionary
        if index in self.__objs: #If widget exists then configure it
            self.__objs[index].config(*pars)
        else: #Display an error using the error function
            self.__LINK["errorDisplay"]("in class screen, an index of "+str(index)+" was addressed but it doesen't exist!")
    def loop(self,mouse): #Pretty much an event loop, this gets called frequently and will update the widgets if a mouse event occures
        if mouse[0] != self.__mouseChange:
            self.__mouseChange = mouse[0] == True
            if mouse[0]:
                pass
            else:
                pass
    def render(self,surf=None): #Render the screen onto the surface
        if surf is None: #If no surface is given then use the global one from __LINK
            main = self.__LINK["main"]
        else:
            main = surf
        multx,multy = self.res[0]/800,self.res[1]/500 #Displacement of objects due to the screen resizing
        for b in self.__objs: #Render all the widgets contained
            a = self.__objs[b]
            a.render(a.pos[0]*multx,a.pos[1]*multy,multx,multy,main)


class Button:
    def __init__(self,x,y,LINK,text="Button",func=None):
        self.__LINK = LINK
        self.pos = [x,y] #Position of the button
        self.bound = [(len(text)*10)+10,30] #Bounding box of the button, this can be used for detecting clicks.
        self.__text = text #Text displayed on the button
        self.__call = func #Function to call
        self.__font = LINK["font24"]
    def config(self):
        pass
    def render(self,x,y,scalex,scaley,surf): #Render the widget
        pygame.draw.rect(surf,(0,255,0),self.pos+[self.bound[0]*scalex,self.bound[1]*scaley],5)
        surf.blit(self.__font.render(self.__text,18,(255,255,255)),(x+5,y+((self.bound[1]*scaley)/6)))