import pygame
pygame.init()

FPS = 60
RESLUTION = [800,500]


main = pygame.display.set_mode(RESLUTION)
pygame.display.set_caption("REMOTE")
clock = pygame.time.Clock()

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    
    main.fill((0,0,0))
    
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
