import math
import os
import random

import pygame

from settings import (
    BASE_DIR,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GROUND_Y,
    VINE_WHIP_DAMAGE,
    SEED_SHOT_DAMAGE,
)


class SporeBurst:
    """Member 2 effect: blue-green particles emitted when an enemy is hit."""

    def __init__(self, x, y, tint=(70, 220, 190), count=26):
        self.particles = []
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1.8, 5.5)
            self.particles.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": random.randint(22, 34),
                    "max_life": 34,
                    "radius": random.randint(3, 7),
                    "color": tint,
                }
            )

    @property
    def alive(self):
        return bool(self.particles)

    def update(self):
        for particle in self.particles[:]:
            particle["life"] -= 1
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["vy"] += 0.08
            particle["radius"] *= 0.96
            if particle["life"] <= 0 or particle["radius"] < 0.5:
                self.particles.remove(particle)

    def draw(self, screen):
        for particle in self.particles:
            alpha_ratio = max(0, particle["life"] / particle["max_life"])
            radius = max(1, int(particle["radius"]))
            color = particle["color"]
            pygame.draw.circle(
                screen,
                (
                    min(255, int(color[0] + 40 * alpha_ratio)),
                    min(255, int(color[1] + 25 * alpha_ratio)),
                    min(255, int(color[2] + 20 * alpha_ratio)),
                ),
                (int(particle["x"]), int(particle["y"])),
                radius,
            )


