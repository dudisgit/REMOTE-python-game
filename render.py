#This file is used to render entities
import pygame, time, screenLib, os, pickle, math, random
import entities.base as base

ARC_SIZE = 60
FLASH_TIME = 4 #Seconds to keep text flashing for
HB_LENG = 150 #Length of the health bar

def insideArc(pos,cent,angle,arcWidth=ARC_SIZE): #Returns true if the point is inside the arc "cent" with the angle "ang"
    ang = angle%360 #Angle in range of 0-360
    ang2 = ang/180*math.pi #Angle in radients
    arcSiz = arcWidth/180*math.pi #Size of the arc in radients
    point = [pos[0]-cent[0],pos[1]-cent[1]] #Point we are checking is inside the arc
    if (ang>270+arcWidth and ang<=360) or (ang>=0 and ang<=90-arcWidth):
        a = math.tan(arcSiz-ang2)*point[0]
        b = math.tan(-arcSiz-ang2)*point[0]
        return point[1]<a and point[1]>b
    elif ang>90+arcWidth and ang<=270-arcWidth:
        a = math.tan(arcSiz+ang2)*(point[0]*-1)
        b = math.tan(-arcSiz+ang2)*(point[0]*-1)
        return point[1]<a and point[1]>b
    elif ang>270-arcWidth and ang<=270+arcWidth:
        a = math.tan(arcSiz-ang2)*point[0]
        b = math.tan(-arcSiz-ang2)*point[0]
        return point[1]>a and point[1]>b
    elif ang>90-arcWidth and ang<=90+arcWidth:
        a = math.tan(arcSiz-ang2)*point[0]
        b = math.tan(-arcSiz-ang2)*point[0]
        return point[1]<a and point[1]<b
    return False
def visualArc(cent,angle,surf,arcWidth=ARC_SIZE): #Draw arcs visualy (used to debug the function above)
    pygame.draw.arc(surf,(255,255,0),[int(cent[0]-200),int(cent[1]-200),400,400],(angle-arcWidth)/180*math.pi,(angle+arcWidth)/180*math.pi,4)

class Scematic:
    def __init__(self,LINK,edit=False):
        self.__LINK = LINK
        self.__edit = edit #If the view of this scematic is through an editor (e.g. map editor)
        self.ents = [] #Entities to be rendered
        self.__scaleChange = 0 #Used to detect changes in scale
    def render(self,x,y,scale,surf=None,inView=False):
        if surf is None:
            surf = self.__LINK["main"]
        edit = self.__edit == True
        if scale != self.__scaleChange: #Resize all images if a scale change is detected.
            for a in self.__LINK["content"]:
                siz = list(self.__LINK["content"][a].get_size())
                self.__LINK["cont"][a] = pygame.transform.scale(self.__LINK["content"][a],(int(siz[0]*scale/10.24),int(siz[1]*scale/10.24)))
            self.__scaleChange = scale+0
        sx,sy = surf.get_size()
        for a in self.ents:
            if (a.canShow(inView) or edit) and a.discovered: #Allowed to show in scematic view
                if ((a.pos[0]*scale)-x<sx and (a.pos[1]*scale)-y<sy and ((a.pos[0]+a.size[0])*scale)-x>0 and ((a.pos[1]+a.size[1])*scale)-y>0) or a.renderAnyway: #Inside screen
                    a.sRender((a.pos[0]*scale)-x,(a.pos[1]*scale)-y,scale,surf,edit,inView)
