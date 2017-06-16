import pygame,client,time
pygame.init()

FPS = 30
RESLUTION = [800,500]

def ERROR(*info): #This function is called whenever an unexspected error occures. It is mainly so it can be displayed on the screen without the game crashing
    print("Err: ",info) #Tempory


pos = [0,0]

LINK = {} #This is a global variable for allowing controll over the whole program through one variable. Every class in this program should have a link to this!
LINK["errorDisplay"] = ERROR
cl = client.Client("169.254.227.104")
if cl.failConnect:
    print("Fail")
    stop = stop
else:
    print("Connected")

main = pygame.display.set_mode(RESLUTION)
pygame.display.set_caption("REMOTE")
clock = pygame.time.Clock()
fontTest = pygame.font.SysFont("impact",16)
keys = {}
keys[pygame.K_UP] = False
keys[pygame.K_DOWN] = False
keys[pygame.K_LEFT] = False
keys[pygame.K_RIGHT] = False

cl.SYNC[client.selfIp] = {}
cl.SYNC[client.selfIp]["x"] = 0.0
cl.SYNC[client.selfIp]["y"] = 0.0
run = True
lastTime = time.time()-0.1
while run:
    lag = (time.time()-lastTime)*FPS
    lastTime = time.time()
    cl.loop()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN:
            keys[event.key] = True
        elif event.type == pygame.KEYUP:
            keys[event.key] = False
    if keys[pygame.K_LEFT]:
        pos[0]-=lag
        if pos[0]<0:
            pos[0] = 0.0
    if keys[pygame.K_RIGHT]:
        pos[0]+=lag
        if pos[0]>RESLUTION[0]:
            pos[0] = float(RESLUTION[0])
    if keys[pygame.K_UP]:
        pos[1]-=lag
        if pos[1]<0:
            pos[1] = 0.0
    if keys[pygame.K_DOWN]:
        pos[1]+=lag
        if pos[1]>RESLUTION[1]:
            pos[1] = float(RESLUTION[1])
    cl.SYNC[client.selfIp]["x"] = pos[0]
    cl.SYNC[client.selfIp]["y"] = pos[1]
    main.fill((0,0,0))

    for a in cl.SYNC:
        if a==client.selfIp:
            pygame.draw.rect(main,(0,255,0),[int(cl.SYNC[a]["x"]),int(cl.SYNC[a]["y"]),5,5])
        else:
            pygame.draw.rect(main,(255,0,0),[int(cl.SYNC[a]["x"]),int(cl.SYNC[a]["y"]),5,5])
        main.blit(fontTest.render(a,16,(0,0,255)),[int(cl.SYNC[a]["x"]),int(cl.SYNC[a]["y"])])

    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
