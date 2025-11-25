# enemy.py
import pygame
import math
import random

class Enemy(pygame.Rect):
    def __init__(self, x, y, size, speed):
        super().__init__(x, y, size, size)
        self.pos = pygame.math.Vector2(float(x), float(y))
        self.speed = speed
        self.hit_timer = 0
        self.color = (255, 0, 0)
        self.hp = 1

    def move_towards_player(self, player, enemies, obstacles=[]):
        center = self.pos + pygame.math.Vector2(self.width / 2, self.height / 2)
        target = pygame.math.Vector2(player.centerx, player.centery)
        to_target = target - center

        if to_target.length_squared() < 0.01:
            return

        direction = to_target.normalize()
        desired = direction * self.speed

        separation = pygame.math.Vector2(0, 0)
        for other in enemies:
            if other is self:
                continue
            other_center = pygame.math.Vector2(other.x + other.width/2, other.y + other.height/2)
            offset = center - other_center
            dist = offset.length()
            if dist > 0 and dist < max(self.width, self.height):
                separation += (offset.normalize() * (max(self.width, self.height) - dist) * 0.02)

        desired += separation

        def test_rect_at(pos_vec):
            return pygame.Rect(int(pos_vec.x), int(pos_vec.y), self.width, self.height)

        new_pos = self.pos + desired
        test_rect = test_rect_at(new_pos)
        if not any(test_rect.colliderect(obs) for obs in obstacles):
            self.pos = new_pos
            self._sync_rect()
            return

        perp = pygame.math.Vector2(-desired.y, desired.x)
        if perp.length_squared() > 0:
            perp = perp.normalize() * self.speed * 0.6
            sides = [perp, -perp] if random.random() < 0.5 else [-perp, perp]
            for s in sides:
                np2 = self.pos + s
                tr2 = test_rect_at(np2)
                if not any(tr2.colliderect(obs) for obs in obstacles):
                    self.pos = np2
                    self._sync_rect()
                    return

        for angle in (15, -15, 30, -30, 45, -45):
            alt = desired.rotate(angle)
            np3 = self.pos + alt
            tr3 = test_rect_at(np3)
            if not any(tr3.colliderect(obs) for obs in obstacles):
                self.pos = np3
                self._sync_rect()
                return

        self.pos -= desired * 0.5
        self._sync_rect()

    def _sync_rect(self):
        self.x = int(self.pos.x)
        self.y = int(self.pos.y)

    @staticmethod
    def spawn(size, speed, width, height, existing):
        for _ in range(50):
            side = random.choice(["top", "left", "right", "bottom"])
            if side == "top":
                x = random.randint(0, width - size)
                y = -size
            elif side == "bottom":
                x = random.randint(0, width - size)
                y = height
            elif side == "left":
                x = -size
                y = random.randint(0, height - size)
            else:
                x = width
                y = random.randint(0, height - size)

            new_enemy = Enemy(x, y, size, speed)
            if not any(new_enemy.colliderect(e) for e in existing):
                return new_enemy
        return None

    def hit_react(self, bx, by):
        self.hp -= 1
        dx = (self.pos.x) - bx
        dy = (self.pos.y) - by
        dist = max(math.hypot(dx, dy), 1)
        self.pos.x += (dx / dist) * 40
        self.pos.y += (dy / dist) * 40

        self.hit_timer = 6
        self.color = (255, 255, 0)
        self._sync_rect()
        return self.hp <= 0

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self)
        if self.hit_timer > 0:
            self.hit_timer -= 1
            if self.hit_timer == 0:
                self.color = (255, 0, 0)