class DroneFeed: #Like the "Scematic" class but for 3D rendering
    def __init__(self,LINK):
        self.__LINK = LINK
        self.__ignore = [self.__getEnt("room"),self.__getEnt("door"),self.__getEnt("airlock"),self.__getEnt("android")] #Entities to render even if their not inside the viewing arc
        self.ents = [] #Entities to be rendered
        self.__doneRooms = [] #Tracks rooms that where rendered so they don't get rendered more than once
    def __getEnt(self,name): #Returns the entity with the name
        if name in self.__LINK["ents"]: #Does the entity exist?
            return self.__LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.__LINK["errorDisplay"]("Tried to create entity but doesen't exist '"+name+"'")
        return self.__LINK["null"]
    def __checkInAngle(self,ob,cent,scale,x,y,ang): #Checks if an entity is inside an arc
        if insideArc([((ob.pos[0]*scale)+(ob.renderSize[0]*scale))-x,((ob.pos[1]*scale)+(ob.renderSize[1]*scale))-y],cent,ang): #Top left
            return True
        if insideArc([((ob.pos[0]*scale)+(ob.renderSize[2]*scale))-x,((ob.pos[1]*scale)+(ob.renderSize[3]*scale))-y],cent,ang): #Bottom right
            return True
        if insideArc([((ob.pos[0]*scale)+(ob.renderSize[0]*scale))-x,((ob.pos[1]*scale)+(ob.renderSize[3]*scale))-y],cent,ang): #Bottom left
            return True
        if insideArc([((ob.pos[0]*scale)+(ob.renderSize[2]*scale))-x,((ob.pos[1]*scale)+(ob.renderSize[1]*scale))-y],cent,ang): #Top right
            return True
        return False
    def render(self,x,y,scale,ang,rendRoom,ignorEnt=None,surf=None,arcSiz=-1,rPos=None,origAng=None): #Render all entities inside the room and other rooms (if door is open)
        if surf is None: #No surface given, use the pygame window
            surf = self.__LINK["main"]
        if origAng is None: #This function was not recursed and is a starting point
            self.__doneRooms = [rendRoom] #Make this current room not renderable when recursing from a door
            arcSiz = ARC_SIZE+0 #Arc size
        RoomReferenceObject = self.__getEnt("room") #Used as a reference object for a room
        DoorReferenceObject = self.__getEnt("door") #Used as a reference object for a door
        AirlockReferenceObject = self.__getEnt("airlock") #Used as a reference object for an airlock
        sx,sy = surf.get_size()
        if rPos is None:
            rPos = [sx/2,sy/2]
            if self.__LINK["DEVDIS"]: #Development view, draws viewing arcs
                visualArc([sx/2,sy/2],ang,surf,arcSiz)
                if not origAng is None: #Draw second viewing arc
                    visualArc([sx/2,sy/2],origAng,surf,arcSiz)
        elif self.__LINK["DEVDIS"]: #Development view, draws viewing arc
            visualArc(rPos,ang,surf,arcSiz)
        for a in self.ents: #Go through every entity in the map
            if type(rendRoom)==RoomReferenceObject: #View is currently inside a room
                inR = a.pos[0]+a.size[0]>rendRoom.pos[0]-50 and a.pos[1]+a.size[1]>rendRoom.pos[1]-50 and a.pos[0]<rendRoom.pos[0]+rendRoom.size[0]+50 and a.pos[1]<rendRoom.pos[1]+rendRoom.size[1]+50
                if not inR: #Entity is not inside room, check if its a door
                    if type(a)==DoorReferenceObject or type(a)==AirlockReferenceObject: #Entity is a door
                        inR = a in rendRoom.doors #Check if the door/airlock is part of the rooms doors/airlocks
            elif type(rendRoom)==DoorReferenceObject or type(rendRoom)==AirlockReferenceObject: #View is currently inside a door
                inR = False
                if not rendRoom.room1 is None: #First room exists
                    inR = a.pos[0]+a.size[0]>rendRoom.room1.pos[0]-50 and a.pos[1]+a.size[1]>rendRoom.room1.pos[1]-50 and a.pos[0]<rendRoom.room1.pos[0]+rendRoom.room1.size[0]+50 and a.pos[1]<rendRoom.room1.pos[1]+rendRoom.room1.size[1]+50
                    if not inR: #Entity is not inside the first room, check if its a door
                        if type(a)==DoorReferenceObject or type(a)==AirlockReferenceObject: #Entity is a door
                            inR = a in rendRoom.room1.doors #Check if the door/airlock is part of the first rooms doors/airlocks
                if not rendRoom.room2 is None: #Second room exists
                    if not inR: #Entity is not part of the first room, check second room
                        inR = a.pos[0]+a.size[0]>rendRoom.room2.pos[0]-50 and a.pos[1]+a.size[1]>rendRoom.room2.pos[1]-50 and a.pos[0]<rendRoom.room2.pos[0]+rendRoom.room2.size[0]+50 and a.pos[1]<rendRoom.room2.pos[1]+rendRoom.room2.size[1]+50
                        if not inR: #Entity is not inside room, check if its a door
                            if type(a)==DoorReferenceObject or type(a)==AirlockReferenceObject: #Entity is a door
                                inR = a in rendRoom.room2.doors #Check if the door/airlock is part of the first rooms doors/airlocks
            else: #Outside map, render all entities.
                inR = True
            if (inR or rendRoom==-1) and (((a.pos[0]*scale)-x<sx and (a.pos[1]*scale)-y<sy and ((a.pos[0]+a.size[0])*scale)-x>0 and ((a.pos[1]+a.size[1])*scale)-y>0) or a.AllwaysRender): #Inside screen
                InArc = self.__checkInAngle(a,rPos,scale,x,y,ang) #Is inside the view angle
                if not origAng is None: #This function was called by a recursion, check the view angle of the original view angle as well.
                    InArc = InArc and self.__checkInAngle(a,origAng[1],scale,x,y,origAng[0])
                if InArc or type(a) in self.__ignore or a==ignorEnt: #Is the entity inside the arc or is the entity bypassing the
                    if not origAng is None: #Check if theres a second angle for the arc (used when seeing through doors)
                        ang3 = origAng[0]
                    else: #Render normaly without second angle
                        ang3 = None
                    if (a == ignorEnt or (a == rendRoom and type(a)!=RoomReferenceObject)) and origAng is None: #Entity is the entity producing the feed (the drone being controlled)
                        if type(a)==self.__getEnt("drone"):
                            a.render((a.pos[0]*scale)-x,(a.pos[1]*scale)-y,scale,ang,surf,arcSiz,ang3,True) #3D render entity
                        else:
                            a.render((a.pos[0]*scale)-x,(a.pos[1]*scale)-y,scale,None,surf,arcSiz) #3D render entity
                    else: #Render normal entity
                        a.render((a.pos[0]*scale)-x,(a.pos[1]*scale)-y,scale,ang,surf,arcSiz,ang3) #3D render entity
                        if origAng is None:
                            a.discovered = True
                        if (type(a)==DoorReferenceObject or type(a)==AirlockReferenceObject) and type(rendRoom)==RoomReferenceObject and not ignorEnt is None and not self.__LINK["popView"]: #Rendered entity is a door or airlock
                            if a.room1 in self.__doneRooms: #Check if the first room of the airlock has been visited before
                                R = a.room2
                            else:
                                R = a.room1
                            if a.settings["open"] and not R in self.__doneRooms and InArc and not R is None: #Door/airlock is open
                                self.__doneRooms.append(R) #Make sure this room isn't visited again when rendering the current frame.
                                ang2 = math.atan2((a.pos[0]+(a.size[0]/2))-(ignorEnt.pos[0]+(ignorEnt.size[0]/2)),(a.pos[1]+(a.size[1]/2))-(ignorEnt.pos[1]+(ignorEnt.size[1]/2)))*180/math.pi
                                arcS = arcSiz-(math.sqrt(((a.pos[0]-ignorEnt.pos[0])**2)+((a.pos[1]-ignorEnt.pos[1])**2))/2.5)
                                if origAng is None: #There is a second angle to the arc (used when seeing through a door)
                                    AdA = [ang,rPos]
                                else: #Render normaly without second angle
                                    AdA = origAng
                                #Recurse this function on a door
                                if arcS>0: #Arc size is not negative
                                    self.render(x,y,scale,ang2-90,R,a,surf,arcS,[((a.pos[0]+(a.size[0]/2))*scale)-x,((a.pos[1]+(a.size[1]/2))*scale)-y],AdA)

