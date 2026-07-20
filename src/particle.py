# Shared particle system used across the game for particle-based effects.

import pygame
import random
import math


class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime, size=4, gravity=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.start_size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity

    @property
    def is_dead(self):
        return self.lifetime <= 0

    def update(self):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        life_ratio = max(0.0, self.lifetime / self.max_lifetime)
        self.size = self.start_size * life_ratio

    def draw(self, screen):
        if self.is_dead or self.size < 0.5:
            return
        alpha = max(0, int(255 * (self.lifetime / self.max_lifetime)))
        size = max(1, int(self.size))
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (size, size), size)
        screen.blit(surf, (int(self.x - size), int(self.y - size)))


class ParticleEmitter:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, count, color, lifetime, size=4,
              speed_range=(1, 3), angle_range=(0, 360), gravity=0.0):
        for _ in range(count):
            angle = math.radians(random.uniform(*angle_range))
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.randint(int(lifetime * 0.7), int(lifetime * 1.3))
            self.particles.append(Particle(x, y, vx, vy, color, life, size, gravity))

    def dust_burst(self, x, y, color=(150, 130, 100)):
        # boss landing / ground slam impact
        self.emit(x, y, count=30, color=color, lifetime=35, size=6,
                   speed_range=(2, 6), angle_range=(200, 340), gravity=0.15)

    def petal_storm(self, screen_width, count=100,
                      colors=((255, 214, 232), (255, 255, 255), (255, 182, 213))):
        # victory effect on boss defeat
        for _ in range(count):
            x = random.uniform(0, screen_width)
            y = random.uniform(-40, 0)
            color = random.choice(colors)
            self.particles.append(
                Particle(x, y, random.uniform(-0.6, 0.6), random.uniform(1.0, 2.5),
                          color, lifetime=180, size=random.uniform(3, 6), gravity=0.1)
            )

    def glow_pulse(self, x, y, frame, radius=30, color=(255, 165, 0)):
        # pulsing glow circle, not a particle (used for the Phase 2 glowing cap)
        glow = 128 + int(127 * math.sin(frame * 0.1))
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (color[0], min(255, glow), color[2], 80),
                            (radius, radius), radius)
        return surf

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if not p.is_dead]

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)

    def clear(self):
        self.particles = []
