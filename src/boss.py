# Level 4 - Ancient Garden Arena. Final boss: The Withered King.

import pygame
import os
import math
import random
from settings import *
from particle import ParticleEmitter

# LPC sheet layout: 24 cols x 66 rows, 64px cells
LPC_CELL = 64
SHEET_PATH = os.path.join(BASE_DIR, "assets", "sprites", "enemies", "Level4_Boss", "withered_king.png")

ANIM_ROWS = {
    'spellcast': 0, 'thrust': 4, 'walk': 8, 'slash': 12, 'shoot': 16,
    'hurt': 20, 'climb': 21, 'idle': 22, 'jump': 26,
    'sit': 30, 'emote': 34, 'run': 38, 'combat_idle': 42,
    'backslash': 46, 'halfslash': 50,
}
ANIM_FRAMES = {
    'spellcast': 7, 'thrust': 8, 'walk': 9, 'slash': 6, 'shoot': 13,
    'hurt': 6, 'climb': 6, 'idle': 2, 'jump': 5,
    'sit': 3, 'emote': 3, 'run': 8, 'combat_idle': 2,
    'backslash': 13, 'halfslash': 6,
}
SINGLE_ROW_ANIMS = ('hurt', 'climb')          # no directional variants
DIRECTION_ROW_OFFSET = {'up': 0, 'left': 1, 'down': 2, 'right': 3}


