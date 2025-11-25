import pygame
import math

class Bullet:
    def __init__(self, x, y, target_x, target_y, bullet_size, bullet_speed):
        self.rect = pygame.Rect(x-bullet_size//2, y-bullet_size//2, bullet_size, bullet_size)
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        self.vel_x = bullet_speed * dx / dist
        self.vel_y = bullet_speed * dy / dist

    def move(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

    def offscreen(self, WIDTH, HEIGHT):
        return (self.rect.x < 0 or self.rect.x > WIDTH or 
                self.rect.y < 0 or self.rect.y > HEIGHT)
