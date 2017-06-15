import pygame, server
pygame.init()

FPS = 120
RESLUTION = [800,500]

def ERROR(*info): #This function is called whenever an unexspected error occures. It is mainly so it can be displayed on the screen without the game crashing
    print("Err: ",info) #Tempory

server.ERROR = ERROR
LINK = {} #This is a global variable for allowing controll over the whole program through one variable. Every class in this program should have a link to this!
LINK["errorDisplay"] = ERROR
LINK["server"] = server.Server(LINK,"169.254.21.86")
LINK["server"].SYNC["test"] = 32


main = pygame.display.set_mode(RESLUTION)
pygame.display.set_caption("REMOTE")
clock = pygame.time.Clock()
fontTest = pygame.font.SysFont("impact",16)

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                LINK["server"].SYNC["test"]+=1
            elif event.key == pygame.K_DOWN:
                LINK["server"].SYNC["test"]-=1
    LINK["server"].loop()
    main.fill((0,0,0))
    main.blit(fontTest.render(str(LINK["server"].SYNC["test"]),16,(255,255,255)),[20,20])
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
LINK["server"].close()
