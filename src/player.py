import pygame
import os
import random
import math
import ctypes
from settings import *


def windows_key_is_down(*virtual_keys):
    try:
        window_handle = pygame.display.get_wm_info().get("window")
        user32 = ctypes.windll.user32
        if not window_handle or user32.GetForegroundWindow() != window_handle:
            return False
        return any(user32.GetAsyncKeyState(key) & 0x8001 for key in virtual_keys)
    except (AttributeError, pygame.error):
        return False

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # ---------- 基础属性 ----------
        self.speed = PLAYER_SPEED
        self.vy = 0
        self.gravity = GRAVITY
        self.jump_power = PLAYER_JUMP_POWER
        self.is_on_ground = False

        # ---------- 加载所有动画帧 ----------
        self.animations = {
            'idle': [],
            'walk': [],
            'fly': [],
            'jump': [],
            'attack': [],
            'hurt': [],
            'dead': []
        }
        
        player_folder = PLAYER_FOLDER
        all_files = os.listdir(player_folder)
        
        # 打印所有文件，方便调试
        print("📂 找到的文件:", all_files)
        
        for file in all_files:
            if not file.endswith(".png"):
                continue
            path = os.path.join(player_folder, file)
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (128, 128))
            
            if "IDLE" in file:
                self.animations['idle'].append(img)
            elif "WALK" in file:
                self.animations['walk'].append(img)
            elif "FLY" in file:
                self.animations['fly'].append(img)
            elif "JUMP" in file:
                self.animations['jump'].append(img)
            elif "ATTACK" in file:
                self.animations['attack'].append(img)
            elif "HURT" in file:
                self.animations['hurt'].append(img)
            elif "DIE" in file:           # ⭐ 注意是 DIE
                self.animations['dead'].append(img)
        
        for key in self.animations:
            if len(self.animations[key]) == 0:
                if key == "attack" and self.animations["idle"]:
                    self.animations[key] = [frame.copy() for frame in self.animations["idle"]]
                    continue
                print(f"⚠️ {key} 动画没有图片，创建占位")
                surf = pygame.Surface((128, 128), pygame.SRCALPHA)
                if key == 'hurt':
                    surf.fill((255, 0, 0, 100))
                elif key == 'dead':
                    surf.fill((50, 50, 50, 200))
                else:
                    surf.fill((255, 0, 255, 128))
                self.animations[key] = [surf]
            else:
                print(f"✅ {key}: {len(self.animations[key])} 帧")
        
        # 默认状态
        self.current_state = 'idle'
        self.current_frame = 0
        self.image = self.animations['idle'][0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        # ---------- 动画控制 ----------
        self.animation_timer = 0
        self.animation_speed = 8
        self.is_walking = False
        self.facing_right = True
        self.is_flying = False
        self.is_attacking = False
        self.attack_timer = 0
        self.is_jumping = False

        # ---------- 攻击系统 ----------
        self.attack_cooldown = 0
        self.seed_shots = []
        self.seed_count = SEED_SHOT_MAX
        self.seed_recharge_timer = 0

        # ---------- 飞行系统 ----------
        self.fly_timer = 0
        self.max_fly_time = MAX_FLY_TIME
        self.fly_speed = FLY_SPEED

        # ==========================================
        # HP 系统
        # ==========================================
        self.max_hp = MAX_HP
        self.hp = MAX_HP
        
        self.idle_timer = 0
        self.is_healing = False
        self.heal_particles = []
        
        # ⭐ 受伤状态
        self.is_hurt = False
        self.hurt_timer = 0
        self.hurt_frame = 0  # 受伤动画帧
        
        # ⭐ 死亡状态
        self.is_dead = False
        self.death_timer = 0
        self.death_animation_complete = False

    def take_damage(self, amount):
        """受到伤害 (支持同帧群殴叠加伤害，被攻击会打断回血)"""
        import pygame
        
        if getattr(self, 'is_dead', False):
            return None

        current_time = pygame.time.get_ticks()
        if not hasattr(self, 'last_hurt_time'):
            self.last_hurt_time = 0

        time_since_last_hit = current_time - self.last_hurt_time

        if self.is_hurt and time_since_last_hit >= 10:
            return None

        self.hp -= amount
        self.last_hurt_time = current_time 
        print(f"受到 {amount} 点伤害！剩余 HP: {self.hp}")

        # 触发受伤状态
        self.is_hurt = True
        self.hurt_timer = 30  
        self.hurt_frame = 0

        # 受击仅强行打断回血
        if getattr(self, 'is_healing', False):
            print("遭到攻击！回血被打断！")
            self.is_healing = False
            if hasattr(self, 'heal_timer'):
                self.heal_timer = 0  # 清空回血计时器

        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            self.death_timer = 0
            self.death_animation_complete = False
            self.current_frame = 0
            print("💀 玩家死亡！")
            return "GAME_OVER"

        return None

    def heal(self, amount):
        if self.is_dead:
            return 0
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.max_hp)
        healed = self.hp - old_hp
        if healed > 0:
            print(f"回复 {healed} HP! 当前 HP: {self.hp}")
        return healed

    # member3 
    def draw_healing_aura(self, screen):
        if self.is_healing:
            import math
            # Using a sine wave to smoothly adjust the halo radius between 35 and 40
            radius = 35 + int(5 * math.sin(pygame.time.get_ticks() * 0.005))
            
            # Create a surface that supports transparency
            aura_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            
            # Draw a soft yellow ring
            pygame.draw.circle(aura_surface, (255, 255, 0, 150), (50, 50), radius, 4)
            
            # Draw on the screen based on the player's current center point
            screen.blit(aura_surface, (self.rect.centerx - 50, self.rect.centery - 50))

    def attack(self):
        if self.is_dead:
            return None
        if self.attack_cooldown <= 0 and not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = ATTACK_DURATION
            self.attack_cooldown = ATTACK_COOLDOWN
            self.current_frame = 0
            print("⚔️ Vine Whip!")
            return self.create_attack_hitbox()
        return None

    def create_attack_hitbox(self):
        if self.facing_right:
            return pygame.Rect(
                self.rect.right,
                self.rect.y + 20,
                VINE_WHIP_RANGE,
                self.rect.height - 40
            )
        else:
            return pygame.Rect(
                self.rect.left - VINE_WHIP_RANGE,
                self.rect.y + 20,
                VINE_WHIP_RANGE,
                self.rect.height - 40
            )

    def shoot_seed(self):
        if self.is_dead:
            return None
        if self.seed_count > 0 and self.attack_cooldown <= 0:
            self.seed_count -= 1
            self.attack_cooldown = ATTACK_COOLDOWN
            print(f"🌱 Seed Shot! 剩余: {self.seed_count}")
            
            seed = SeedShot(
                self.rect.centerx if self.facing_right else self.rect.left,
                self.rect.centery,
                self.facing_right
            )
            self.seed_shots.append(seed)
            return seed
        return None

    def update(self):
        keys = pygame.key.get_pressed()
        
        # 死亡状态：播放死亡动画，不响应其他操作
        if self.is_dead:
            self.update_death_animation()
            return
        
        # ==========================================
        # 1. 重力
        # ==========================================
        self.vy += self.gravity
        self.rect.y += self.vy
        
        self.is_on_ground = False
        # 增加一个判断：如果 player 自己有 ground_y 属性，就用自己的；否则才用全局的 GROUND_Y
        target_ground = getattr(self, 'ground_y', GROUND_Y)
        if self.rect.bottom >= target_ground:
            self.rect.bottom = target_ground
            self.vy = 0
            self.is_on_ground = True
            self.is_jumping = False
        
        if self.rect.top < 0:
            self.rect.top = 0
            self.vy = 0

        # ==========================================
        # 2. 飞行系统
        # ==========================================
        self.is_flying = False
        
        if keys[pygame.K_w] and self.fly_timer < self.max_fly_time:
            self.is_flying = True
            self.fly_timer += 1
            self.vy = self.fly_speed
            self.vy += self.gravity * 0.2
        
        if not self.is_flying:
            if self.fly_timer > 0:
                self.fly_timer -= 1
            if self.is_on_ground and self.fly_timer > 0:
                self.fly_timer -= 2
            if self.fly_timer < 0:
                self.fly_timer = 0

        # ==========================================
        # 3. 跳跃
        # ==========================================
        if keys[pygame.K_SPACE] and self.is_on_ground:
            self.vy = self.jump_power
            self.is_jumping = True

        # ==========================================
        # 4. 左右移动
        # ==========================================
        self.is_walking = False
        
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
            self.is_walking = True
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            self.is_walking = True
            self.facing_right = True

        # ==========================================
        # 5. 边界限制
        # ==========================================
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        # ==========================================
        # 6. 攻击系统
        # ==========================================
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        if self.is_attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.is_attacking = False
        
        melee_key_down = (
            keys[pygame.K_z]
            or keys[pygame.K_j]
            or keys[pygame.K_c]
            or windows_key_is_down(0x5A, 0x4A, 0x43)
        )
        seed_key_down = (
            keys[pygame.K_x]
            or keys[pygame.K_k]
            or keys[pygame.K_v]
            or windows_key_is_down(0x58, 0x4B, 0x56)
        )

        if melee_key_down:
            self.attack()
        if seed_key_down:
            self.shoot_seed()

        # ==========================================
        # 7. 弹药回复
        # ==========================================
        if self.seed_count < SEED_SHOT_MAX:
            self.seed_recharge_timer += 1
            if self.seed_recharge_timer >= SEED_SHOT_RECHARGE:
                self.seed_count += 1
                self.seed_recharge_timer = 0

        # ==========================================
        # 8. 子弹更新
        # ==========================================
        for seed in self.seed_shots[:]:
            seed.update()
            if seed.is_off_screen():
                self.seed_shots.remove(seed)

        # ==========================================
        # 9. 被动回血
        # ==========================================
        # member 3
        # 你的判定逻辑：没有按左右键，在地面上，没在飞
        # 【核心修复】：增加 and not self.is_hurt 判定
        # 只要正在挨打僵直，就绝对不算在“待机休息”！
        is_idle = (not keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT]
               and self.is_on_ground and not getattr(self, 'is_flying', False)
               and not self.is_hurt)

        if is_idle and self.hp < self.max_hp:
            self.idle_timer += 1
            # 180 帧 = 3 秒 (假设游戏运行在 60 FPS)
            if self.idle_timer >= 180:
                self.is_healing = True
                # 每 60 帧 (1秒) 恢复 5 HP
                if self.idle_timer % 60 == 0:
                    self.heal(5)
        else:
            self.idle_timer = 0
            self.is_healing = False

        # ==========================================
        # 10. ⭐ 受伤计时器
        # ==========================================
        if self.is_hurt:
            self.hurt_timer -= 1
            if self.hurt_timer <= 0:
                self.is_hurt = False

        # ==========================================
        # 11. ⭐ 动画状态机（受伤和死亡优先）
        # ==========================================
        self.animation_timer += 1
        
        # 不同状态使用不同速度
        if self.is_hurt:
            speed = 5  # 受伤动画速度
        elif self.is_attacking:
            speed = 4
        elif self.is_flying:
            speed = 4
        elif not self.is_on_ground:
            speed = 5
        elif self.is_walking:
            speed = 6
        else:
            speed = 8
        
        if self.animation_timer >= speed:
            self.animation_timer = 0
            
            # ⭐ 优先级：受伤 > 攻击 > 飞行 > 跳跃 > 行走 > 待机
            if self.is_hurt:
                state = 'hurt'
            elif self.is_attacking:
                state = 'attack'
            elif self.is_flying:
                state = 'fly'
            elif not self.is_on_ground:
                state = 'jump'
            elif self.is_walking:
                state = 'walk'
            else:
                state = 'idle'
            
            frames = self.animations.get(state, self.animations['idle'])
            
            if frames:
                if state == 'attack' and self.is_attacking:
                    if self.current_frame < len(frames) - 1:
                        self.current_frame += 1
                elif state == 'hurt' and self.is_hurt:
                    # 受伤动画循环播放
                    self.current_frame = (self.current_frame + 1) % len(frames)
                else:
                    self.current_frame = (self.current_frame + 1) % len(frames)
                
                original_image = frames[self.current_frame % len(frames)]
                
                if self.facing_right:
                    self.image = original_image
                else:
                    self.image = pygame.transform.flip(original_image, True, False)

    # ==========================================
    # ⭐ 死亡动画更新
    # ==========================================
    def update_death_animation(self):
        """更新死亡动画"""
        self.death_timer += 1
        
        frames = self.animations.get('dead', [])
        if frames:
            # 死亡动画播放一次后停在最后一帧
            if self.current_frame < len(frames) - 1:
                if self.death_timer % 8 == 0:
                    self.current_frame += 1
            else:
                self.death_animation_complete = True
            
            original_image = frames[self.current_frame % len(frames)]
            if self.facing_right:
                self.image = original_image
            else:
                self.image = pygame.transform.flip(original_image, True, False)
        
        # 死亡时缓慢下落
        self.vy += self.gravity * 0.5
        self.rect.y += self.vy
        
        if self.rect.bottom > GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vy = 0

    def get_fly_progress(self):
        return self.fly_timer / self.max_fly_time
    
    def get_hp_progress(self):
        return self.hp / self.max_hp
    
    def get_hp_percent(self):
        return int((self.hp / self.max_hp) * 100)
    
    def is_dead_animation_complete(self):
        return self.death_animation_complete