class BlightBeetle(pygame.sprite.Sprite):
    """Straight-line Level 2 enemy with a normal and armoured variant."""

    def __init__(self, x, y, variant="standard", direction=-1):
        super().__init__()
        self.variant = variant
        self.direction = 1 if direction >= 0 else -1
        self.max_hp = 50 if variant == "armoured" else 30
        self.hp = self.max_hp
        self.damage = 12 if variant == "armoured" else 8
        self.speed = 1.4 if variant == "armoured" else 2.2
        self.score_value = 20 if variant == "armoured" else 10
        self.platform_flash = 5 if variant == "armoured" else 0
        self.damage_cooldown = 0
        self.hit_flash = 0

        self.frames = self._load_frames()
        self.frame_index = 0.0
        self.animation_speed = 0.12 if variant == "armoured" else 0.16
        self.image = self.frames[0]
        self.rect = self.image.get_rect(midbottom=(x, y))

    def _load_frames(self):
        enemy_folder = "level2_armoured_beetle" if self.variant == "armoured" else "level2_blight_beetle"
        path = os.path.join(BASE_DIR, "assets", "sprites", "enemies", enemy_folder, "Walk.png")
        frames = []
        if os.path.exists(path):
            sheet = pygame.image.load(path).convert_alpha()
            frame_count = 6
            frame_width = sheet.get_width() // frame_count
            frame_height = sheet.get_height()
            scale = 1.45 if self.variant == "standard" else 1.55
            for index in range(frame_count):
                frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame.blit(sheet, (0, 0), (index * frame_width, 0, frame_width, frame_height))
                frame = pygame.transform.scale(
                    frame,
                    (int(frame_width * scale), int(frame_height * scale)),
                )
                frames.append(frame)

        if not frames:
            size = (70, 42) if self.variant == "standard" else (86, 52)
            base = pygame.Surface(size, pygame.SRCALPHA)
            body = (65, 150, 80) if self.variant == "standard" else (65, 95, 150)
            pygame.draw.ellipse(base, body, base.get_rect())
            pygame.draw.circle(base, (30, 35, 45), (size[0] - 14, size[1] // 2), 8)
            frames = [base]
        return frames

    def update(self, player=None, platforms=None):
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1

        self.rect.x += int(self.speed * self.direction)
        if self.rect.left <= -40:
            self.direction = 1
        elif self.rect.right >= SCREEN_WIDTH + 40:
            self.direction = -1

        if platforms:
            self._keep_on_platform(platforms)

        self.frame_index = (self.frame_index + self.animation_speed) % len(self.frames)
        frame = self.frames[int(self.frame_index)]
        if self.hit_flash:
            flash = frame.copy()
            flash.fill((80, 220, 200, 90), special_flags=pygame.BLEND_RGBA_ADD)
            frame = flash
        self.image = pygame.transform.flip(frame, self.direction < 0, False)

    def _keep_on_platform(self, platforms):
        for platform in platforms:
            on_top = abs(self.rect.bottom - platform.top) <= 4
            if on_top and self.rect.centerx < platform.left + 18:
                self.direction = 1
            elif on_top and self.rect.centerx > platform.right - 18:
                self.direction = -1

    def take_hit(self, damage):
        self.hp -= damage
        self.hit_flash = 8
        return self.hp <= 0


class WaveSpawner:
    """Timer-based Level 2 wave spawner."""

    WAVE_PLANS = [
        [("standard", 3), ("armoured", 1)],
        [("standard", 2), ("armoured", 3)],
        [("armoured", 4), ("standard", 2)],
    ]

    def __init__(self):
        self.wave_index = 0
        self.pending = []
        self.spawn_timer = 0
        self.spawn_interval = 75
        self.completed = False
        self.active = False

    def start_next_wave(self):
        if self.wave_index >= len(self.WAVE_PLANS):
            self.completed = True
            self.active = False
            return

        self.pending = []
        for variant, amount in self.WAVE_PLANS[self.wave_index]:
            self.pending.extend([variant] * amount)
        random.shuffle(self.pending)
        self.spawn_timer = 0
        self.spawn_interval = max(50, 85 - self.wave_index * 12)
        self.active = True

    def update(self, enemy_group, platforms):
        if self.completed:
            return
        if not self.active and not enemy_group:
            self.start_next_wave()
        if not self.active:
            return

        self.spawn_timer += 1
        if self.pending and self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            variant = self.pending.pop(0)
            spawn_from_left = random.choice([True, False])
            x = -30 if spawn_from_left else SCREEN_WIDTH + 30
            direction = 1 if spawn_from_left else -1
            y = GROUND_Y
            if random.random() < 0.35:
                platform = random.choice(platforms)
                y = platform.top
                x = platform.left + 40 if spawn_from_left else platform.right - 40
            enemy_group.add(BlightBeetle(x, y, variant, direction))

        if not self.pending and not enemy_group:
            self.wave_index += 1
            self.active = False
            if self.wave_index >= len(self.WAVE_PLANS):
                self.completed = True


class Level2Scene:
    """Member 2 Dark Forest scene: platforms, enemies, overlay, and effects."""

    def __init__(self):
        self.platforms = [
            pygame.Rect(210, 470, 260, 24),
            pygame.Rect(560, 370, 260, 24),
            pygame.Rect(900, 500, 240, 24),
        ]
        self.enemies = pygame.sprite.Group()
        self.spawner = WaveSpawner()
        self.effects = []
        self.platform_flash = {index: 0 for index in range(len(self.platforms))}
        self.door_rect = pygame.Rect(SCREEN_WIDTH - 85, GROUND_Y - 110, 58, 110)
        self.level_cleared = False
        self.dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.dark_overlay.fill((0, 0, 0, 110))
        self.background = self._load_background()
        self.mushrooms = [
            (155, GROUND_Y - 14, 12),
            (500, 455, 10),
            (705, 355, 14),
            (1030, 485, 12),
            (1180, GROUND_Y - 18, 16),
        ]

    def _load_background(self):
        candidates = [
            os.path.join(BASE_DIR, "assets", "sprites", "backgrounds", "level2_dark_forest", "background.png"),
        ]
        for path in candidates:
            if os.path.exists(path):
                image = pygame.image.load(path).convert()
                return pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.fill((18, 46, 38))
        return surface

    def reset(self, player):
        self.enemies.empty()
        self.effects.clear()
        self.spawner = WaveSpawner()
        self.level_cleared = False
        if player:
            player.rect.x = 80
            player.rect.bottom = GROUND_Y
            player.ground_y = GROUND_Y

    def update(self, player):
        self._resolve_platform_collision(player)
        self.spawner.update(self.enemies, self.platforms)
        self.enemies.update(player, self.platforms)
        self._handle_player_contact(player)
        gained_score = self._handle_attacks(player)

        for index in self.platform_flash:
            if self.platform_flash[index] > 0:
                self.platform_flash[index] -= 1
        for effect in self.effects[:]:
            effect.update()
            if not effect.alive:
                self.effects.remove(effect)

        if self.spawner.completed and not self.enemies:
            self.level_cleared = True
            if player.rect.colliderect(self.door_rect):
                return gained_score, "LEVEL_COMPLETE"
        return gained_score, None

    def _resolve_platform_collision(self, player):
        if not player:
            return
        player.ground_y = GROUND_Y
        if getattr(player, "vy", 0) < 0:
            return
        for platform in self.platforms:
            horizontal_overlap = player.rect.right > platform.left and player.rect.left < platform.right
            close_to_top = player.rect.bottom >= platform.top and player.rect.bottom <= platform.top + 22
            if horizontal_overlap and close_to_top:
                player.rect.bottom = platform.top
                player.vy = 0
                player.is_on_ground = True
                player.ground_y = platform.top
                return

    def _handle_player_contact(self, player):
        if not player:
            return
        for enemy in self.enemies:
            if enemy.damage_cooldown <= 0 and enemy.rect.colliderect(player.rect):
                result = player.take_damage(enemy.damage)
                enemy.damage_cooldown = 55
                if result == "GAME_OVER":
                    break

    def _handle_attacks(self, player):
        gained_score = 0
        if not player:
            return gained_score

        hitbox = player.create_attack_hitbox() if getattr(player, "is_attacking", False) else None
        for enemy in list(self.enemies):
            if hitbox and hitbox.colliderect(enemy.rect):
                gained_score += self._damage_enemy(enemy, VINE_WHIP_DAMAGE)

            for seed in player.seed_shots[:]:
                if seed.rect.colliderect(enemy.rect):
                    if seed in player.seed_shots:
                        player.seed_shots.remove(seed)
                    gained_score += self._damage_enemy(enemy, SEED_SHOT_DAMAGE)
                    break
        return gained_score

    def _damage_enemy(self, enemy, damage):
        self.effects.append(SporeBurst(enemy.rect.centerx, enemy.rect.centery))
        defeated = enemy.take_hit(damage)
        if not defeated:
            return 0
        score = enemy.score_value
        self._flash_platform_under(enemy)
        enemy.kill()
        return score

    def _flash_platform_under(self, enemy):
        if enemy.platform_flash <= 0:
            return
        for index, platform in enumerate(self.platforms):
            if platform.collidepoint(enemy.rect.centerx, enemy.rect.bottom + 4):
                self.platform_flash[index] = enemy.platform_flash

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        pygame.draw.rect(screen, (30, 55, 38), (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
        self._draw_mushroom_glow(screen)
        self._draw_platforms(screen)
        self.enemies.draw(screen)
        for enemy in self.enemies:
            self._draw_enemy_hp(screen, enemy)
        for effect in self.effects:
            effect.draw(screen)
        if self.level_cleared:
            self._draw_door(screen)
        screen.blit(self.dark_overlay, (0, 0))

    def _draw_platforms(self, screen):
        for index, platform in enumerate(self.platforms):
            color = (245, 245, 255) if self.platform_flash[index] else (76, 59, 44)
            pygame.draw.rect(screen, color, platform, border_radius=4)
            pygame.draw.rect(screen, (42, 32, 28), platform, 2, border_radius=4)
            moss = pygame.Rect(platform.left, platform.top, platform.width, 5)
            pygame.draw.rect(screen, (62, 120, 72), moss, border_radius=3)

    def _draw_mushroom_glow(self, screen):
        for x, y, radius in self.mushrooms:
            glow = pygame.Surface((radius * 8, radius * 8), pygame.SRCALPHA)
            center = (radius * 4, radius * 4)
            pygame.draw.circle(glow, (120, 210, 255, 45), center, radius * 4)
            pygame.draw.circle(glow, (185, 245, 255, 120), center, radius * 2)
            screen.blit(glow, (x - center[0], y - center[1]))
            pygame.draw.rect(screen, (205, 235, 220), (x - 3, y, 6, 14), border_radius=3)
            pygame.draw.ellipse(screen, (120, 210, 255), (x - radius, y - radius, radius * 2, radius))

    def _draw_enemy_hp(self, screen, enemy):
        if enemy.hp >= enemy.max_hp:
            return
        bar_width = 46
        bar_rect = pygame.Rect(0, 0, bar_width, 5)
        bar_rect.midbottom = (enemy.rect.centerx, enemy.rect.top - 6)
        pygame.draw.rect(screen, (30, 30, 34), bar_rect)
        fill = bar_rect.copy()
        fill.width = max(0, int(bar_width * enemy.hp / enemy.max_hp))
        pygame.draw.rect(screen, (75, 230, 185), fill)

    def _draw_door(self, screen):
        pygame.draw.rect(screen, (24, 45, 38), self.door_rect, border_radius=6)
        pygame.draw.rect(screen, (100, 230, 190), self.door_rect, 3, border_radius=6)
        glow = pygame.Surface((120, 170), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (80, 220, 190, 55), (0, 0, 120, 170))
        screen.blit(glow, (self.door_rect.centerx - 60, self.door_rect.centery - 85))
