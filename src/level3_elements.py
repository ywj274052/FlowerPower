import pygame
import math
import os
import random

# ==========================================
# Full-screen poison gas survival system mechanism
# ==========================================
class PoisonGasSystem:
    def __init__(self, screen_width=1280, screen_height=720):
        self.width = screen_width
        self.height = screen_height
        
        self.active = False              
        self.gas_released = False        
        self.wave_timer = 0              
        self.gas_duration_timer = 0      
        self.damage_tick_timer = 0       
        self.damage_accumulated = 0      
        
        # Pre-rendered static edge vignette
        # The center of the screen is completely transparent, with only the edges showing a gradient of dark green.
        self.vignette = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for i in range(40):
            # Transparency decreases from the edge inwards
            alpha = 120 - i * 3
            if alpha < 0: alpha = 0
            rect = pygame.Rect(i * 4, i * 4, self.width - i * 8, self.height - i * 8)
            pygame.draw.rect(self.vignette, (40, 120, 40, alpha), rect, 4)

        # Poison spore particle system
        self.particles = []
        for _ in range(50): 
            self.particles.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'speed': random.uniform(0.5, 2.0),
                'size': random.randint(2, 4)
            })

    def start_wave(self):
        self.active = True
        self.gas_released = False
        self.wave_timer = 0
        self.damage_accumulated = 0

    def end_wave(self, player):
        if self.active:
            if self.damage_accumulated > 0:
                player.hp += self.damage_accumulated
                if hasattr(player, 'max_hp') and player.hp > player.max_hp:
                    player.hp = player.max_hp
                print(f"✨ 毒气消散！系统为您返还了 {self.damage_accumulated} 点生命值！")
            
            self.active = False
            self.gas_released = False
            self.damage_accumulated = 0

    def update(self, player):
        if not self.active:
            return

        # Phase 1: 10 seconds countdown
        if not self.gas_released:
            self.wave_timer += 1
            if self.wave_timer == 600:
                self.gas_released = True
                self.gas_duration_timer = 0
                self.damage_tick_timer = 0
                print("☣️ 警告！全屏毒气开始释放，持续 10 秒！")
                
        # Phase 2: During the gas eruption 
        else:
            self.gas_duration_timer += 1
            if self.gas_duration_timer <= 600:
                for p in self.particles:
                    p['y'] -= p['speed'] # Float upwards
                    p['x'] += math.sin(p['y'] * 0.05) * 1.5 # Swaying left and right
                    # After flying off the top of the screen, it regenerates from the bottom
                    if p['y'] < -10:
                        p['y'] = self.height + 10
                        p['x'] = random.randint(0, self.width)
                        
                # Blood Deduction Logic
                self.damage_tick_timer += 1
                if self.damage_tick_timer >= 60: 
                    self.damage_tick_timer = 0
                    damage = 3
                    player.hp -= damage   
                    self.damage_accumulated += damage
                    print(f"🤢 吸入毒气！失去 3 点生命... (已累计失去 {self.damage_accumulated} 点)")
                    
                    player.is_hurt = True
                    if hasattr(player, 'hurt_timer'): player.hurt_timer = 30
            else:
                pass 

    def draw(self, screen):
        if self.gas_released and self.gas_duration_timer <= 600:
            # 1. Draw a static edge green light
            screen.blit(self.vignette, (0, 0))
            
            # 2. Drawing floating poison spores
            for p in self.particles:
                pygame.draw.circle(screen, (100, 255, 100, 180), (int(p['x']), int(p['y'])), p['size'])

# ==========================================
# Level 3 专属怪物系统
# ==========================================