class LPCSpriteSheet:
    # Loads the boss spritesheet and slices animations on demand.
    # Falls back to placeholder frames if the PNG isn't in assets/ yet.

    def __init__(self, path=SHEET_PATH, cell=LPC_CELL, scale=2):
        self.cell = cell
        self.scale = scale
        self.cache = {}
        self.sheet = None
        if os.path.exists(path):
            self.sheet = pygame.image.load(path).convert_alpha()

    def get_animation(self, anim_name, direction='left'):
        key = (anim_name, direction)
        if key in self.cache:
            return self.cache[key]

        if self.sheet is None:
            frames = self._placeholder_frames(anim_name)
            self.cache[key] = frames
            return frames

        base_row = ANIM_ROWS[anim_name]
        n_frames = ANIM_FRAMES[anim_name]
        row = base_row if anim_name in SINGLE_ROW_ANIMS else base_row + DIRECTION_ROW_OFFSET.get(direction, 1)

        frames = []
        size = self.cell * self.scale
        for i in range(n_frames):
            frame = pygame.Surface((self.cell, self.cell), pygame.SRCALPHA)
            frame.blit(self.sheet, (0, 0), (i * self.cell, row * self.cell, self.cell, self.cell))
            if self.scale != 1:
                frame = pygame.transform.scale(frame, (size, size))
            frames.append(frame)
        self.cache[key] = frames
        return frames

    def _placeholder_frames(self, anim_name):
        size = self.cell * self.scale
        n = ANIM_FRAMES.get(anim_name, 2)
        frames = []
        for i in range(n):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            sway = int(6 * math.sin(i * 1.5))
            pygame.draw.circle(surf, (110, 75, 50), (size // 2, size // 2 - 20), size // 4)
            pygame.draw.rect(surf, (90, 60, 40),
                              (size // 2 - 20 + sway, size // 2, 40, size // 2 - 10), border_radius=6)
            frames.append(surf)
        return frames


class ScreenShake:
    # main.py reads .offset each frame and shifts the arena surface by it.

    def __init__(self):
        self.timer = 0
        self.max_timer = 1
        self.intensity = 0

    def trigger(self, intensity=14, duration=14):
        self.timer = duration
        self.max_timer = duration
        self.intensity = intensity

    def update(self):
        if self.timer > 0:
            self.timer -= 1

    @property
    def is_active(self):
        return self.timer > 0

    @property
    def offset(self):
        if self.timer <= 0:
            return (0, 0)
        power = self.intensity * (self.timer / self.max_timer)
        return (random.uniform(-power, power), random.uniform(-power, power))


class PhaseFlash:
    # Full-screen color flash for the Phase 2 transition, fades over duration.

    def __init__(self):
        self.timer = 0
        self.max_timer = 1
        self.color = (255, 110, 40)

    def trigger(self, duration=30, color=(255, 110, 40)):
        self.timer = duration
        self.max_timer = duration
        self.color = color

    def update(self):
        if self.timer > 0:
            self.timer -= 1

    @property
    def is_active(self):
        return self.timer > 0

    def draw(self, screen):
        if self.timer <= 0:
            return
        alpha = int(160 * (self.timer / self.max_timer))
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((*self.color, alpha))
        screen.blit(surf, (0, 0))


SFX_FOLDER = os.path.join(BASE_DIR, "assets", "audio")

# base filenames only - loader tries several extensions and uses whichever exists
SFX_BASENAMES = {
    'slam': 'sfx_boss_slam',
    'landing': 'sfx_boss_landing',
    'laser_charge': 'sfx_boss_laser_charge',
    'laser_fire': 'sfx_laser_fire',
    'roar': 'sfx_boss_roar',
    'hit': 'sfx_boss_hit',
    'death': 'sfx_boss_death',
    'basic_attack': 'sfx_boss_basic_attack',
}
SFX_EXTENSIONS = ('.wav',)


class BossSFX:
    # Loads one-shot sound effects. Missing files are skipped so the game
    # still runs before audio assets are added.

    def __init__(self):
        self.sounds = {}
        for key, basename in SFX_BASENAMES.items():
            for ext in SFX_EXTENSIONS:
                path = os.path.join(SFX_FOLDER, basename + ext)
                if os.path.exists(path):
                    try:
                        self.sounds[key] = pygame.mixer.Sound(path)
                    except pygame.error as e:
                        print(f"SFX failed to load ({basename + ext}): {e}")
                    break

    def play(self, key, volume=0.7, fallback=None):
        sound = self.sounds.get(key)
        if sound is None and fallback:
            sound = self.sounds.get(fallback)
        if sound:
            sound.set_volume(volume)
            sound.play()


# ---- basic attack: root projectile ----
class RootProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, speed=8):
        super().__init__()
        self.image = pygame.Surface((26, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (92, 64, 51), (0, 0, 26, 14))
        pygame.draw.circle(self.image, (140, 90, 60), (20, 7), 4)
        self.rect = self.image.get_rect(center=(x, y))
        dx, dy = target_x - x, target_y - y
        dist = max(1.0, math.hypot(dx, dy))
        self.vx, self.vy = (dx / dist) * speed, (dy / dist) * speed
        angle = math.degrees(math.atan2(-dy, dx))
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=(x, y))
        self.exact_x, self.exact_y = float(self.rect.x), float(self.rect.y)

    def update(self, *a, **k):
        self.exact_x += self.vx
        self.exact_y += self.vy
        self.rect.x, self.rect.y = int(self.exact_x), int(self.exact_y)
        if not (-40 <= self.rect.x <= SCREEN_WIDTH + 40 and -40 <= self.rect.y <= SCREEN_HEIGHT + 40):
            self.kill()


# ---- ground slam telegraph marker ----
class SlamWarning:
    def __init__(self, x, ground_y, warn_frames=90):
        self.x = x
        self.ground_y = ground_y
        self.timer = warn_frames
        self.max_timer = warn_frames
        self.radius_x = 75   # oval half-width
        self.radius_y = 28   # oval half-height

    def update(self):
        self.timer -= 1

    @property
    def is_done(self):
        return self.timer <= 0

    def draw(self, screen):
        t = max(0.0, self.timer / self.max_timer)  # 1 -> 0 as impact nears

        # outer ring shrinks down onto the landing oval
        scale = 1.0 + t * 2.0
        rw, rh = int(self.radius_x * 2 * scale), int(self.radius_y * 2 * scale)
        ring = pygame.Surface((rw, rh), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (255, 90, 30, 170), (0, 0, rw, rh), width=4)
        screen.blit(ring, (self.x - rw // 2, self.ground_y - rh // 2))

        # landing zone oval, pulsing
        pulse = abs(math.sin((self.max_timer - self.timer) * 0.25))
        alpha = int(110 + 110 * pulse)
        ow, oh = int(self.radius_x * 2), int(self.radius_y * 2)
        oval = pygame.Surface((ow, oh), pygame.SRCALPHA)
        pygame.draw.ellipse(oval, (255, 60, 30, alpha), (0, 0, ow, oh), width=5)
        pygame.draw.ellipse(oval, (255, 130, 40, int(alpha * 0.45)), (0, 0, ow, oh))
        screen.blit(oval, (self.x - self.radius_x, self.ground_y - self.radius_y))


# ---- Phase 2 laser beam: fixed origin, static angle, no tracking ----
class LaserBeam:
    CHANNEL, FIRE, DONE = 'channel', 'fire', 'done'

    def __init__(self, origin_x, origin_y, angle_deg, length=900,
                 channel_frames=40, fire_frames=20, width=14, damage=18):
        self.origin = (origin_x, origin_y)
        self.angle = math.radians(angle_deg)
        self.length = length
        self.width = width
        self.damage = damage
        self.channel_timer = channel_frames
        self.fire_timer = fire_frames
        self.state = self.CHANNEL
        self.has_hit_player = False

        dx, dy = math.cos(self.angle), math.sin(self.angle)
        end_x = origin_x + dx * length
        end_y = origin_y + dy * length
        self.line = (origin_x, origin_y, end_x, end_y)

    def update(self):
        if self.state == self.CHANNEL:
            self.channel_timer -= 1
            if self.channel_timer <= 0:
                self.state = self.FIRE
        elif self.state == self.FIRE:
            self.fire_timer -= 1
            if self.fire_timer <= 0:
                self.state = self.DONE

    @property
    def is_done(self):
        return self.state == self.DONE

    def hits_player(self, player_rect):
        # deals damage once, only while actively firing
        if self.state != self.FIRE or self.has_hit_player:
            return False
        x1, y1, x2, y2 = self.line
        px, py = player_rect.centerx, player_rect.centery
        dx, dy = x2 - x1, y2 - y1
        seg_len_sq = dx * dx + dy * dy
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / seg_len_sq)) if seg_len_sq else 0
        closest_x, closest_y = x1 + t * dx, y1 + t * dy
        dist = math.hypot(px - closest_x, py - closest_y)
        if dist <= self.width / 2 + max(player_rect.width, player_rect.height) / 3:
            self.has_hit_player = True
            return True
        return False

    def draw(self, screen):
        x1, y1, x2, y2 = self.line
        if self.state == self.CHANNEL:
            pygame.draw.line(screen, (255, 100, 30, 120), (x1, y1), (x2, y2), 2)
            glow = pygame.Surface((60, 60), pygame.SRCALPHA)
            pulse = abs(math.sin(self.channel_timer * 0.3))
            pygame.draw.circle(glow, (255, 150, 50, int(150 * pulse)), (30, 30), 30)
            screen.blit(glow, (x1 - 30, y1 - 30))
        elif self.state == self.FIRE:
            core = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(core, (255, 220, 150, 230), (x1, y1), (x2, y2), self.width)
            pygame.draw.line(core, (255, 90, 20, 255), (x1, y1), (x2, y2), max(2, self.width // 3))
            screen.blit(core, (0, 0))


# ---- cutscene: relic + sequencer ----
class RelicPlaceholder:
    def __init__(self, x, ground_y):
        self.rect = pygame.Rect(0, 0, 40, 56)
        self.rect.midbottom = (x, ground_y)
        self.shattered = False

    def draw(self, screen):
        if self.shattered:
            return
        pygame.draw.rect(screen, (120, 100, 160), self.rect, border_radius=6)
        pygame.draw.rect(screen, (200, 180, 255), self.rect, width=3, border_radius=6)
        glow = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(glow, (200, 160, 255, 90), (35, 35), 35)
        screen.blit(glow, (self.rect.centerx - 35, self.rect.centery - 35))


class BossRoomCutscene:
    # WALK_IN: player locked, auto-walks to target x.
    # ATTACK: scripted hit on the relic.
    # DROP_WAIT: boss falls from the top.
    # BEAT: ~1s pause once the boss lands, before combat starts.
    WALK_IN, ATTACK, DROP_WAIT, BEAT, DONE = 'walk_in', 'attack', 'drop_wait', 'beat', 'done'

    def __init__(self, walk_target_x, relic_x, ground_y, walk_speed=3):
        self.state = self.WALK_IN
        self.walk_target_x = walk_target_x
        self.walk_speed = walk_speed
        self.relic = RelicPlaceholder(relic_x, ground_y)
        self.attack_timer = 25
        self.beat_timer = 60

    @property
    def player_locked(self):
        return self.state in (self.WALK_IN, self.ATTACK)

    @property
    def is_done(self):
        return self.state == self.DONE

    def update(self, player, boss, particle_emitter):
        if self.state == self.WALK_IN:
            if player.rect.centerx < self.walk_target_x:
                player.rect.x += self.walk_speed
            else:
                self.state = self.ATTACK

        elif self.state == self.ATTACK:
            self.attack_timer -= 1
            if self.attack_timer == 15:
                self.relic.shattered = True
                particle_emitter.emit(self.relic.rect.centerx, self.relic.rect.centery,
                                        count=20, color=(200, 160, 255), lifetime=25,
                                        size=4, speed_range=(1, 4), angle_range=(0, 360))
            if self.attack_timer <= 0:
                boss.begin_drop()
                self.state = self.DROP_WAIT

        elif self.state == self.DROP_WAIT:
            if boss.state == WitheredKing.LANDING_BEAT:
                self.state = self.BEAT

        elif self.state == self.BEAT:
            self.beat_timer -= 1
            if self.beat_timer <= 0:
                self.state = self.DONE

    def draw(self, screen):
        self.relic.draw(screen)


# ---- The Withered King ----
class WitheredKing:
    HIDDEN = 'hidden'
    DROPPING = 'dropping'
    LANDING_BEAT = 'landing_beat'
    PHASE1 = 'phase1'
    PHASE2 = 'phase2'
    DEAD = 'dead'

    MAX_HP = 100
    CONTACT_DAMAGE = 15

    BASIC_COOLDOWN = 70
    SLAM_COOLDOWN_P1 = 240
    SLAM_COOLDOWN_P2 = 170
    LASER_COOLDOWN = 300
    SLAM_JUMP_FRAMES = 40   # leap duration
    SLAM_JUMP_HEIGHT = 170  # peak leap height in pixels

    def __init__(self, x, ground_y):
        self.sheet = LPCSpriteSheet()
        self.x = float(x)
        self.ground_y = ground_y
        self.facing_right = False
        self.frame_timer = 0.0
        self.frame_index = 0
        self.anim_speed = 0.15

        self.state = self.HIDDEN
        self.y = -200.0
        self.drop_progress = 0
        self.beat_timer = 0

        self.hp = self.MAX_HP
        self.last_hp = self.MAX_HP
        self.is_hurt = False
        self.hurt_timer = 0
        self.death_complete = False

        self.action = 'chase'  # chase | slam_telegraph | slam_jump | slam_impact | laser_channel | laser_fire | basic_windup | recover | phase2_transition
        self.action_timer = 0
        self.basic_cd = self.BASIC_COOLDOWN
        self.slam_cd = self.SLAM_COOLDOWN_P1
        self.laser_cd = self.LASER_COOLDOWN

        self.slam_warning = None
        self.slam_target_x = None
        self.slam_start_x = None
        self.active_laser = None
        self._pending_projectile = None
        self.contact_cd = 0
        self.shake = ScreenShake()
        self.phase_flash = PhaseFlash()
        self.phase2_triggered = False
        self.phase2_transition_timer = 0
        self.sfx = BossSFX()

        self.global_frame = 0

    @property
    def rect(self):
        size = LPC_CELL * self.sheet.scale
        return pygame.Rect(int(self.x - size // 2), int(self.y - size), size, size)

    @property
    def head_pos(self):
        r = self.rect
        return r.centerx, r.top + int(r.height * 0.2)

    def begin_drop(self):
        self.state = self.DROPPING
        self.drop_progress = 0

    def take_damage(self, amount):
        if self.state in (self.HIDDEN, self.DROPPING, self.LANDING_BEAT, self.DEAD):
            return
        if self.action == 'phase2_transition':
            return
        self.hp = max(0, self.hp - amount)
        self.sfx.play('hit', volume=0.4)

    def pop_projectile(self):
        p = self._pending_projectile
        self._pending_projectile = None
        return p

    def pop_laser(self):
        # main.py calls this once to grab a newly-fired laser for collision checks
        laser = self.active_laser
        self.active_laser = None
        return laser

    def update(self, player, particle_emitter=None):
        self.global_frame += 1
        self.shake.update()
        self.phase_flash.update()
        event = None

        if self.state == self.HIDDEN:
            return None

        if self.state == self.DROPPING:
            self._update_drop(particle_emitter)
            return None

        if self.state == self.LANDING_BEAT:
            self.beat_timer -= 1
            self._animate('idle')
            if self.beat_timer <= 0:
                self.state = self.PHASE1
            return None

        if self.state == self.DEAD:
            self._update_death()
            return None

        # Phase 2 enrage freeze in progress: roar pose held, no movement/attacks
        if self.action == 'phase2_transition':
            self.phase2_transition_timer -= 1
            self._animate('emote')
            if self.phase2_transition_timer <= 0:
                self.state = self.PHASE2
                self.action = 'chase'
            return None

        # hurt flash bookkeeping
        if self.hp < self.last_hp:
            self.is_hurt = True
            self.hurt_timer = 8
        self.last_hp = self.hp
        if self.is_hurt:
            self.hurt_timer -= 1
            if self.hurt_timer <= 0:
                self.is_hurt = False

        # death check
        if self.hp <= 0:
            self.state = self.DEAD
            self.hurt_timer = 40
            if particle_emitter is not None:
                particle_emitter.petal_storm(SCREEN_WIDTH)
            self.sfx.play('death', volume=0.9)
            return "DEFEATED"

        # phase transition trigger - fires once
        if self.state == self.PHASE1 and self.hp <= self.MAX_HP * 0.5 and not self.phase2_triggered:
            self.phase2_triggered = True
            self.action = 'phase2_transition'
            self.phase2_transition_timer = 55
            self.phase_flash.trigger(duration=30, color=(255, 100, 30))
            self.shake.trigger(intensity=26, duration=30)
            self.sfx.play('roar', volume=0.85)
            if particle_emitter:
                hx, hy = self.head_pos
                particle_emitter.emit(hx, hy, count=40, color=(255, 130, 40),
                                        lifetime=45, size=5, speed_range=(2, 7),
                                        angle_range=(0, 360))
            return "PHASE2"

        speed = 2 if self.state == self.PHASE1 else 3
        move_anim = 'walk' if self.state == self.PHASE1 else 'run'

        self.basic_cd = max(0, self.basic_cd - 1)
        self.slam_cd = max(0, self.slam_cd - 1)
        self.contact_cd = max(0, self.contact_cd - 1)
        if self.state == self.PHASE2:
            self.laser_cd = max(0, self.laser_cd - 1)

        if self.action == 'chase':
            self.facing_right = self.x < player.rect.centerx
            self.x += speed * (1 if self.facing_right else -1)
            margin = 90
            self.x = max(margin, min(SCREEN_WIDTH - margin, self.x))
            self._animate(move_anim)

            if self.contact_cd <= 0 and not player.is_dead and self.rect.colliderect(player.rect):
                player.take_damage(self.CONTACT_DAMAGE)
                self.contact_cd = 40

            self._choose_next_action(player)
        else:
            self._update_action(player, particle_emitter)

        return event

    def _choose_next_action(self, player):
        if self.slam_cd <= 0:
            self.action = 'slam_telegraph'
            self.slam_target_x = player.rect.centerx
            self.slam_start_x = self.x
            self.slam_warning = SlamWarning(self.slam_target_x, self.ground_y)
            self.slam_cd = self.SLAM_COOLDOWN_P1 if self.state == self.PHASE1 else self.SLAM_COOLDOWN_P2
        elif self.state == self.PHASE2 and self.laser_cd <= 0:
            self.action = 'laser_channel'
            self.action_timer = 40
            hx, hy = self.head_pos
            angle = 180 if not self.facing_right else 0
            self.active_laser = LaserBeam(hx, hy, angle)
            self.laser_cd = self.LASER_COOLDOWN
            self.sfx.play('laser_charge', volume=0.7)
        elif self.basic_cd <= 0:
            self.action = 'basic_windup'
            self.action_timer = 14
            self.basic_cd = self.BASIC_COOLDOWN

    def _update_action(self, player, particle_emitter):
        if self.action == 'slam_telegraph':
            self.slam_warning.update()
            self._animate('idle')
            if self.slam_warning.is_done:
                self.action = 'slam_jump'
                self.action_timer = self.SLAM_JUMP_FRAMES
        elif self.action == 'slam_jump':
            self.action_timer -= 1
            t = 1 - (self.action_timer / self.SLAM_JUMP_FRAMES)
            self.x = self.slam_start_x + (self.slam_target_x - self.slam_start_x) * t
            # parabola: 0 at t=0 and t=1, peak at t=0.5 -> leap up then down
            self.y = self.ground_y - self.SLAM_JUMP_HEIGHT * 4 * t * (1 - t)
            self._animate('jump')
            if self.action_timer <= 0:
                self.x = self.slam_target_x
                self.y = self.ground_y
                self.action = 'slam_impact'
                self.action_timer = 12
                if particle_emitter:
                    particle_emitter.dust_burst(self.x, self.ground_y)
                self.shake.trigger(intensity=18, duration=16)
                self.sfx.play('slam', volume=0.8)
                impact_radius = self.slam_warning.radius_x if self.slam_warning else 75
                if not player.is_dead and abs(player.rect.centerx - self.x) < impact_radius:
                    player.take_damage(20)
        elif self.action == 'slam_impact':
            self.action_timer -= 1
            self._animate('slash')
            if self.action_timer <= 0:
                self.action = 'chase'
                self.slam_warning = None

        elif self.action == 'laser_channel':
            self.action_timer -= 1
            self._animate('spellcast')
            if self.active_laser:
                self.active_laser.update()
            if self.action_timer <= 0:
                self.action = 'laser_fire'
                self.action_timer = 20
                self.sfx.play('laser_fire', volume=0.85)
        elif self.action == 'laser_fire':
            self.action_timer -= 1
            self._animate('spellcast')
            if self.active_laser:
                self.active_laser.update()
                if not player.is_dead and self.active_laser.hits_player(player.rect):
                    player.take_damage(self.active_laser.damage)
            if self.action_timer <= 0:
                self.action = 'chase'
                self.active_laser = None

        elif self.action == 'basic_windup':
            self.action_timer -= 1
            self._animate('thrust')
            if self.action_timer <= 0:
                hx, hy = self.head_pos
                self._pending_projectile = RootProjectile(hx, hy, player.rect.centerx, player.rect.centery)
                self.action = 'recover'
                self.action_timer = 12
                self.sfx.play('basic_attack', volume=0.6)
        elif self.action == 'recover':
            self.action_timer -= 1
            self._animate('idle')
            if self.action_timer <= 0:
                self.action = 'chase'

    def _update_drop(self, particle_emitter):
        self.drop_progress += 1
        progress = min(1.0, self.drop_progress / 60)
        self.y = -100 + (self.ground_y - (-100)) * progress
        self._animate('jump', frame_override=len(self.sheet.get_animation('jump', 'left')) - 1)
        if progress >= 1.0:
            self.y = self.ground_y
            self.state = self.LANDING_BEAT
            self.beat_timer = 60
            if particle_emitter:
                particle_emitter.dust_burst(self.x, self.ground_y)
            self.shake.trigger(intensity=22, duration=22)
            self.sfx.play('landing', volume=0.8, fallback='slam')

    def _update_death(self):
        self.hurt_timer -= 1
        direction = 'right' if self.facing_right else 'left'
        frames = self.sheet.get_animation('idle', direction)
        base = frames[0]

        # alternating white-silhouette flashes, then hold the last look
        flash_on = (self.hurt_timer // 4) % 2 == 0
        if flash_on and self.hurt_timer > -40:
            flashed = base.copy()
            white = pygame.Surface(flashed.get_size(), pygame.SRCALPHA)
            white.fill((255, 255, 255, 255))
            flashed.blit(white, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            self._current_image = flashed
        else:
            self._current_image = base

        if self.hurt_timer <= -40:
            self.death_complete = True

    def _animate(self, anim_name, frame_override=None):
        direction = 'right' if self.facing_right else 'left'
        frames = self.sheet.get_animation(anim_name, direction)

        if frame_override is not None:
            idx = min(frame_override, len(frames) - 1)
        else:
            self.frame_timer += self.anim_speed
            if self.frame_timer >= len(frames):
                self.frame_timer = 0
            idx = int(self.frame_timer)

        img = frames[idx]
        if self.is_hurt and pygame.time.get_ticks() % 200 < 100:
            tint = img.copy()
            red = pygame.Surface(tint.get_size(), pygame.SRCALPHA)
            red.fill((255, 60, 60, 90))
            tint.blit(red, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            img = tint
        self._current_image = img

    def draw_glowing_cap(self, screen, particle_emitter):
        if self.state != self.PHASE2:
            return
        hx, hy = self.head_pos
        glow = particle_emitter.glow_pulse(hx, hy, self.global_frame, radius=32, color=(255, 165, 0))
        screen.blit(glow, (hx - 32, hy - 32))

    def draw(self, screen):
        if self.state == self.HIDDEN or getattr(self, '_current_image', None) is None:
            return
        img = self._current_image
        rect = img.get_rect(midbottom=(int(self.x), int(self.y)))
        screen.blit(img, rect)

        if self.action == 'slam_telegraph' and self.slam_warning:
            self.slam_warning.draw(screen)
        if self.active_laser:
            self.active_laser.draw(screen)


# ---- UI ----
class WitheredKingHealthBar:
    def __init__(self):
        self.font = pygame.font.Font(None, 34)

    def draw(self, screen, boss):
        if boss is None or boss.state in (WitheredKing.HIDDEN, WitheredKing.DROPPING,
                                            WitheredKing.LANDING_BEAT, WitheredKing.DEAD):
            return
        bar_w, bar_h = 500, 22
        x = (SCREEN_WIDTH - bar_w) // 2
        y = 30

        name = "THE WITHERED KING" if boss.state == WitheredKing.PHASE1 else "THE WITHERED KING - ENRAGED"
        color = (255, 220, 150) if boss.state == WitheredKing.PHASE1 else (255, 140, 60)
        text = self.font.render(name, True, color)
        shadow = self.font.render(name, True, (0, 0, 0))
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, y - 14))
        screen.blit(shadow, (rect.x + 2, rect.y + 2))
        screen.blit(text, rect)

        pygame.draw.rect(screen, (30, 20, 15), (x, y, bar_w, bar_h))
        pygame.draw.rect(screen, (170, 140, 100), (x, y, bar_w, bar_h), 2)
        ratio = boss.hp / boss.MAX_HP
        fill_color = (170, 60, 30) if boss.state == WitheredKing.PHASE1 else (220, 90, 20)
        if ratio > 0:
            pygame.draw.rect(screen, fill_color, (x, y, int(bar_w * ratio), bar_h))
        hp_text = self.font.render(f"{boss.hp}/{boss.MAX_HP}", True, (255, 255, 255))
        screen.blit(hp_text, hp_text.get_rect(center=(x + bar_w // 2, y + bar_h // 2)))


def draw_win_screen(screen, score):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill((10, 30, 15))
    overlay.set_alpha(150)
    screen.blit(overlay, (0, 0))

    title_font = pygame.font.Font(None, 120)
    big_font = pygame.font.Font(None, 60)
    medium_font = pygame.font.Font(None, 50)
    small_font = pygame.font.Font(None, 36)

    pulse = 200 + int(55 * abs(math.sin(pygame.time.get_ticks() / 300)))
    title = title_font.render("YOU WIN!", True, (255, pulse, 200))
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 180)))

    sub = big_font.render("The Withered King has fallen.", True, WHITE)
    screen.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 280)))

    score_text = medium_font.render(f"Final Score: {score}", True, (255, 230, 150))
    screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, 360)))

    alpha = 128 + int(127 * abs(math.sin(pygame.time.get_ticks() / 400)))
    restart = medium_font.render("Press R to Restart", True, (255, 255, 200))
    restart.set_alpha(alpha)
    screen.blit(restart, restart.get_rect(center=(SCREEN_WIDTH // 2, 460)))

    quit_text = small_font.render("Press ESC to Quit", True, (200, 200, 200))
    screen.blit(quit_text, quit_text.get_rect(center=(SCREEN_WIDTH // 2, 520)))


ARENA_BG_FILE = os.path.join(BASE_DIR, "assets", "sprites", "backgrounds", "level4_arena.webp")
_arena_bg_cache = None


def draw_garden_arena_background(screen):
    global _arena_bg_cache
    if _arena_bg_cache is None:
        if os.path.exists(ARENA_BG_FILE):
            _arena_bg_cache = pygame.transform.scale(
                pygame.image.load(ARENA_BG_FILE).convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            for y in range(SCREEN_HEIGHT):
                t = y / SCREEN_HEIGHT
                pygame.draw.line(surf, (int(35 + 20 * t), int(20 + 10 * t), int(25 + 15 * t)), (0, y), (SCREEN_WIDTH, y))
            cx, cy = SCREEN_WIDTH // 2, GROUND_Y + 40
            pygame.draw.ellipse(surf, (55, 40, 35), (cx - 420, cy - 90, 840, 180))
            pygame.draw.rect(surf, (60, 35, 25), (cx - 22, cy - 260, 44, 200), border_radius=10)
            pygame.draw.circle(surf, (180, 90, 40), (cx, cy - 280), 22)
            _arena_bg_cache = surf
    screen.blit(_arena_bg_cache, (0, 0))
