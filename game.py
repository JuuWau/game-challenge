class Game:
    def __init__(self):
        self.player = Player(...)
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.state = "GAMEPLAY"

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