class Model: #An object to reprisent a model
    def __init__(self,LINK,polys):
        self.__angle = 0 #Used to detect changes in angle
        self.__LINK = LINK
        self.__pos = [0,0] #Used to detect changes in position
        self.__modelSize = [None,None,None,None] #Size of the actual model
        self.__polys = [] #Vertices that are cached for rendering
        if type(polys)==str:
            self.__orig = LINK["models"][polys] #Pointer to the original model
        else:
            self.__orig = polys #Pointer to the original model
        self.__Rang = 0 #Used to detect changes in view arc
        self.__angle2 = 0 #Used to detect changes in the second view arc
        self.__rotModl = [] #Vertices that are cached for further processing after rotation.
        for a in self.__orig: #Build polygons
            self.__polys.append(None)
            self.__rotModl.append(None)
            if self.__modelSize[0] is None:
                self.__modelSize = [a[0]+0,a[1]+0,a[0]+0,a[1]+0]
            if a[0]<self.__modelSize[0]:
                self.__modelSize[0] = a[0]+0
            if a[1]<self.__modelSize[1]:
                self.__modelSize[1] = a[1]+0
            if a[0]>self.__modelSize[2]:
                self.__modelSize[2] = a[0]+0
            if a[1]>self.__modelSize[3]:
                self.__modelSize[3] = a[1]+0
        if abs(self.__modelSize[0])>self.__modelSize[2]:
            self.__modelSize[2] = abs(self.__modelSize[0])
        elif self.__modelSize[2]>abs(self.__modelSize[0]):
            self.__modelSize[0] = -self.__modelSize[2]
        if abs(self.__modelSize[1])>self.__modelSize[3]:
            self.__modelSize[3] = abs(self.__modelSize[1])
        elif self.__modelSize[3]>abs(self.__modelSize[1]):
            self.__modelSize[1] = -self.__modelSize[3]
        if self.__modelSize[2]>self.__modelSize[3]:
            self.__modelSize[3] = self.__modelSize[2]+0
            self.__modelSize[1] = -self.__modelSize[3]
        elif self.__modelSize[3]>self.__modelSize[2]:
            self.__modelSize[2] = self.__modelSize[3]+0
            self.__modelSize[0] = -self.__modelSize[2]
        self.__modelSize[0]-=1
        self.__modelSize[1]-=1
        self.__modelSize[2]+=1
        self.__modelSize[3]+=1
        self.__size = list(self.__LINK["main"].get_size()) #Get the size of the screen
        self.__DIV = math.sqrt((self.__size[0]**2)+(self.__size[1]**2))/2.5 #Divide amount
        self.__updateRotate(0) #Fill polygon rotation list
        self.__updateModel(0,0,0,None,1,ARC_SIZE) #Fill render polygon list
    def __updateRotate(self,angle): #Rotates all the vertices by an angle
        for i,a in enumerate(self.__orig): #Go through all vertices of the original model
            ang = math.atan2(a[0],a[1]) #Find angle towards center
            dist = math.sqrt((a[0]**2)+(a[1]**2)) #Find distance towards center
            ang += angle/180*math.pi #Rotate vertex around center
            self.__rotModl[i] = [math.sin(ang)*dist,math.cos(ang)*dist,a[2],a[3]] #Save the vertex
    def __updateModel(self,x,y,Rang,angle2,scale,arcSiz): #Hide verticies that are not in a view arc
        for i,a in enumerate(self.__rotModl): #Go through all the vertices of the rotated vertices list
            MULT = 1+((a[2]*scale)/self.__DIV)
            PS = [((a[0]*scale)-((self.__size[0]/2)-x))*MULT,((a[1]*scale)-((self.__size[1]/2)-y))*MULT]
            if Rang is None:
                InA = True
            else:
                InA = insideArc([PS[0]+(self.__size[0]/2),PS[1]+(self.__size[1]/2)],[self.__size[0]/2,self.__size[1]/2],Rang,arcSiz)
            if not angle2 is None: #Second angle detected
                InA = InA and insideArc([PS[0]+(self.__size[0]/2),PS[1]+(self.__size[1]/2)],[self.__size[0]/2,self.__size[1]/2],angle2,arcSiz)
            self.__polys[i] = [a[0]+0,a[1]+0,a[2]+0,a[3],InA]
    def __render(self,x,y,angle,scale,surf,col=(255,255,255),Rang=None,angle2=None,arcSiz=ARC_SIZE): #Render the model to a surface
        if arcSiz==-1:
            arcSiz = ARC_SIZE
        #Update all new data with the data inside this class
        if Rang is None:
            self.__Rang = None
        else:
            self.__Rang = Rang+0
        if angle2 is None:
            self.__angle2 = None
        else:
            self.__angle2 = angle2+0
        self.__pos = [x+0,y+0]

        for a in self.__polys: #Go through every vertex of the model
            if a[4] or Rang is None:
                MULT = 1+((a[2]*scale)/self.__DIV) #Z multiplier of current vertex
                PS = [((a[0]*scale)-((self.__size[0]/2)-x))*MULT,((a[1]*scale)-((self.__size[1]/2)-y))*MULT] #Vertex position before rendering to screen and without scaling
                lSIZ = round(1*(a[2]/20)*scale)
                if lSIZ<=0:
                    lSIZ = 1
                for b in a[3]: #Go through every vertex attached to this vertex
                    if self.__polys[b][4] or Rang is None: #Inside arc (or just true when there is no arc)
                        MULT2 = 1+((self.__polys[b][2]*scale)/self.__DIV) #Z multiplier for attached vertex
                        PSRaw = [((self.__polys[b][0]*scale)-((self.__size[0]/2)-x))*MULT2,((self.__polys[b][1]*scale)-((self.__size[1]/2)-y))*MULT2] #Vertex position of attached vertex without scaling
                        pygame.draw.line(surf,col,[PS[0]+(self.__size[0]/2),PS[1]+(self.__size[1]/2)],[PSRaw[0]+(self.__size[0]/2),PSRaw[1]+(self.__size[1]/2)],lSIZ) #Draw a line from vertex to attached vertex
    def __CheckIn(self,point,x,y,angle,scale,Rang,angle2,arcSiz): #Returns true if a point is inside the render box of this entity
        PS = [(point[0]*scale)-((self.__size[0]/2)-x),(point[1]*scale)-((self.__size[1]/2)-y)] #Vertex position before rendering to screen and without scaling
        if Rang is None:
            InA = True
        else:
            InA = insideArc([PS[0]+(self.__size[0]/2),PS[1]+(self.__size[1]/2)],[self.__size[0]/2,self.__size[1]/2],Rang,arcSiz)
        if not angle2 is None: #Second angle detected
            InA = InA and insideArc([PS[0]+(self.__size[0]/2),PS[1]+(self.__size[1]/2)],[self.__size[0]/2,self.__size[1]/2],angle2,arcSiz)
        return InA
    def render(self,x,y,angle,scale,surf,col=(255,255,255),Rang=None,angle2=None,arcSiz=ARC_SIZE):
        UL = self.__CheckIn([self.__modelSize[0],self.__modelSize[1]],x,y,angle,scale,Rang,angle2,arcSiz)
        UR = self.__CheckIn([self.__modelSize[2],self.__modelSize[1]],x,y,angle,scale,Rang,angle2,arcSiz)
        DR = self.__CheckIn([self.__modelSize[0],self.__modelSize[3]],x,y,angle,scale,Rang,angle2,arcSiz)
        DL = self.__CheckIn([self.__modelSize[2],self.__modelSize[3]],x,y,angle,scale,Rang,angle2,arcSiz)
        if self.__LINK["DEVDIS"]: #Draw model bounding box
            PS = [(self.__modelSize[0]*scale)-((self.__size[0]/2)-x),(self.__modelSize[1]*scale)-((self.__size[1]/2)-y)] #Vertex position before rendering to screen and without scaling
            PS2 = [(self.__modelSize[2]*scale)-((self.__size[0]/2)-x),(self.__modelSize[3]*scale)-((self.__size[1]/2)-y)] #Vertex position before rendering to screen and without scaling
            pygame.draw.rect(surf,(255,0,255),[PS[0]+(self.__size[0]/2),PS[1]+(self.__size[1]/2),PS2[0]-PS[0],PS2[1]-PS[1]],1)
        if angle!=self.__angle: #Has the model changed angle
            self.__angle = angle + 0
            self.__updateRotate(angle)
            self.__updateModel(x,y,Rang,angle2,scale,arcSiz)
        if Rang!=self.__Rang or angle2!=self.__angle2 or [x,y]!=self.__pos: #Has the model changed view arc or position.
            if not (UL and UR and DR and DL) and (UL or UR or DR or DL):
                self.__updateModel(x,y,Rang,angle2,scale,arcSiz)
        #Check if the model is inside the box
        if UL and UR and DR and DL:
            self.__render(x,y,None,scale,surf,col,None,None,arcSiz)
        elif UL or UR or DR or DL: #Model can render
            self.__render(x,y,angle,scale,surf,col,Rang,angle2,arcSiz) #Render the model