class ToxicSludge(pygame.sprite.Sprite):
    """怪物 1: 兽人步兵 (分离式 PNG 动画加载)"""
    def __init__(self, x, y):
        super().__init__()
        
        self.state = 'walk'            
        self.facing_right = False      
        self.animations = {'idle': [], 'walk': [], 'attack': [], 'hurt': [], 'dead': []}
        self.frame_index = 0           
        self.animation_speed = 0.2     
        
        self.load_animations(base_path="assets/sprites/enemies/")
        
        self.image = self.animations[self.state][self.frame_index]
        
        # 【视觉修复 1：解决悬空问题】
        # 图片下方有大量透明留白，我们需要把它的物理碰撞框强行往下平移 (补偿视觉差)
        self.y_offset = 15  # 如果他还是悬空，把数字加大；如果陷进土里了，把数字减小！
        self.rect = self.image.get_rect(bottomleft=(x, y + self.y_offset))

        self.hp = 30
        self.last_hp = 30              
        self.speed = 1.5
        self.attack_damage = 5

        self.is_hurt = False
        self.is_dead = False
        self.is_attacking = False
        self.attack_cooldown = 0
        self.has_dealt_damage = False  

        self.max_hp = self.hp     # 记录最大血量，用于计算血条比例
        self.show_hp_timer = 0    # 显血计时器

        self.score_value = 10
        self.score_given = False

    def kill(self):
        """【核心黑科技：拦截 main.py 的瞬间删除指令】"""
        # 如果还没死，说明这是 main.py 刚把它打空血的瞬间
        if not getattr(self, 'is_dead', False):
            self.hp = 0
            self.is_dead = True
            self.state = 'dead'
            self.frame_index = 0
            
            # 极其巧妙的一步：把物理碰撞框长宽设为 0！
            # 这样既能让尸体继续画在原地，又不会变成挡住子弹的“肉盾”（子弹会直接穿透尸体）
            self.rect.width = 0
            self.rect.height = 0
            
            return # 强行 return，拦截指令，不执行真实的删除操作！

        # 只有当死亡动画播完，并且躺够了 120 帧 (2秒) 时，才真正从内存中抹除
        if hasattr(self, 'dead_timer') and self.dead_timer >= 120:
            super().kill()

    def load_animations(self, base_path):
        """处理单独的 PNG 序列图"""
        
        # 配置每个动作对应的【文件名】和【总帧数】
        animation_config = {
            'idle':   {'file': 'Idle.png', 'frames': 5},
            'walk':   {'file': 'Walk.png', 'frames': 7},
            'attack': {'file': 'Attack_1.png', 'frames': 4},
            'hurt':   {'file': 'Hurt.png', 'frames': 2},
            'dead':   {'file': 'Dead.png', 'frames': 4}
        }

        scale = 1.3 # 放大倍数
        
        for state, info in animation_config.items():
            path = os.path.join(base_path, info['file'])
            
            if os.path.exists(path):
                sheet = pygame.image.load(path).convert_alpha()
                
                frame_width = sheet.get_width() // info['frames']
                frame_height = sheet.get_height()
                
                for i in range(info['frames']):
                    img = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA).convert_alpha()
                    img.blit(sheet, (0, 0), (i * frame_width, 0, frame_width, frame_height))
                    img = pygame.transform.scale(img, (int(frame_width * scale), int(frame_height * scale)))
                    self.animations[state].append(img)
            else:
                print(f"⚠️ 找不到图片 {path}，使用默认红色方块代替")
                frame_width, frame_height = 100, 100
                for i in range(info['frames']):
                    img = pygame.Surface((int(frame_width * scale), int(frame_height * scale)))
                    img.fill((200, 50, 50))
                    self.animations[state].append(img)

    def update_animation(self):
        # 1. 专门处理死亡动画逻辑，避免和其他动作混淆
        if self.state == 'dead':
            # 如果还没播到最后一帧，继续往下播
            if self.frame_index < len(self.animations['dead']) - 1:
                self.frame_index += self.animation_speed
            else:
                # 锁死在倒地的最后一帧
                self.frame_index = len(self.animations['dead']) - 1 
                # 开始死亡倒计时
                if not hasattr(self, 'dead_timer'):
                    self.dead_timer = 0
                self.dead_timer += 1
                if self.dead_timer >= 120: # 躺地上 120 帧 (约 2 秒) 后再消失
                    self.kill()
                    
            # 渲染死亡画面并提前返回，不跑下面的普通逻辑
            image = self.animations['dead'][int(self.frame_index)]
            if not self.facing_right:
                self.image = pygame.transform.flip(image, True, False)
            else:
                self.image = image
            return

        # 2. 其他普通动作的动画逻辑
        self.frame_index += self.animation_speed
        
        if self.frame_index >= len(self.animations[self.state]):
            if self.is_hurt:
                self.is_hurt = False
                self.state = 'walk'
                self.frame_index = 0
            elif self.state == 'attack':
                self.is_attacking = False
                self.has_dealt_damage = False
                self.state = 'idle'
                self.attack_cooldown = 45  
                self.frame_index = 0
            else:
                self.frame_index = 0 

        image = self.animations[self.state][int(self.frame_index)]
        
        if not self.facing_right:
            self.image = pygame.transform.flip(image, True, False)
        else:
            self.image = image

    def update(self, player):
        # 1. 受击判定
        if self.hp < self.last_hp and not self.is_dead:
            self.show_hp_timer = 300  # 【新增】受到伤害，重置为 300 帧 (5秒)
            if self.hp <= 0:
                self.is_dead = True
                self.state = 'dead'
            else:
                self.is_hurt = True
                self.state = 'hurt'
            self.frame_index = 0
            self.last_hp = self.hp

        # 2. AI 行为逻辑
        if not self.is_dead and not self.is_hurt:
            # 【逻辑修复 2：状态锁定】一旦开始攻击，无视其他所有指令，直到动画自然播放完毕！
            if self.state == 'attack':
                pass 
            # 攻击处于冷却状态
            elif self.attack_cooldown > 0:
                self.attack_cooldown -= 1
                if self.state != 'idle':
                    self.state = 'idle'
                    self.frame_index = 0
            # 正常思考状态
            else:
                if player:
                    if self.rect.centerx < player.rect.centerx:
                        self.facing_right = True
                    else:
                        self.facing_right = False
                        
                    distance = abs(self.rect.centerx - player.rect.centerx)
                    
                    if distance <= 80: 
                        # 【逻辑修复 3：重置帧】切入攻击时，强制从第 0 帧开始！
                        self.state = 'attack'
                        self.frame_index = 0
                        self.has_dealt_damage = False
                    else: 
                        if self.state != 'walk':
                            self.state = 'walk'
                            self.frame_index = 0
                            
                        if self.facing_right:
                            self.rect.x += self.speed
                        else:
                            self.rect.x -= self.speed

        # 3. 动画驱动伤害
        # 当动画播放到挥刀那一帧 (第 3 帧) 造成伤害
        if self.state == 'attack' and int(self.frame_index) == 3 and not self.has_dealt_damage:
            if player and self.rect.colliderect(player.rect):
                player.take_damage(self.attack_damage)
                print(f"🪓 兽人重砍！造成 {self.attack_damage} 点伤害！")
            self.has_dealt_damage = True

    def draw_health_bar(self, screen):
        """绘制头顶动态血条 (受击后显示 5 秒)"""
        # 如果还没死，并且计时器大于 0，才绘制
        if getattr(self, 'show_hp_timer', 0) > 0 and not self.is_dead:
            self.show_hp_timer -= 1  # 倒计时流逝
            
            bar_width = 40
            bar_height = 6
            # 算出头顶的正中位置 (往上偏移 15 像素)
            x = self.rect.centerx - bar_width // 2
            y = self.rect.top - 15
            
            # 计算当前血量百分比 (加 max 防止变负数)
            health_ratio = max(0, self.hp / getattr(self, 'max_hp', 1))
            
            # 画黑灰色底框
            pygame.draw.rect(screen, (40, 40, 40), (x, y, bar_width, bar_height))
            # 画红色的当前血量
            pygame.draw.rect(screen, (220, 20, 60), (x, y, int(bar_width * health_ratio), bar_height))
            # 画白色的外边框
            pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 1)

        self.update_animation()

