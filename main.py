import pygame, server
pygame.init()

FPS = 120
RESLUTION = [800,500]

servTest = server.Server("169.254.178.71")

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

    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
servTest.close()