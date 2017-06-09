import pygame, server
pygame.init()

FPS = 120
RESLUTION = [800,500]

servTest = server.Server("127.0.0.1")

main = pygame.display.set_mode(RESLUTION)
pygame.display.set_caption("REMOTE")
clock = pygame.time.Clock()
fontTest = pygame.font.SysFont("impact",16)

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    servTest.loop()
    main.fill((0,0,0))

    for i,b in enumerate(servTest.users):
        a = servTest.users[b]
        main.blit(fontTest.render( str(i)+": "+a.ip+" - "+str(a.ping) ,16,(255,255,255)),[10,10+(i*12)])

    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
servTest.close()