# ----------------------------------------------------
# 怪物 2：蓝火法师 (代码类名保留为 SwampMoth 防止 main.py 报错)
# ----------------------------------------------------
class MothSpike(pygame.sprite.Sprite):
    """法师发射的炫酷幽蓝魔法球 (修复了外太空逃逸Bug)"""
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        
        self.size = 28
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.hp = 1 
        
        angle = math.atan2(target_y - y, target_x - x)
        speed = 6 
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        # 【新增】使用浮点数精确记录坐标，防止 Pygame 整数截断导致弹道变形
        self.exact_x = float(self.rect.x)
        self.exact_y = float(self.rect.y)
        
        self.timer = 0  

        self.score_value = 20
        self.score_given = False

    def draw_glowing_effect(self):
        """核心特效：每一帧在透明画布上动态绘制多层能量重叠效果"""
        self.image.fill((0, 0, 0, 0))
        self.timer += 0.4
        pulse = math.sin(self.timer) * 3 
        center = (self.size // 2, self.size // 2)
        
        # 三层光晕叠加
        outer_radius = max(5, int(11 + pulse))
        pygame.draw.circle(self.image, (0, 120, 255, 70), center, outer_radius)
        mid_radius = max(3, int(6 + pulse * 0.5))
        pygame.draw.circle(self.image, (80, 200, 255), center, mid_radius)
        inner_radius = 2
        pygame.draw.circle(self.image, (255, 255, 255), center, inner_radius)

    def update(self, player):
        self.draw_glowing_effect()
        
        # 【修复】使用精确的浮点数累加，然后再赋值给 rect，让子弹指哪打哪
        self.exact_x += self.vx
        self.exact_y += self.vy
        self.rect.x = int(self.exact_x)
        self.rect.y = int(self.exact_y)
        
        if player and self.rect.colliderect(player.rect):
            player.take_damage(5) 
            print("📌 玩家被幽蓝法球击中，扣除 5 点 HP！")
            self.kill() 
            
        # 【核心修复】加上了 self.rect.y < -500，封死上方的天空边界！
        if self.rect.y > 1000 or self.rect.y < -500 or self.rect.x < -1000 or self.rect.x > 3000:
            self.kill()

class SwampMoth(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        self.state = 'walk'            
        self.facing_right = False      
        self.animations = {'walk': [], 'attack': [], 'dead': []}
        self.frame_index = 0           
        self.animation_speed = 0.2     
        
        # 【关键】请确保图片命名为 mage_sheet.png 放在这个路径下
        self.load_animations(path="assets/sprites/enemies/mage_sheet.png")
        
        self.image = self.animations[self.state][self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))

        self.hp = 15
        self.speed = 2
        self.start_y = y
        self.timer = 0
        
        # 战斗属性
        self.is_dead = False
        self.shoot_timer = 0
        self.has_shot = False  # 确保一次施法只发射一颗子弹

        self.max_hp = self.hp     # 记录最大血量，用于计算血条比例
        self.show_hp_timer = 0    # 显血计时器

    def kill(self):
        """【拦截 main.py 的瞬间删除指令】"""
        if not getattr(self, 'is_dead', False):
            self.hp = 0
            self.is_dead = True
            self.state = 'dead'
            self.frame_index = 0
            # 缩小子弹碰撞框，变成一具无法挡子弹的尸体
            self.rect.width = 0
            self.rect.height = 0
            return 

        if hasattr(self, 'dead_timer') and self.dead_timer >= 120:
            super().kill()

    def load_animations(self, path):
        """读取 3行 9列 的单张精灵图"""
        if os.path.exists(path):
            sheet = pygame.image.load(path).convert_alpha()
            # 【自动抠图】如果你保存的 PNG 带有那个浅灰色的背景，这行代码会自动把它抠成透明！
            colorkey = sheet.get_at((0, 0))
            sheet.set_colorkey(colorkey)
        else:
            print(f"⚠️ 找不到图片 {path}，使用默认方块")
            sheet = pygame.Surface((900, 300))
            sheet.fill((150, 50, 150))

        # 根据图片结构：网格最宽有 9 帧，总共有 3 行
        frame_width = sheet.get_width() // 9
        frame_height = sheet.get_height() // 3
        
        # 你的图片结构定义：
        # 第 0 行 (第一行)：死亡 (9帧)
        # 第 1 行 (第二行)：攻击 (6帧)
        # 第 2 行 (第三行)：移动 (4帧)
        animation_config = {
            'dead':   {'row': 0, 'frames': 9},
            'attack': {'row': 1, 'frames': 6},
            'walk':   {'row': 2, 'frames': 4}
        }

        scale = 2.0 
        
        for state, info in animation_config.items():
            row = info['row']
            num_frames = info['frames']
            for i in range(num_frames):
                img = pygame.Surface((frame_width, frame_height)).convert()
                # 填充背景色以便抠图
                if os.path.exists(path): img.fill(colorkey)
                img.blit(sheet, (0, 0), (i * frame_width, row * frame_height, frame_width, frame_height))
                if os.path.exists(path): img.set_colorkey(colorkey)
                
                img = pygame.transform.scale(img, (int(frame_width * scale), int(frame_height * scale)))
                self.animations[state].append(img)

    def update_animation(self):
        # 1. 死亡动画拦截
        if self.state == 'dead':
            if self.frame_index < len(self.animations['dead']) - 1:
                self.frame_index += self.animation_speed
            else:
                self.frame_index = len(self.animations['dead']) - 1 
                if not hasattr(self, 'dead_timer'): self.dead_timer = 0
                self.dead_timer += 1
                if self.dead_timer >= 120: self.kill()
                    
            image = self.animations['dead'][int(self.frame_index)]
            self.image = pygame.transform.flip(image, True, False) if not self.facing_right else image
            return

        # 2. 正常动作循环
        self.frame_index += self.animation_speed
        
        if self.frame_index >= len(self.animations[self.state]):
            if self.state == 'attack':
                # 施法结束，恢复漂浮状态
                self.state = 'walk'
                self.has_shot = False
            self.frame_index = 0 

        image = self.animations[self.state][int(self.frame_index)]
        self.image = pygame.transform.flip(image, True, False) if not self.facing_right else image

    def update(self, player):
        # 1. 死亡状态锁定
        if self.is_dead:
            self.update_animation()
            return
        
        # 【新增】法师的扣血检测与计时器激活
        if not hasattr(self, 'last_hp'): self.last_hp = self.hp
        if self.hp < self.last_hp:
            self.show_hp_timer = 300  # 受到伤害，重置为 300 帧 (5秒)
            self.last_hp = self.hp
            
        # 2. 扣血转死亡
        if self.hp <= 0:
            self.kill()
            return

        # 3. 悬浮与 AI 逻辑
        self.timer += 1
        self.rect.y = self.start_y + int(math.sin(self.timer * 0.05) * 30)
        
        if player:
            # 转向玩家
            self.facing_right = True if self.rect.centerx < player.rect.centerx else False
                
            # 保持安全距离 (大约 300 像素)
            distance_x = abs(self.rect.centerx - player.rect.centerx)
            if self.state != 'attack':
                if distance_x > 300:
                    self.rect.x += self.speed if self.facing_right else -self.speed
            
            # 冷却计时器
            self.shoot_timer += 1
            if self.shoot_timer >= 120 and self.state != 'attack':  
                self.state = 'attack'
                self.frame_index = 0
                self.shoot_timer = 0
                
            # 【动画驱动射击】当法师举起火球 (假设是第 3 帧)，才真正把子弹发射出去！
            if self.state == 'attack' and int(self.frame_index) == 3 and not self.has_shot:
                spike = MothSpike(self.rect.centerx, self.rect.bottom, player.rect.centerx, player.rect.centery)
                for group in self.groups():
                    group.add(spike)
                self.has_shot = True

    def draw_health_bar(self, screen):
        """绘制头顶动态血条 (受击后显示 5 秒)"""
        # 如果还没死，并且计时器大于 0，才绘制
        if getattr(self, 'show_hp_timer', 0) > 0 and not self.is_dead:
            self.show_hp_timer -= 1  # 倒计时流逝
            
            bar_width = 40
            bar_height = 6
            # 算出头顶的正中位置 (往上偏移 15 像素)
            x = self.rect.centerx - bar_width // 2
            y = self.rect.top - 15
            
            # 计算当前血量百分比 (加 max 防止变负数)
            health_ratio = max(0, self.hp / getattr(self, 'max_hp', 1))
            
            # 画黑灰色底框
            pygame.draw.rect(screen, (40, 40, 40), (x, y, bar_width, bar_height))
            # 画红色的当前血量
            pygame.draw.rect(screen, (220, 20, 60), (x, y, int(bar_width * health_ratio), bar_height))
            # 画白色的外边框
            pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 1)

        self.update_animation()

