import pygame
import os
import sys

def asset_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

pygame.mixer.init()
player_hurt_sound = pygame.mixer.Sound(asset_path("assets/hurt.mp3"))
player_hurt_sound.set_volume(0.5)

class Player(pygame.Rect):
    def __init__(self, x, y, size, speed):
        super().__init__(x, y, size, size)
        self.speed = speed
        self.vel_x = 0
        self.vel_y = 0
        self.life = 3
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_cooldown = 1000

    def handle_input(self, WIDTH, HEIGHT):
        keys = pygame.key.get_pressed()
        self.velocity = pygame.math.Vector2(0, 0)

        if keys[pygame.K_w]:
            self.velocity.y = -1
        if keys[pygame.K_s]:
            self.velocity.y = 1
        if keys[pygame.K_a]:
            self.velocity.x = -1
        if keys[pygame.K_d]:
            self.velocity.x = 1

        if self.velocity.length() > 0:
            self.velocity = self.velocity.normalize() * self.speed

    def update_invincible(self):
        if self.invincible and pygame.time.get_ticks() - self.invincible_timer >= self.invincible_cooldown:
            self.invincible = False

    def take_damage(self):
        if not self.invincible:
            player_hurt_sound.play()
            self.life -= 1
            self.invincible = True
            self.invincible_timer = pygame.time.get_ticks()

    def move_and_collide(self, obstacles, WIDTH, HEIGHT):
        self.x += self.velocity.x
        for box in obstacles:
            if self.colliderect(box):
                if self.velocity.x > 0:
                    self.right = box.left
                elif self.velocity.x < 0:
                    self.left = box.right

        self.y += self.velocity.y
        for box in obstacles:
            if self.colliderect(box):
                if self.velocity.y > 0:
                    self.bottom = box.top
                elif self.velocity.y < 0:
                    self.top = box.bottom

        if self.left < 0:
            self.left = 0
        if self.right > WIDTH:
            self.right = WIDTH
        if self.top < 0:
            self.top = 0
        if self.bottom > HEIGHT:
            self.bottom = HEIGHT
