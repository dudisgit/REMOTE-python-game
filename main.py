import pygame,client,time,screenLib,math
pygame.init()

FPS = 30
RESLUTION = [800,500]

def ERROR(*info): #This function is called whenever an unexspected error occures. It is mainly so it can be displayed on the screen without the game crashing
    print("Err: ",info) #Tempory

LINK = {} #This is a global variable for allowing controll over the whole program through one variable. Every class in this program should have a link to this!
LINK["errorDisplay"] = ERROR
LINK["reslution"] = RESLUTION
LINK["DEV"] = True #Development mode, this will stop the game when errors occur.

main = pygame.display.set_mode(RESLUTION)
pygame.display.set_caption("REMOTE")
clock = pygame.time.Clock()
LINK["main"] = main
LINK["font24"] = pygame.font.Font("comandFont.ttf",24)


run = True
lastTime = time.time()-0.1
while run:
    lag = (time.time()-lastTime)*FPS
    lastTime = time.time()
    KeyEvent = [] #A list of key events to send to all users
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            KeyEvent.append(event)
        if event.type == 6: #Mouse wheel
            KeyEvent.append(event)
    mouse = [pygame.mouse.get_pressed()[0]]+list(pygame.mouse.get_pos())
    main.fill((0,0,0))
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