# ----------------------------------------------------
# 怪物 3：跳跃突击者 (绿皮地精 / 抛物线精准制导扑击)
# ----------------------------------------------------
class PoisonToad(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        self.state = 'idle'            
        self.facing_right = False      
        self.animations = {'idle': [], 'jump': [], 'attack': [], 'hurt': [], 'dead': []}
        self.frame_index = 0           
        self.animation_speed = 0.2     
        
        self.load_animations(base_path="assets/sprites/enemies/goblin/")
        
        self.image = self.animations[self.state][self.frame_index]
        
        self.y_offset = 15  
        self.ground_y = y + self.y_offset
        self.rect = self.image.get_rect(bottomleft=(x, self.ground_y))
        
        # 精确 X 坐标，防止抛物线计算时掉帧卡顿
        self.exact_x = float(self.rect.x)

        self.hp = 20
        self.last_hp = 20              
        self.attack_damage = 8
        self.jump_force = -12      # 跳跃高度
        
        self.vy = 0
        self.vx = 0                # 跳跃时的水平移动速度
        self.jump_timer = 0
        self.is_jumping = False

        self.is_hurt = False
        self.is_dead = False
        self.attack_cooldown = 0
        self.has_dealt_damage = False  

        self.max_hp = self.hp     # 记录最大血量，用于计算血条比例
        self.show_hp_timer = 0    # 显血计时器

        self.score_value = 30
        self.score_given = False

    def kill(self):
        if not getattr(self, 'is_dead', False):
            self.hp = 0
            self.is_dead = True
            self.state = 'dead'
            self.frame_index = 0
            self.rect.width = 0
            self.rect.height = 0
            return 

        if hasattr(self, 'dead_timer') and self.dead_timer >= 120:
            super().kill()

    def load_animations(self, base_path):
        animation_config = {
            'idle':   {'file': 'Idle.png', 'frames': 5},
            'jump':   {'file': 'Jump.png', 'frames': 8}, 
            'attack': {'file': 'Attack_1.png', 'frames': 4},
            'hurt':   {'file': 'Hurt.png', 'frames': 2},
            'dead':   {'file': 'Dead.png', 'frames': 4}
        }

        scale = 1.3 
        for state, info in animation_config.items():
            path = os.path.join(base_path, info['file'])
            if os.path.exists(path):
                sheet = pygame.image.load(path).convert_alpha()
                frame_width = sheet.get_width() // info['frames']
                frame_height = sheet.get_height()
                for i in range(info['frames']):
                    img = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA).convert_alpha()
                    img.blit(sheet, (0, 0), (i * frame_width, 0, frame_width, frame_height))
                    img = pygame.transform.scale(img, (int(frame_width * scale), int(frame_height * scale)))
                    self.animations[state].append(img)
            else:
                print(f"⚠️ 找不到图片 {path}")
                frame_width, frame_height = 100, 100
                for i in range(info['frames']):
                    img = pygame.Surface((int(frame_width * scale), int(frame_height * scale)))
                    img.fill((50, 150, 50)) 
                    self.animations[state].append(img)

    def update_animation(self):
        if self.state == 'dead':
            if self.frame_index < len(self.animations['dead']) - 1:
                self.frame_index += self.animation_speed
            else:
                self.frame_index = len(self.animations['dead']) - 1 
                if not hasattr(self, 'dead_timer'): self.dead_timer = 0
                self.dead_timer += 1
                if self.dead_timer >= 120: self.kill()
                    
            image = self.animations['dead'][int(self.frame_index)]
            self.image = pygame.transform.flip(image, True, False) if not self.facing_right else image
            return

        self.frame_index += self.animation_speed
        
        if self.frame_index >= len(self.animations[self.state]):
            if self.is_hurt:
                self.is_hurt = False
                self.state = 'idle'
                self.frame_index = 0
            elif self.state == 'attack':
                self.has_dealt_damage = False
                self.state = 'idle'
                self.attack_cooldown = 45  
                self.frame_index = 0
            else:
                self.frame_index = 0 

        if self.state == 'jump' and self.frame_index >= len(self.animations['jump']):
            self.frame_index = len(self.animations['jump']) - 1

        image = self.animations[self.state][int(self.frame_index)]
        self.image = pygame.transform.flip(image, True, False) if not self.facing_right else image

    def update(self, player):
        if self.is_dead:
            self.update_animation()
            return

        if self.hp < self.last_hp and not self.is_dead:
            self.show_hp_timer = 300  # 【新增】受到伤害，重置为 300 帧 (5秒)
            if self.hp <= 0:
                self.is_dead = True
                self.state = 'dead'
                self.frame_index = 0
            else:
                self.is_hurt = True
                self.state = 'hurt'
                self.frame_index = 0
            self.last_hp = self.hp

        if not self.is_hurt:
            # 【物理引擎升级：加入水平速度 vx 的抛物线控制】
            self.vy += 1.0
            self.rect.y += self.vy
            
            if self.is_jumping:
                self.exact_x += self.vx
                self.rect.x = int(self.exact_x)
            else:
                self.exact_x = float(self.rect.x) # 站立时保持同步
            
            if self.rect.bottom >= self.ground_y:
                self.rect.bottom = self.ground_y
                self.vy = 0
                self.vx = 0 # 落地时立刻清空水平速度，不滑步
                if self.is_jumping:
                    self.is_jumping = False
                    self.state = 'idle' 

            if self.state == 'attack':
                pass 
            elif self.attack_cooldown > 0:
                self.attack_cooldown -= 1
            else:
                if player:
                    if not self.is_jumping:
                        self.facing_right = True if self.rect.centerx < player.rect.centerx else False
                    distance = abs(self.rect.centerx - player.rect.centerx)
                    
                    if not self.is_jumping:
                        if distance <= 100: 
                            self.state = 'attack'
                            self.frame_index = 0
                            self.has_dealt_damage = False
                        else:
                            self.state = 'idle'
                            self.jump_timer += 1
                            if self.jump_timer > 90:  
                                
                                # 1. 目标不是玩家的正中心，而是玩家“身前”的一点点距离，防穿模
                                target_x = player.rect.centerx
                                if target_x > self.rect.centerx:
                                    target_x -= 40
                                else:
                                    target_x += 40
                                    
                                # 2. 计算需要跨越的总距离 dx
                                dx = target_x - self.rect.centerx
                                
                                # 3. 根据重力系统反推滞空时间 (初始速度 10，重力 0.5，上下刚好各 20 帧，总计 40 帧)
                                air_time = 24
                                
                                # 4. 速度 = 距离 / 时间
                                self.vx = dx / air_time
                                # ==========================================
                                
                                self.vy = self.jump_force   
                                self.is_jumping = True
                                self.state = 'jump'
                                self.frame_index = 0
                                self.jump_timer = 0
                    else:
                        self.state = 'jump'

        if self.state == 'attack' and int(self.frame_index) == 2 and not self.has_dealt_damage:
            if player and self.rect.colliderect(player.rect):
                player.take_damage(self.attack_damage)
                print(f"🐸 绿皮地精跳跃重击！造成 {self.attack_damage} 点伤害！")
            self.has_dealt_damage = True

    def draw_health_bar(self, screen):
        """绘制头顶动态血条 (受击后显示 5 秒)"""
        # 如果还没死，并且计时器大于 0，才绘制
        if getattr(self, 'show_hp_timer', 0) > 0 and not self.is_dead:
            self.show_hp_timer -= 1  # 倒计时流逝
            
            bar_width = 40
            bar_height = 6
            # 算出头顶的正中位置 (往上偏移 15 像素)
            x = self.rect.centerx - bar_width // 2
            y = self.rect.top - 15
            
            # 计算当前血量百分比 (加 max 防止变负数)
            health_ratio = max(0, self.hp / getattr(self, 'max_hp', 1))
            
            # 画黑灰色底框
            pygame.draw.rect(screen, (40, 40, 40), (x, y, bar_width, bar_height))
            # 画红色的当前血量
            pygame.draw.rect(screen, (220, 20, 60), (x, y, int(bar_width * health_ratio), bar_height))
            # 画白色的外边框
            pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 1)

        self.update_animation()