def distort(surf,amo,dead=False): #Distorts a surface
    s = pygame.PixelArray(surf)
    sx,sy = surf.get_size()
    for i in range(amo): #Transport random segments on the Y axis to anouther
        siz = random.randint(1,20)
        rp = random.randint(0,sy-siz)
        rp2 = random.randint(0,sy-siz)
        s[0:sx,rp:rp+siz] = s[0:sx,rp2:rp2+siz]
    if dead: #Dead glitching effect
        for i in range(0,5): #Transport random segments on the Y axis to a random X axis
            ry = random.randint(40,280)%sy
            rp = random.randint(0,sy-ry)
            rlen = random.randint(80,sx-160)
            rx = random.randint(80,sx-rlen-80)
            rm = random.randint(-80,80)
            s[rx:rx+rlen,rp:rp+ry] = s[rx+rm:rx+rlen+rm,rp:rp+ry]

    return surf

def openModel(filePath): #Opens a 3D model
    file = open(filePath,"r")
    verts = []
    f = []
    for a in file: #Go through each line of the file and extract all vertex and face data
        line = a.split("\n")[0] #Strip the line from \n charicters
        if line!="": #Line is not empty
            spl = line.split(" ")
            if line[0]=="v": #Is a vertex
                verts.append([float(spl[1]),float(spl[2]),float(spl[3]),[]])
            elif line[0]=="f": #Linking a face (processed later to stop repeats)
                f.append(line)
    for a in f: #Link vertex's together
        spl = a.split(" ")
        for b in spl[2:]: # Go through every vertex this vertex is attached to
            if not int(spl[1])-1 in verts[int(b)-1][3]: #Vertex not allredey connected on other end.
                verts[int(spl[1])-1][3].append(int(b)-1)
    file.close()
    return verts