# ---------- 子弹类 ----------
class SeedShot(pygame.sprite.Sprite):
    def __init__(self, x, y, facing_right):
        super().__init__()
        
        self.frames = []
        attack_folder = ATTACK_FOLDER
        
        if os.path.exists(attack_folder):
            all_files = os.listdir(attack_folder)
            frame_files = []
            for file in all_files:
                if file.startswith("Fairy_03__ATTACK_") and file.endswith(".png"):
                    frame_files.append(file)
            frame_files.sort()
            
            for file in frame_files:
                path = os.path.join(attack_folder, file)
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (48, 48))
                self.frames.append(img)
        
        if len(self.frames) == 0:
            print("⚠️ 没有找到攻击图片！使用代码生成的子弹")
            self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (100, 255, 100), (10, 10), 12)
            pygame.draw.circle(self.image, (200, 255, 200), (10, 10), 8)
            self.frames = [self.image]
        else:
            print(f"✅ 子弹加载了 {len(self.frames)} 帧攻击动画")
            self.image = self.frames[0]
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        self.speed = SEED_SHOT_SPEED
        self.facing_right = facing_right
        
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 3
        self.trail_particles = []
    
    def update(self):
        if self.facing_right:
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed
        
        if len(self.frames) > 1:
            self.animation_timer += 1
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]
        
        self.trail_particles.append({
            'x': self.rect.centerx,
            'y': self.rect.centery,
            'life': 15,
            'color': (100, 255, 100)
        })
        
        for p in self.trail_particles[:]:
            p['life'] -= 1
            p['x'] += random.uniform(-0.5, 0.5)
            if p['life'] <= 0:
                self.trail_particles.remove(p)
    
    def draw_trail(self, screen):
        for p in self.trail_particles:
            alpha = int(255 * (p['life'] / 15))
            color = (p['color'][0], p['color'][1], p['color'][2], alpha)
            size = 4 * (p['life'] / 15)
            if size > 1:
                pygame.draw.circle(screen, color[:3], (int(p['x']), int(p['y'])), int(size))
    
    def is_off_screen(self):
        return self.rect.right < 0 or self.rect.left > SCREEN_WIDTH