# ==========================================
# 最终 Boss 专属物件与特效
# ==========================================

class BossSpike(pygame.sprite.Sprite):
    # BOSS Skill 1
    def __init__(self, x, y, angle_offset, target_x, target_y):
        super().__init__()
        self.size = 32
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.hp = 1 
        
        base_angle = math.atan2(target_y - y, target_x - x)
        final_angle = base_angle + angle_offset
        speed = 8 
        self.exact_x = float(x)
        self.exact_y = float(y)
        self.vx = math.cos(final_angle) * speed
        self.vy = math.sin(final_angle) * speed
        
        angle_deg = math.degrees(final_angle)
        base_img = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.polygon(base_img, (255, 20, 147, 100), [(0, 16), (32, 16), (20, 8), (20, 24)]) 
        pygame.draw.polygon(base_img, (200, 0, 100), [(4, 16), (28, 16), (20, 12), (20, 20)])      
        pygame.draw.polygon(base_img, (255, 200, 220), [(12, 16), (24, 16), (20, 14), (20, 18)])   
        
        self.image = pygame.transform.rotate(base_img, -angle_deg)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, player):
        self.exact_x += self.vx
        self.exact_y += self.vy
        self.rect.x = int(self.exact_x)
        self.rect.y = int(self.exact_y)
        
        hitbox = self.rect.inflate(-16, -16)
        
        if player and hitbox.colliderect(player.rect):
            player.take_damage(8) 
            self.kill() 
            
        if self.rect.y > 1000 or self.rect.y < -500 or self.rect.x < -1000 or self.rect.x > 3000:
            self.kill()