def renderModel(model,x,y,angle,scale,surf,col=(255,255,255),Rang=None,angle2=None,arcSiz=ARC_SIZE): #Renders a 3D model on the surface
    #Algorithm will change in future, very inefficient atm.
    #Depricated
    if arcSiz==-1:
        arcSiz = ARC_SIZE
    sx,sy = surf.get_size()
    DIV = math.sqrt((sx**2)+(sy**2))/2.5
    if angle==0: #Angle is 0, no rotation needed
        modelC = []
        for a in model: #Go through every vertex of the model and check if its inside the viewing arc
            if Rang is None: #No viewing arc enabled for this render
                modelC.append(a+[True])
            else: #Check point
                MULT = 1+((a[2]*scale)/DIV) #Z multiplier of current vertex
                PS = [((a[0]*scale)-((sx/2)-x))*MULT,((a[1]*scale)-((sy/2)-y))*MULT]
                InA = insideArc([PS[0]+(sx/2),PS[1]+(sy/2)],[sx/2,sy/2],Rang,arcSiz)
                if not angle2 is None: #Second angle detected
                    InA = InA and insideArc([PS[0]+(sx/2),PS[1]+(sy/2)],[sx/2,sy/2],angle2,arcSiz)
                modelC.append([a[0]+0,a[1]+0,a[2]+0,a[3],InA])
    else: #Rotate the model
        modelC = []
        for a in model: #Go through every vertex in the model
            ang = math.atan2(a[0],a[1]) #Find angle towards center
            dist = math.sqrt((a[0]**2)+(a[1]**2)) #Find distance towards center
            ang += angle/180*math.pi #Rotate vertex around center
            if Rang is None: #No viewing arc enabled for this render
                AD = True
            else: #Check point
                MULT = 1+((a[2]*scale)/DIV) #Z multiplier of current vertex
                PS = [((math.sin(ang)*dist*scale)-((sx/2)-x))*MULT,((math.cos(ang)*dist*scale)-((sy/2)-y))*MULT]
                AD = insideArc([PS[0]+(sx/2),PS[1]+(sy/2)],[sx/2,sy/2],Rang,arcSiz)
                if not angle2 is None: #Second angle detected
                    AD = AD and insideArc([PS[0]+(sx/2),PS[1]+(sy/2)],[sx/2,sy/2],angle2,arcSiz)
            modelC.append([math.sin(ang)*dist,math.cos(ang)*dist,a[2],a[3],AD]) #Save the vertex
    #Rendering the model
    for a in modelC: #Go through every vertex of the model
        if a[4]:
            MULT = 1+((a[2]*scale)/DIV) #Z multiplier of current vertex
            PS = [((a[0]*scale)-((sx/2)-x))*MULT,((a[1]*scale)-((sy/2)-y))*MULT] #Vertex position before rendering to screen and without scaling
            lSIZ = round(1*(a[2]/20)*scale)
            if lSIZ<=0:
                lSIZ = 1
            for b in a[3]: #Go through every vertex attached to this vertex
                if modelC[b][4]: #Inside arc (or just true when there is no arc)
                    MULT2 = 1+((modelC[b][2]*scale)/DIV) #Z multiplier for attached vertex
                    PSRaw = [((modelC[b][0]*scale)-((sx/2)-x))*MULT2,((modelC[b][1]*scale)-((sy/2)-y))*MULT2] #Vertex position of attached vertex without scaling
                    pygame.draw.line(surf,col,[PS[0]+(sx/2),PS[1]+(sy/2)],[PSRaw[0]+(sx/2),PSRaw[1]+(sy/2)],lSIZ) #Draw a line from vertex to attached vertex

def drawDevMesh(x,y,scale,surf,LINK): #Used in development only, this will draw a pixel grid for MESH
    for xp in LINK["mesh"]:
        for yp in LINK["mesh"][xp]:
            pygame.draw.rect(surf,(75,0,75),[(xp*scale*125)-x,(yp*scale*125)-y,125*scale,125*scale],1)
            surf.blit(LINK["font24"].render(str(len(LINK["mesh"][xp][yp])),16,(255,0,255)),[(xp*scale*125)-x,(yp*scale*125)-y])
            mid = [(xp*scale*125)-x+(62*scale),(yp*scale*125)-y+(62*scale)]
            for a in LINK["mesh"][xp][yp]:
                pygame.draw.line(surf, (75,0,75), mid, [(a.pos[0]*scale)-x,(a.pos[1]*scale)-y])
def drawConnection(x,y,surf,LINK): #Used in development only, will draw a graph explaining how behind SYNC is
    #The algorithms made to display this infomation are not designed to be fast!
    if LINK["multi"]==1: #Is a client
        POS,BRS = LINK["cli"].getInfo()
        MX = 1
        DR = []
        for a in BRS: #Find maximum message length
            if a!=False:
                LN = len(pickle.dumps(a))
                if LN>MX:
                    MX = LN+0
                DR.append(LN)
            else:
                DR.append(False)
        for i,a in enumerate(DR): #Draw all bars
            Height = 10
            if i==POS: #Is currently received message
                col = (0,255,0)
            elif a!=False: #Bar is awaiting to be processed
                col = (255,0,0)
            else: #Received and processed
                col = (0,0,0)
            if a!=False:
                Height = int((a/MX)*20)
                if Height<5:
                    Height = 5
            pygame.draw.line(surf,col,[x+(i*2),y],[x+(i*2),y+Height],2)
        pygame.draw.rect(surf,(255,255,0),[x,y,len(BRS)*2,20],1)
    elif LINK["multi"]==2: #Is a server
        i = 0
        for a in LINK["serv"].users: #Draw a bar graph for all users connected
            surf.blit(LINK["font24"].render(LINK["serv"].users[a].name,16,(255,255,255)),[x+10,y+5+(i*70)])
            cPos = LINK["serv"].users[a].IDRec
            IC = LINK["serv"].users[a].getIDSend()
            for i2,b in enumerate(LINK["serv"].users[a].ReceiveBuffer): #Draw a bar graph for the received buffer
                if i2==cPos: #Currently received message
                    col = (0,255,0)
                elif i2==IC: #Is the currently sent position (used for reference in anouther graph)
                    col = (0,0,255)
                elif not b is None: #Is awaiting to be processed
                    col = (255,0,0)
                else: #Processed and finished
                    col = (0,0,0)
                pygame.draw.line(surf,col,[x+(i2*2),y+25+(i*70)],[x+(i2*2),y+40+(i*70)],2)
            pygame.draw.rect(surf,(255,255,0),[x,y+25+(i*70),len(LINK["serv"].users[a].ReceiveBuffer)*2,20],1)
            MX = 1
            DR = []
            for b in LINK["serv"].users[a].SendingBuffer: #Find the maximum bar height
                if not b is None:
                    LN = len(pickle.dumps(b))
                    if LN>MX:
                        MX = LN+0
                    DR.append(LN)
                else:
                    DR.append(None)
            for i2,b in enumerate(DR): #Draw all the bars
                if b is None:
                    Height = 10
                else:
                    Height = int((b/MX)*20)
                    if Height<5:
                        Height = 5
                pygame.draw.line(surf,(255,255,255),[x+(i2*2),y+50+(i*70)],[x+(i2*2),y+50+Height+(i*70)],2)
            pygame.draw.rect(surf,(255,255,0),[x,y+50+(i*70),len(LINK["serv"].users[a].ReceiveBuffer)*2,20],1)
            b1,b2 = LINK["serv"].users[a].getBufs()
            surf.blit(LINK["font24"].render("Last send: "+str(LINK["serv"].users[a].SendingBuffer[IC-1]),16,(255,255,255)),[x+130,y+20+(i*70)])
            surf.blit(LINK["font24"].render("TCP length: "+str(b1),16,(255,255,255)),[x+130,y+40+(i*70)])
            surf.blit(LINK["font24"].render("UDP length: "+str(b2),16,(255,255,255)),[x+130,y+60+(i*70)])
            i+=1

