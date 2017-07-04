#This file is used to render entities
import pygame

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
                a.sRender((a.pos[0]*scale)-x,(a.pos[1]*scale)-y,scale,surf,True)