class TrackingSpike(pygame.sprite.Sprite):
    # BOSS Skill 3
    def __init__(self, position_type, shared_state, player):
        super().__init__()
        self.size = 70  
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA).convert_alpha()
        self.rect = self.image.get_rect()
        
        self.hp = 20 
        
        self.position_type = position_type
        self.shared_state = shared_state
        self.player = player
        
        self.exact_x = 0.0
        self.exact_y = 0.0
        self.vx = 0
        self.vy = 0
        self.fired = False
        
        self.lock_timer = 0
        self.track_timer = 0 

    def draw_crystal(self, angle_deg):
        self.image.fill((0,0,0,0))
        base_img = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.polygon(base_img, (255, 20, 147, 80), [(0, 35), (70, 35), (35, 15), (35, 55)])
        pygame.draw.polygon(base_img, (180, 0, 80), [(10, 35), (60, 35), (35, 22), (35, 48)])
        pygame.draw.polygon(base_img, (255, 150, 200), [(20, 35), (50, 35), (35, 28), (35, 42)])
        
        self.image = pygame.transform.rotate(base_img, -angle_deg)
        self.rect = self.image.get_rect(center=self.rect.center)

    def kill(self):
        if self.shared_state.get('tracking', True):
            print("玩家打碎了巨刺阵眼！追踪立即停止！")
            self.shared_state['tracking'] = False
            self.shared_state['reason'] = 'broken'
        super().kill()

    def update(self, player_ignored):
        hitbox = self.rect.inflate(-30, -30)
        
        if self.shared_state.get('tracking', True):
            # Phase 1: Follow closely and start a 2-second countdown.
            self.track_timer += 1
            if self.track_timer >= 120: 
                print("2秒追踪时间到! 惩罚机制触发！大毒刺将直接锁定玩家！")
                self.shared_state['tracking'] = False 
                self.shared_state['reason'] = 'timeout'
                
            offset = 120
            if self.position_type == 'top': target = (self.player.rect.centerx, self.player.rect.centery - offset)
            elif self.position_type == 'bottom': target = (self.player.rect.centerx, self.player.rect.centery + offset)
            elif self.position_type == 'left': target = (self.player.rect.centerx - offset, self.player.rect.centery)
            elif self.position_type == 'right': target = (self.player.rect.centerx + offset, self.player.rect.centery)
                
            self.rect.center = target
            self.exact_x, self.exact_y = self.rect.x, self.rect.y
            
            # The spearhead is aimed at the player
            angle = math.atan2(self.player.rect.centery - self.rect.centery, self.player.rect.centerx - self.rect.centerx)
            self.draw_crystal(math.degrees(angle))
            
            if hitbox.colliderect(self.player.rect):
                self.player.take_damage(10)
                self.kill()
        else:
            # Phase 2: Determine subsequent actions based on the reason for termination.
            self.lock_timer += 1
            
            # Scenario A: Released due to timeout
            if self.shared_state.get('reason') == 'timeout':
                if self.lock_timer == 1:
                    # Instantly lock onto the player's current location and launch.
                    angle = math.atan2(self.player.rect.centery - self.rect.centery, self.player.rect.centerx - self.rect.centerx)
                    speed = 18  
                    self.vx = math.cos(angle) * speed
                    self.vy = math.sin(angle) * speed
                    self.draw_crystal(math.degrees(angle))
                    self.fired = True

            # Situation B: The issue is resolved because the player broke one of the pillars.
            elif self.shared_state.get('reason') == 'broken':
                if self.lock_timer == 1:
                    if self.position_type == 'top': self.draw_crystal(-90)
                    elif self.position_type == 'bottom': self.draw_crystal(90)
                    elif self.position_type == 'left': self.draw_crystal(180)
                    elif self.position_type == 'right': self.draw_crystal(0)
                    
                if self.lock_timer >= 120 and not self.fired:
                    speed = 15
                    if self.position_type == 'top': self.vx, self.vy = 0, -speed
                    elif self.position_type == 'bottom': self.vx, self.vy = 0, speed
                    elif self.position_type == 'left': self.vx, self.vy = -speed, 0
                    elif self.position_type == 'right': self.vx, self.vy = speed, 0
                    self.fired = True
                
            # Execute post-launch movement logic
            if self.fired:
                self.exact_x += self.vx
                self.exact_y += self.vy
                self.rect.x = int(self.exact_x)
                self.rect.y = int(self.exact_y)
                
                if hitbox.colliderect(self.player.rect):
                    self.player.take_damage(15)
                    print("玩家被 Boss 巨型毒刺命中！")
                    self.kill()
                    
                if self.rect.y > 1000 or self.rect.y < -500 or self.rect.x < -1000 or self.rect.x > 3000:
                    self.kill()