class ParticleEffect(base.Main): #Particle effect
    def __init__(self,LINK,posx,posy,direction,spread,speed,drag=0.95,amount=20,spreadAccelerate=0,burstTime=None,lifeTime=1,posSpread=0,noPhys=False):
        self.pos = [posx,posy] #Position of the particles
        self.angle = direction #Angle to fire the particles at
        self.LINK = LINK #LINK variable
        self.__spread = spread #Particle spread (angle wise)
        self.__speed = speed #Angle fire speed
        self.__posSpread = posSpread #Spread amount whem spawned
        self.__noPhys = noPhys #Disable particle physics (colisions)
        self.__lifeTime = lifeTime #What value to delete the particles when they are less than this limit
        self.__spreadAccelerate = spreadAccelerate #Rotational acceleration (makes a spiral effect)
        self.__drag = drag #Particle drag (how fast they go slower)
        self.__burstTime = burstTime #How long to wait until bursting particles
        self.__burstWait = time.time() #Time in between bursts
        self.__particles = [] #The particles themselves
        #Syntax
        #0 = X
        #1 = Y
        #2 = Direction
        #3 = Speed
        #4 = Rotational acceleration
        #5 = Rotation direction (true/false)
        self.__amount = amount #Amount of particles
        self.__createUpdate = time.time() #Time inbetween creating a new particle
        self.__updateRate = time.time() #Time between updating every particle
        self.renderParticle = self.__defaultRender #Fucntion to call when rendering the particle
    def __defaultRender(self,x,y,scale,alpha,surf,PREF): #Default rendering function that rendered a purple circle
        pygame.draw.circle(surf,(255,0,255),[int(x),int(y)],int(2*scale*alpha))
    def loop(self,lag): #Particle physics and deletion
        RoomReferenceObject = self.getEnt("room")
        DoorReferenceObject = self.getEnt("door")
        if time.time()>self.__updateRate: #Its time to update particles
            self.__updateRate = time.time()+(1/23) #Make particles update 23 times a second.
            if self.__burstTime is None: #Normal particle fire
                if time.time()>self.__createUpdate:
                    self.__createUpdate = time.time()+(1/self.__amount)
                    PS = [self.pos[0]+random.randint(-self.__posSpread,self.__posSpread),self.pos[1]+random.randint(-self.__posSpread,self.__posSpread)]
                    self.__particles.append([PS[0],PS[1],self.angle+random.randint(-self.__spread,self.__spread)
                        ,random.randint(int(self.__speed*0.8),int(self.__speed*1.2)),0.5,random.randint(0,1)==1])
                    if self.__drag==0:
                        self.__particles[-1].append(time.time()+self.__lifeTime)
            elif time.time()>self.__burstWait: #Burst particle fire
                self.__burstWait = time.time()+(self.__burstTime*(random.randint(60,140)/100))
                for i in range(int(random.randint(5,20)*self.__burstTime)): #Create multiple particles in one go.
                    self.__particles.append([self.pos[0]+0,self.pos[1]+0,self.angle+random.randint(-self.__spread,self.__spread)
                        ,random.randint(int(self.__speed*0.8),int(self.__speed*1.2)),0.5,random.randint(0,1)==1])
                    if self.__drag==0:
                        self.__particles[-1].append(time.time()+self.__lifeTime)
            rem = [] #Particles to remove
            TIM = time.time()
            for a in self.__particles: #Physics for all particles
                a[0]+=math.cos(a[2]/180*math.pi)*a[3] #Move particle X coordinate
                a[1]+=math.sin(a[2]/180*math.pi)*a[3] #Move particle Y coordinate
                if self.__drag!=0:
                    a[3]*=self.__drag #Slow particle down
                a[4]+=self.__spreadAccelerate*((int(a[5])*2)-1) #Increase spiral rotation
                a[2]+=a[4] #Make particle rotate into a spiral
                room = self.findPosition(a,[1,1]) #Find room particle is in for particle colision
                if room!=-1 and not self.__noPhys: #Inside the map
                    if type(room)==RoomReferenceObject: #Inside a room
                        if a[0]>room.pos[0]+room.size[0]-10: #Right
                            a[0] = room.pos[0]+room.size[0]-10
                            a[2] = 180-a[2]
                        if a[1]>room.pos[1]+room.size[1]-10: #Bottom
                            a[1] = room.pos[1]+room.size[1]-10
                            a[2] = 90+a[2]
                        if a[0]<room.pos[0]+10: #Left
                            a[0] = room.pos[0]+10
                            a[2] = a[2]+180
                        if a[1]<room.pos[1]+10: #Top
                            a[1] = room.pos[1]+10
                            a[2] = 270+a[2]
                    elif room.settings["open"]: #Inside a door/airlock and it is open
                        if type(room)==DoorReferenceObject: #Is a door
                            LR = room.settings["lr"]
                        else: #Is an airlock
                            LR = room.settings["dir"]>=2
                        #Door colision
                        if not LR: #Is up to down
                            if a[0]>room.pos[0]+room.size[0]-10: #Right
                                a[0] = room.pos[0]+room.size[0]-10
                                a[2] = 180-a[2]
                            if a[0]<room.pos[0]+10: #Left
                                a[0] = room.pos[0]+10
                                a[2] = a[2]+180
                        else: #Is right to left
                            if a[1]>room.pos[1]+room.size[1]-10: #Bottom
                                a[1] = room.pos[1]+room.size[1]-10
                                a[2] = 90+a[2]
                            if a[1]<room.pos[1]+10: #Top
                                a[1] = room.pos[1]+10
                                a[2] = 270+a[2]
                if (abs(a[3])<self.__lifeTime and self.__drag!=0) or (TIM>a[-1] and self.__drag==0): #Remove the particle
                    rem.append(a)
            for a in rem: #Remove particles from particle list
                self.__particles.remove(a)
    def render(self,x,y,scale,ang,ang2=None,surf=None): #Render all particles
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        scrpos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Scroll position
        for a in self.__particles: #Loop through all particles
            if ang is None: #No view arc
                Allow = True
            else: #Inside the viewing arc of a drone/door
                Allow = self.LINK["render"].insideArc([(a[0]*scale)-scrpos[0],(a[1]*scale)-scrpos[1]],[sx/2,sy/2],ang)
            if not ang2 is None: #Inside the viewing arc of specificly a drone
                Allow = Allow and self.LINK["render"].insideArc([(a[0]*scale)-scrpos[0],(a[1]*scale)-scrpos[1]],[sx/2,sy/2],ang2)
            if Allow: #Particle is allowed to render (is inside both arcs)
                self.renderParticle((a[0]*scale)-scrpos[0],(a[1]*scale)-scrpos[1],scale,1,surf,a)

