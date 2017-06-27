import pygame,client,time,screenLib
pygame.init()

FPS = 30
RESLUTION = [800,500]

def ERROR(*info): #This function is called whenever an unexspected error occures. It is mainly so it can be displayed on the screen without the game crashing
    print("Err: ",info) #Tempory


LINK = {} #This is a global variable for allowing controll over the whole program through one variable. Every class in this program should have a link to this!
LINK["errorDisplay"] = ERROR
LINK["reslution"] = RESLUTION

main = pygame.display.set_mode(RESLUTION)
pygame.display.set_caption("REMOTE")
clock = pygame.time.Clock()
LINK["main"] = main
LINK["font24"] = pygame.font.Font("comandFont.ttf",24)

test = screenLib.Screen(LINK)
test.addItem(screenLib.Button,10,10,"Testing")

run = True
lastTime = time.time()-0.1
while run:
    lag = (time.time()-lastTime)*FPS
    lastTime = time.time()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    main.fill((0,0,0))
    test.render()
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