# ----------------------------------------------------
# 最终 Boss：HECATE
# ----------------------------------------------------
class Hecate(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        if x > 1100: x = 1100
        self.exact_x = float(x) 

        self.state = 'idle'            
        self.facing_right = False      
        self.animations = {
            'idle': [], 'walk': [], 'run': [], 
            'attack1': [], 'attack2': [], 'attack3': [], 
            'scream': [], 
            'hurt': [], 'dead': []
        }
        self.frame_index = 0           
        self.animation_speed = 0.2     
        
        self.load_animations(base_path="assets/sprites/enemies/Level3_Boss/")
        
        self.image = self.animations[self.state][self.frame_index]
        self.y_offset = 20  
        self.ground_y = y + self.y_offset
        self.rect = self.image.get_rect(bottomleft=(x, self.ground_y))

        self.hp = 150
        self.last_hp = 150 
        self.max_hp = 150             
        self.walk_speed = 1.5
        self.run_speed = 7.0       
        
        self.attack_cooldown = 120    
        self.ult_cooldown = 0         
        
        # 半血状态记录与自带毒气系统
        self.has_screamed = False
        self.boss_gas = BossPoisonGasSystem(1280, 720) 
        
        self.current_action_done = True
        self.has_fired = False
        self.is_hurt = False
        self.is_dead = False

        self.score_value = 500
        self.score_given = False

    def kill(self):
        if not getattr(self, 'is_dead', False):
            self.hp = 0
            self.is_dead = True
            self.state = 'dead'
            self.frame_index = 0
            self.rect.width = 0
            self.rect.height = 0
            return 
        if hasattr(self, 'dead_timer') and self.dead_timer >= 180: 
            super().kill()

    def load_animations(self, base_path):
        animation_config = {
            'idle':    {'file': 'Idle.png', 'frames': 5},
            'walk':    {'file': 'Walk.png', 'frames': 5}, 
            'run':     {'file': 'Run.png', 'frames': 5}, 
            'attack1': {'file': 'Attack_4.png', 'frames': 7}, 
            'attack2': {'file': 'Attack_2.png', 'frames': 4}, 
            'attack3': {'file': 'Attack_3.png', 'frames': 7}, 
            'scream':  {'file': 'Scream.png', 'frames': 4}, 
            'hurt':    {'file': 'Hurt.png', 'frames': 3},
            'dead':    {'file': 'Dead.png', 'frames': 4}
        }
        scale = 1.8 
        for state, info in animation_config.items():
            path = os.path.join(base_path, info['file'])
            if os.path.exists(path):
                sheet = pygame.image.load(path).convert_alpha()
                fw = sheet.get_width() // info['frames']
                fh = sheet.get_height()
                for i in range(info['frames']):
                    img = pygame.Surface((fw, fh), pygame.SRCALPHA).convert_alpha()
                    img.blit(sheet, (0, 0), (i * fw, 0, fw, fh))
                    img = pygame.transform.scale(img, (int(fw * scale), int(fh * scale)))
                    self.animations[state].append(img)
            else:
                fw, fh = 100, 100
                for i in range(info['frames']):
                    img = pygame.Surface((int(fw * scale), int(fh * scale)))
                    img.fill((100, 0, 100)) 
                    self.animations[state].append(img)

    def update_animation(self):
        if self.state == 'dead':
            if self.frame_index < len(self.animations['dead']) - 1:
                self.frame_index += self.animation_speed
            else:
                self.frame_index = len(self.animations['dead']) - 1 
                if not hasattr(self, 'dead_timer'): self.dead_timer = 0
                self.dead_timer += 1
                if self.dead_timer >= 180: self.kill()
            img = self.animations['dead'][int(self.frame_index)]
            self.image = pygame.transform.flip(img, True, False) if not self.facing_right else img
            return

        self.frame_index += self.animation_speed
        
        if self.frame_index >= len(self.animations[self.state]):
            if self.is_hurt:
                self.is_hurt = False
            
            if self.state in ['attack1', 'attack2', 'attack3', 'run', 'scream']:
                self.current_action_done = True
                self.attack_cooldown = 90  
            
            self.state = 'idle'
            self.frame_index = 0 

        img = self.animations[self.state][int(self.frame_index)]
        self.image = pygame.transform.flip(img, True, False) if not self.facing_right else img

    def update(self, player):
        if self.is_dead:
            self.update_animation()
            return

        # 让毒气系统保持运转
        self.boss_gas.update(player)

        if self.ult_cooldown > 0:
            self.ult_cooldown -= 1

        # Half-health transition mechanism
        if self.hp <= self.max_hp * 0.5 and not self.has_screamed and not self.is_dead:
            self.has_screamed = True
            self.state = 'scream'
            self.frame_index = 0
            self.current_action_done = False
            self.has_fired = False
            self.is_hurt = False  # Clears hit recovery stun and grants super armor.

        if self.hp < self.last_hp:
            if self.hp <= 0:
                self.is_dead = True
                self.state = 'dead'
                self.frame_index = 0
            # 只有在非大招、非尖叫阶段，才会产生受击硬直
            elif self.state in ['idle', 'walk']:
                self.is_hurt = True
                self.state = 'hurt'
                self.frame_index = 0
            self.last_hp = self.hp

        if not self.is_hurt:
            if player:
                distance = abs(self.rect.centerx - player.rect.centerx)
                if self.state not in ['attack1', 'attack2', 'attack3', 'run', 'scream']:
                    self.facing_right = True if self.rect.centerx < player.rect.centerx else False
                
                # Half-health skill
                if self.state == 'scream':
                    # When the screaming animation plays to frame 2, poison gas is released.
                    if int(self.frame_index) == 2 and not self.has_fired:
                        self.boss_gas.trigger()
                        self.has_fired = True

                # AI decision-making
                else:
                    if self.current_action_done and self.attack_cooldown <= 0:
                        self.current_action_done = False
                        self.has_fired = False
                        self.frame_index = 0
                        
                        if self.ult_cooldown <= 0 and random.random() < 0.20:
                            print("Boss 释放大招：追踪巨型毒刺！")
                            self.state = 'attack3'
                            self.ult_cooldown = 600  
                        else:
                            if random.random() < 0.50:
                                print("Boss 释放技能 1: 深粉红散弹！")
                                self.state = 'attack1'
                            else:
                                print("Boss 释放技能 2: 致命冲锋！")
                                self.state = 'run'
                            
                    elif self.current_action_done:
                        self.attack_cooldown -= 1
                        self.state = 'walk'
                        self.exact_x += self.walk_speed if self.facing_right else -self.walk_speed
                        self.rect.x = int(self.exact_x)

                    # --- 普通技能执行 ---
                    if self.state == 'attack1' and int(self.frame_index) == 4 and not self.has_fired:
                        angles = [-0.3, 0, 0.3] 
                        for angle in angles:
                            spike = BossSpike(self.rect.centerx, self.rect.centery, angle, player.rect.centerx, player.rect.centery)
                            for group in self.groups(): group.add(spike)
                        self.has_fired = True
                        
                    if self.state == 'run':
                        self.exact_x += self.run_speed if self.facing_right else -self.run_speed
                        self.rect.x = int(self.exact_x)
                        if distance <= 120:
                            self.state = 'attack2'
                            self.frame_index = 0
                            self.has_fired = False
                            
                    if self.state == 'attack2' and int(self.frame_index) == 2 and not self.has_fired:
                        if self.rect.colliderect(player.rect):
                            player.take_damage(15)
                        self.has_fired = True
                        
                    if self.state == 'attack3' and int(self.frame_index) == 5 and not self.has_fired:
                        shared_state = {'tracking': True}
                        positions = ['top', 'bottom', 'left', 'right']
                        for pos in positions:
                            spike = TrackingSpike(pos, shared_state, player)
                            for group in self.groups(): group.add(spike)
                        self.has_fired = True

        self.update_animation()

# ==========================================
# Boss 战专属 UI 与 警告特效
# ==========================================

class BossWarningEffect:
    def __init__(self, screen_width=1280, screen_height=720):
        self.width = screen_width
        self.height = screen_height
        self.active = False
        self.timer = 0
        
        # Pre-draw a red gradient striped canvas with alpha channels.
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        stripe_width = 150 
        
        for x in range(stripe_width):
            # The closer to the edge, the redder it is; the closer to the center of the screen, the more transparent it becomes.
            alpha = int(255 * (1 - (x / stripe_width)))
            pygame.draw.line(self.surface, (200, 0, 0, alpha), (x, 0), (x, self.height))
            pygame.draw.line(self.surface, (200, 0, 0, alpha), (self.width - 1 - x, 0), (self.width - 1 - x, self.height))

    def trigger(self):
        self.active = True
        self.timer = 180
        print("Boss 警告特效已触发！")

    def draw(self, screen):
        if self.active and self.timer > 0:
            self.timer -= 1
            # Calculate the transparency of the breathing flicker using a sine wave function.
            pulse_alpha = int(abs(math.sin(self.timer * 0.1)) * 150 + 50)
            
            # Duplicate the canvas and apply transparency to prevent alteration of the original artwork.
            temp_surface = self.surface.copy()
            temp_surface.set_alpha(pulse_alpha)
            screen.blit(temp_surface, (0, 0))
        else:
            self.active = False

# ==========================================
# Boss 半血大招：全屏深粉色毒气系统 (带锁血保护)
# ==========================================
class BossPoisonGasSystem:
    def __init__(self, screen_width=1280, screen_height=720):
        self.width = screen_width
        self.height = screen_height
        self.active = False
        self.timer = 0
        self.damage_tick = 0
        
        # Deep pink edge shading
        self.vignette = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for i in range(40):
            alpha = 120 - i * 3
            if alpha < 0: alpha = 0
            rect = pygame.Rect(i * 4, i * 4, self.width - i * 8, self.height - i * 8)
            pygame.draw.rect(self.vignette, (180, 20, 100, alpha), rect, 4)

        # Deep pink poison spores
        self.particles = []
        for _ in range(50): 
            self.particles.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'speed': random.uniform(0.5, 2.0),
                'size': random.randint(2, 4)
            })

    def trigger(self):
        self.active = True
        self.timer = 600 
        self.damage_tick = 0
        print("HECATE 发出尖叫！全屏深粉色毒气爆发！")

    def update(self, player):
        if not self.active: return
        
        self.timer -= 1
        if self.timer > 0:
            # Particle motion
            for p in self.particles:
                p['y'] -= p['speed'] 
                p['x'] += math.sin(p['y'] * 0.05) * 1.5 
                if p['y'] < -10:
                    p['y'] = self.height + 10
                    p['x'] = random.randint(0, self.width)
                    
            # Blood deduction once every second
            self.damage_tick += 1
            if self.damage_tick >= 60: 
                self.damage_tick = 0
                
                # Invincibility Mechanism
                if player.hp > 1:
                    player.hp -= 4
                    # Forcibly locked at 1 drop of blood
                    if player.hp < 1:
                        player.hp = 1
                        
                    print(f"Boss毒气侵!失去生命，当前强制剩余 {player.hp}!")
                    player.is_hurt = True
                    if hasattr(player, 'hurt_timer'): player.hurt_timer = 30
        else:
            self.active = False

    def draw(self, screen):
        if self.active and self.timer > 0:
            screen.blit(self.vignette, (0, 0))
            for p in self.particles:
                pygame.draw.circle(screen, (255, 20, 147, 180), (int(p['x']), int(p['y'])), p['size'])