class CommandLine: #A command line interface with tabs
    def __init__(self,LINK,drones=3):
        self.__LINK = LINK
        self.tabs = [] #Variable to store all the tabs inside of.
        #Syntax:
        #0: Tab name
        #1: Contents
        #2: Damage/colour of tab
        #3: Upgrades
        #4: Is being attacked
        #5: (option) Drone object
        self.tabs.append(["SCHEMATIC",[[">",[255,255,255],False]],0,[],False]) #For the ship
        self.activeTab = 0
    def settings(self,Tab,dmg=0,attacked=False,upgrades=None): #Change settings of a tab
        if Tab<0 or Tab>=len(self.tabs): #Check if tab is valid
            self.__LINK["errorDisplay"]("Command line was asked to edit a tab but it doesen't exist.")
        else:
            self.tabs[Tab][2] = dmg #Apply damage
            self.tabs[Tab][4] = attacked == True #Being attacked
            if upgrades!=None: #Check if any upgrades need changing
                self.tabs[Tab][3] = upgrades
    def addLine(self,line,colour,flash=False,Tab=-1): #Adds a line with its colour to the command line
        if Tab==-1: #Add command to current tab
            if self.activeTab>=0 and self.activeTab<len(self.tabs): #Check if current tab is valid
                self.tabs[self.activeTab][1].append([line,colour,flash,time.time()+FLASH_TIME])
                if len(self.tabs[self.activeTab][1])>60:
                    self.tabs[self.activeTab][1].pop(0)
            else: #Display error
                self.__LINK["errorDisplay"]("Active tab in command line is invalid!")
        elif Tab>=0 and Tab<len(self.tabs): #Check if given tab is valid
            self.tabs[Tab][1].append([line,colour,flash,time.time()+FLASH_TIME])
            if len(self.tabs[Tab][1])>60:
                self.tabs[Tab][1].pop(0)
        else: #Display an error
            self.__LINK["errorDisplay"]("Given tab does not exist "+str(Tab))
    def replaceLast(self,line,col=None,tab=None,flash=None): #Changes the text at the end of the current tab command line
        if tab is None:
            TAB = self.activeTab
        else:
            TAB = tab
        if TAB>=0 and TAB<len(self.tabs): #Check if current tab is valid
            self.tabs[TAB][1][-1][0] = line
            if not col is None:
                self.tabs[TAB][1][-1][1] = col
            if not flash is None:
                self.tabs[TAB][1][-1][2] = flash
                if flash:
                    if len(self.tabs[TAB][1][-1])==4:
                        self.tabs[TAB][1][-1][3] = time.time()+FLASH_TIME
                    else:
                        self.tabs[TAB][1][-1].append(time.time()+FLASH_TIME)
        else: #Display an error
            self.__LINK["errorDisplay"]("Editing tab that doesen't exist "+str(TAB))
    def render(self,x,y,sizex,sizey,surf=None): #Render the command line
        if surf is None: #Get the main surface if none is supplied
            surf = self.__LINK["main"]
        col2 = (0,0,0) #Colour for the boarder of the command line
        for i,a in enumerate(self.tabs): #Render all tabs
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
            TX = a[0]+""
            if len(a)!=5:
                if a[5].settings["name"]!="Name":
                    TX = a[5].settings["name"]
            surf.blit(self.__LINK["font16"].render(TX,16,(255,255,255)),(x+(i*80)+3,y-15)) #Draw name of tab
            if len(a)!=5:
                H = a[5].health/a[5].settings["maxHealth"]
                if a[2]==2:
                    H = 0
                pygame.draw.polygon(surf,(0,50,0),[ [x+(i*80),y-49], [x+(i*80)+70,y-49], 
                    [x+(i*80)+(100*H)+(HB_LENG-80),y-(((HB_LENG-50)*H)+49)], [x+(i*80)+((HB_LENG-50)*H),y-(((HB_LENG-50)*H)+49)] ])
                pygame.draw.polygon(surf,(0,255,0),[ [x+(i*80),y-49], [x+(i*80)+70,y-49], [x+(i*80)+HB_LENG+20,y-HB_LENG], [x+(i*80)+HB_LENG-50,y-HB_LENG] ],2)
            for c,b in enumerate(a[3]):
                if b.damage==0:
                    if b.used:
                        col = (0,255,0)
                    else:
                        col = (255,255,255)
                elif b.damage==1:
                    col = (255,255,0)
                else:
                    col = (255,0,0)
                dr = pygame.transform.rotate(self.__LINK["font24"].render(b.displayName,16,col),45)
                surf.blit(dr,(x+(i*80)+3+(c*25),y-45-dr.get_height()))
                if "icon"+b.name in self.__LINK["content"]:
                    surf.blit(self.__LINK["content"]["icon"+b.name],(x+(i*80)+3+(c*25),y-45))
                else:
                    surf.blit(self.__LINK["content"]["iconbase"],(x+(i*80)+3+(c*25),y-45))
        pygame.draw.rect(surf,(0,0,0),[x,y,sizex,sizey]) #Draw a black rectangle so it isn't see-through
        pygame.draw.rect(surf,col2,[x,y,sizex,sizey],2) #Draw boarder for command line
        if self.activeTab>=0 and self.activeTab<len(self.tabs): #Render command lines text if the tab is valid
            #Draw command line with text wrapping
            X = x+3
            Y = y+sizey-24
            for i in range(1,60): #Go throguh 60 possible text lines (normlay it will only go to 12)
                if i>len(self.tabs[self.activeTab][1]):
                    break
                a = self.tabs[self.activeTab][1][-i]
                col = (a[1][0]+0,a[1][1]+0,a[1][2]+0)
                if a[2] and ((time.time()-int(time.time()))*2)%1>0.5: #Make text flash
                    col = (col[0]*0.5,col[1]*0.5,col[2]*0.5)
                if len(a)==4: #Stop text flashing after X amount of seconds
                    if time.time()>a[3]:
                        a[2] = False
                #Text wrapping into a list
                Split = a[0].split(" ")
                Build = ""
                words = []
                for b in Split:
                    if self.__LINK["font24"].size(Build+b+" ")[0]>sizex:
                        words.append(Build+"")
                        Build = b+" "
                    else:
                        Build += b+" "
                words.append(Build)
                words.reverse()
                #Draw the text wrap list
                for i2,b in enumerate(words):
                    surf.blit(self.__LINK["font24"].render(b,16,col),(X,Y))
                    Y -= 18
                    if Y<y: #Going off the top of the command line window
                        break
                if Y<y: #Going off the top of the command line window
                    break