# ----------------------------------------------------
# Boss 专属 UI (结合了动态头像与毒气渲染黑科技)
# ----------------------------------------------------
class BossHealthBar:
    def __init__(self):
        self.font = pygame.font.Font(None, 36) 
        self.portrait_bg = pygame.Surface((64, 64))
        self.portrait_bg.fill((40, 40, 40))

    def draw(self, screen, boss):
        if not boss or boss.is_dead:
            return
            
        # 【神级黑科技】：在画血条之前，利用已有的机制渲染全屏深粉色毒气！
        # 这样毒气既能覆盖全屏，又不会遮挡住 Boss 自己的高贵血条。
        if hasattr(boss, 'boss_gas'):
            boss.boss_gas.draw(screen)
            
        screen_width = screen.get_width()
        bar_width = 500  
        bar_height = 24
        
        start_x = (screen_width - bar_width) // 2 + 100
        start_y = 40  
        
        portrait_rect = pygame.Rect(start_x - 70, start_y - 20, 64, 64)
        pygame.draw.rect(screen, (200, 180, 50), portrait_rect, 3) 
        screen.blit(self.portrait_bg, (portrait_rect.x, portrait_rect.y))
        
        current_face = pygame.transform.scale(boss.image, (64, 64))
        screen.blit(current_face, (portrait_rect.x, portrait_rect.y))
        
        name_text = self.font.render("HECATE", True, (255, 220, 100))
        shadow_text = self.font.render("HECATE", True, (0, 0, 0))
        screen.blit(shadow_text, (start_x + 2, start_y - 30))  
        screen.blit(name_text, (start_x, start_y - 32))        
        
        bg_rect = pygame.Rect(start_x, start_y, bar_width, bar_height)
        pygame.draw.rect(screen, (30, 30, 30), bg_rect)
        pygame.draw.rect(screen, (150, 150, 150), bg_rect, 2) 
        
        health_ratio = max(0, boss.hp / getattr(boss, 'max_hp', 150))
        current_health_width = int(bar_width * health_ratio)
        if current_health_width > 0:
            hp_rect = pygame.Rect(start_x, start_y, current_health_width, bar_height)
            pygame.draw.rect(screen, (220, 20, 60), hp_rect)

# ==========================================
# 战斗视觉特效：受击十字闪光 (Hit Spark)
# ==========================================
class HitEffect(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = 80  # Special effects canvas size
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.timer = 12
        self.max_timer = 12

    def update(self, *args):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()  # Automatically destroys after animation ends.
        else:
            self.image.fill((0, 0, 0, 0))  # Clear the canvas of the previous frame
            
            # Dynamically calculate the expansion size and fade-out transparency of special effects.
            progress = 1 - (self.timer / self.max_timer)
            alpha = int(255 * (self.timer / self.max_timer))
            current_size = int(20 + 60 * progress) 
            
            center = self.size // 2
            offset = current_size // 2
            
            color = (255, 220, 50, alpha)
            
            # 1. Draw a horizontal slash of light
            pygame.draw.polygon(self.image, color, [
                (center - offset, center), (center, center - 3), 
                (center + offset, center), (center, center + 3)
            ])
            # 2. Draw a vertical slash of light
            pygame.draw.polygon(self.image, color, [
                (center, center - offset), (center + 3, center), 
                (center, center + offset), (center - 3, center)
            ])
            # 3. The white dot with extremely high brightness in the center
            core_radius = max(1, 8 - int(7 * progress))
            pygame.draw.circle(self.image, (255, 255, 255, alpha), (center, center), core_radius)

# ==========================================
# 关卡开场文字横幅 (渐变特效)
# ==========================================
class LevelBanner:
    def __init__(self, text="Level 3", screen_width=1280):
        self.font = pygame.font.Font(None, 80)
        self.text = text
        self.screen_width = screen_width
        
        self.text_surf = self.font.render(self.text, True, (255, 215, 0))
        
        # The center position is calculated to be exactly in the top center of the screen.
        self.rect = self.text_surf.get_rect(center=(self.screen_width // 2, 80))
        
        # Core control variables
        self.alpha = 0            
        self.state = 'fade_in'     
        self.hold_timer = 0        

    def update(self):
        if self.state == 'fade_in':
            self.alpha += 5         # Increase transparency by 5 points per frame.
            if self.alpha >= 255:
                self.alpha = 255
                self.state = 'hold'  # To achieve full display, switch to hold mode.
                self.hold_timer = 0
                
        elif self.state == 'hold':
            self.hold_timer += 1
            if self.hold_timer >= 90: 
                self.state = 'fade_out'
                
        elif self.state == 'fade_out':
            self.alpha -= 5         # Reduce transparency by 5 points per frame.
            if self.alpha <= 0:
                self.alpha = 0
                self.state = 'done'  # The animation has completely ended.

    def draw(self, screen):
        if self.state != 'done':
            # You must duplicate the text canvas before applying transparency; otherwise, it will taint the original canvas.
            temp_surf = self.text_surf.copy()
            temp_surf.set_alpha(self.alpha)
            screen.blit(temp_surf, self.rect)