class DebugServer: #This is a tkinter window that is used to debug the server and show entities.
    def __init__(self,LINK):
        pygame.init() #Initialize pygame
        self.__LINK = LINK
        LINK["DEVDIS"] = True
        self.__main = pygame.display.set_mode([500,400]) #Make a pygame window
        files = os.listdir("content")
        LINK["content"] = {} #Images
        LINK["models"] = {} #3D models
        for a in files:
            if a[-4:]==".png":
                LINK["content"][a[:-4]] = pygame.image.load("content/"+a)
            elif a[-4:]==".obj":
                LINK["models"][a[:-4]] = openModel("content/"+a)
        LINK["cont"] = {} #This is used for storing "content" in LINK but is resized every frame.
        LINK["font24"] = pygame.font.Font("comandFont.ttf",24)
        LINK["font16"] = pygame.font.Font("comandFont.ttf",16)
        LINK["font42"] = pygame.font.Font("comandFont.ttf",42)
        self.__textEnt = screenLib.TextEntry(0,0,LINK,200,True,"Command line",self.COM) #Command line entry
        self.__pos = [0,0]
        self.__zoom = 1
        self.__rdn = Scematic(LINK)
        self.__av = 60 #Average FPS
        self.__lastTime = time.time()
        pygame.display.set_caption("Server debug window")
        LINK["main"] = self.__main
    def COM(self,LNK,text):
        self.__LINK["world"].doCommand(text,-1)
        self.__textEnt.text = ""
    def render(self,MAP):
        self.__rdn.ents = MAP
        lag = (time.time()-self.__lastTime)*30 # Used to vary lag
        self.__lastTime = time.time()
        EV = []
        for event in pygame.event.get():
            EV.append(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.__pos[1]+=15
                elif event.key == pygame.K_DOWN:
                    self.__pos[1]-=15
                elif event.key == pygame.K_LEFT:
                    self.__pos[0]+=15
                elif event.key == pygame.K_RIGHT:
                    self.__pos[0]-=15
                elif event.key == pygame.K_w:
                    self.__zoom /= 2
                elif event.key == pygame.K_s:
                    self.__zoom *= 2
        mouseRaw = pygame.mouse.get_pressed()
        mouse = [mouseRaw[0]]+list(pygame.mouse.get_pos())+[mouseRaw[1],mouseRaw[2]]
        self.__textEnt.loop(mouse,EV)
        self.__main.fill((0,0,0))
        self.__rdn.render(self.__pos[0],self.__pos[1],self.__zoom,self.__main)
        self.__textEnt.render()
        self.__main.blit(self.__LINK["font24"].render("FPS: "+str(int(30/lag)),16,(255,0,255)),[10,60])
        self.__av = ((self.__av*800) + int(30/lag))/801
        self.__main.blit(self.__LINK["font24"].render("AVERAGE FPS: "+str(int(self.__av)),16,(255,0,255)),[10,75])
        self.__main.blit(self.__LINK["font24"].render("LAG: "+str(lag),16,(255,0,255)),[10,90])
        drawConnection(10,120,self.__main,self.__LINK)
        pygame.display.flip()
