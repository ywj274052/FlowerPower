import pygame
import math
import os
import random

class PoisonZone(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        # 创建一个支持透明度的表面，设为紫色半透明以符合毒液的视觉效果
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill((128, 0, 128, 120)) 
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # 伤害计时器
        self.damage_timer = 0

    def update(self, player):
        # 检测玩家的碰撞框是否和毒沼泽重叠
        if self.rect.colliderect(player.rect):
            self.damage_timer += 1
            # 假设游戏是 60 FPS，30 帧就是半秒
            if self.damage_timer >= 30: 
                player.hp -= 2
                self.damage_timer = 0
        else:
            # 玩家离开毒沼泽，立刻重置计时器
            self.damage_timer = 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# ==========================================
# Level 3 专属怪物系统
# ==========================================

class ToxicSludge(pygame.sprite.Sprite):
    """怪物 1：兽人步兵 (分离式 PNG 动画加载)"""
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
        
        # 【新增】精确 X 坐标，防止抛物线计算时掉帧卡顿
        self.exact_x = float(self.rect.x)

        self.hp = 20
        self.last_hp = 20              
        self.attack_damage = 8
        self.jump_force = -12      # 跳跃高度
        
        self.vy = 0
        self.vx = 0                # 【新增】跳跃时的水平移动速度
        self.jump_timer = 0
        self.is_jumping = False

        self.is_hurt = False
        self.is_dead = False
        self.attack_cooldown = 0
        self.has_dealt_damage = False  

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
                                # ==========================================
                                # 【全新追踪跳跃核心逻辑】
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

        self.update_animation()

import random

# ==========================================
# 最终 Boss 专属物件与特效
# ==========================================

class BossSpike(pygame.sprite.Sprite):
    """Boss 技能 1：深粉红散弹毒刺"""
    def __init__(self, x, y, angle_offset, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA).convert_alpha()
        # 画一个深粉红色的小毒刺
        pygame.draw.circle(self.image, (255, 20, 147), (8, 8), 6)
        pygame.draw.circle(self.image, (255, 180, 200), (8, 8), 3) # 高亮核心
        self.rect = self.image.get_rect(center=(x, y))
        self.hp = 1 
        
        # 计算基础角度，并加上偏移量形成散弹
        base_angle = math.atan2(target_y - y, target_x - x)
        final_angle = base_angle + angle_offset
        speed = 6 
        self.exact_x = float(x)
        self.exact_y = float(y)
        self.vx = math.cos(final_angle) * speed
        self.vy = math.sin(final_angle) * speed

    def update(self, player):
        self.exact_x += self.vx
        self.exact_y += self.vy
        self.rect.x = int(self.exact_x)
        self.rect.y = int(self.exact_y)
        
        if player and self.rect.colliderect(player.rect):
            player.take_damage(8) 
            print("💢 玩家被 Boss 散弹毒刺击中！")
            self.kill() 
            
        if self.rect.y > 1000 or self.rect.y < -500 or self.rect.x < -1000 or self.rect.x > 3000:
            self.kill()

class TrackingSpike(pygame.sprite.Sprite):
    """Boss 技能 3: 深粉红追踪巨型毒刺 (加入超时惩罚机制)"""
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
        """记录解除原因：如果是被打爆的，标记为 'broken'"""
        if self.shared_state.get('tracking', True):
            print("💥 漂亮！玩家打碎了巨刺阵眼！追踪立即停止！")
            self.shared_state['tracking'] = False
            self.shared_state['reason'] = 'broken'  # 【新增】告诉其他毒刺：我是被打碎的！
        super().kill()

    def update(self, player_ignored):
        hitbox = self.rect.inflate(-30, -30)
        
        if self.shared_state.get('tracking', True):
            # --- 阶段 1：死死跟随，并开启 5 秒倒计时 ---
            self.track_timer += 1
            if self.track_timer >= 300: 
                print("⚠️ 5秒追踪时间到！惩罚机制触发！大毒刺将直接锁定玩家！")
                self.shared_state['tracking'] = False 
                self.shared_state['reason'] = 'timeout' # 【新增】告诉其他毒刺：时间到了！
                
            offset = 120
            if self.position_type == 'top': target = (self.player.rect.centerx, self.player.rect.centery - offset)
            elif self.position_type == 'bottom': target = (self.player.rect.centerx, self.player.rect.centery + offset)
            elif self.position_type == 'left': target = (self.player.rect.centerx - offset, self.player.rect.centery)
            elif self.position_type == 'right': target = (self.player.rect.centerx + offset, self.player.rect.centery)
                
            self.rect.center = target
            self.exact_x, self.exact_y = self.rect.x, self.rect.y
            
            # 矛头对准玩家
            angle = math.atan2(self.player.rect.centery - self.rect.centery, self.player.rect.centerx - self.rect.centerx)
            self.draw_crystal(math.degrees(angle))
            
            if hitbox.colliderect(self.player.rect):
                self.player.take_damage(10)
                self.kill()
        else:
            # --- 阶段 2：根据解除原因，决定后续行为 ---
            self.lock_timer += 1
            
            # 情况 A：因为超时而解除 (惩罚机制：立刻朝玩家射击)
            if self.shared_state.get('reason') == 'timeout':
                if self.lock_timer == 1:
                    # 瞬间锁定玩家当前位置并发射，不给喘息时间！
                    angle = math.atan2(self.player.rect.centery - self.rect.centery, self.player.rect.centerx - self.rect.centerx)
                    speed = 18  # 弹道极快
                    self.vx = math.cos(angle) * speed
                    self.vy = math.sin(angle) * speed
                    self.draw_crystal(math.degrees(angle))
                    self.fired = True

            # 情况 B：因为玩家打碎了其中一根而解除 (奖励机制：停顿2秒，十字乱射)
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
                
            # 执行发射后的移动逻辑
            if self.fired:
                self.exact_x += self.vx
                self.exact_y += self.vy
                self.rect.x = int(self.exact_x)
                self.rect.y = int(self.exact_y)
                
                if hitbox.colliderect(self.player.rect):
                    self.player.take_damage(15)
                    print("📌 玩家被 Boss 巨型毒刺命中！")
                    self.kill()
                    
                if self.rect.y > 1000 or self.rect.y < -500 or self.rect.x < -1000 or self.rect.x > 3000:
                    self.kill()

# ----------------------------------------------------
# 最终 Boss：腐败萨满 (Rot Shaman)
# ----------------------------------------------------
# ==========================================
# 最终 Boss 专属物件与特效
# ==========================================

class BossSpike(pygame.sprite.Sprite):
    """Boss 技能 1：深粉红散弹毒刺 (已修复空气墙伤害)"""
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
        
        # 【核心修复：缩小判定框】
        # inflate(-16, -16) 意味着将物理判定框的宽高各缩小 16 像素。
        # 这样毒刺的边缘光晕就不会造成伤害，必须是“实体刺中”才会扣血！
        hitbox = self.rect.inflate(-16, -16)
        
        if player and hitbox.colliderect(player.rect):
            player.take_damage(8) 
            self.kill() 
            
        if self.rect.y > 1000 or self.rect.y < -500 or self.rect.x < -1000 or self.rect.x > 3000:
            self.kill()

class TrackingSpike(pygame.sprite.Sprite):
    """Boss 技能 3: 深粉红追踪巨型毒刺 (加入超时惩罚机制)"""
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
        """记录解除原因：如果是被打爆的，标记为 'broken'"""
        if self.shared_state.get('tracking', True):
            print("💥 漂亮！玩家打碎了巨刺阵眼！追踪立即停止！")
            self.shared_state['tracking'] = False
            self.shared_state['reason'] = 'broken'  # 【新增】告诉其他毒刺：我是被打碎的！
        super().kill()

    def update(self, player_ignored):
        hitbox = self.rect.inflate(-30, -30)
        
        if self.shared_state.get('tracking', True):
            # --- 阶段 1：死死跟随，并开启 5 秒倒计时 ---
            self.track_timer += 1
            if self.track_timer >= 300: 
                print("⚠️ 5秒追踪时间到！惩罚机制触发！大毒刺将直接锁定玩家！")
                self.shared_state['tracking'] = False 
                self.shared_state['reason'] = 'timeout' # 【新增】告诉其他毒刺：时间到了！
                
            offset = 120
            if self.position_type == 'top': target = (self.player.rect.centerx, self.player.rect.centery - offset)
            elif self.position_type == 'bottom': target = (self.player.rect.centerx, self.player.rect.centery + offset)
            elif self.position_type == 'left': target = (self.player.rect.centerx - offset, self.player.rect.centery)
            elif self.position_type == 'right': target = (self.player.rect.centerx + offset, self.player.rect.centery)
                
            self.rect.center = target
            self.exact_x, self.exact_y = self.rect.x, self.rect.y
            
            # 矛头对准玩家
            angle = math.atan2(self.player.rect.centery - self.rect.centery, self.player.rect.centerx - self.rect.centerx)
            self.draw_crystal(math.degrees(angle))
            
            if hitbox.colliderect(self.player.rect):
                self.player.take_damage(10)
                self.kill()
        else:
            # --- 阶段 2：根据解除原因，决定后续行为 ---
            self.lock_timer += 1
            
            # 情况 A：因为超时而解除 (惩罚机制：立刻朝玩家射击)
            if self.shared_state.get('reason') == 'timeout':
                if self.lock_timer == 1:
                    # 瞬间锁定玩家当前位置并发射，不给喘息时间！
                    angle = math.atan2(self.player.rect.centery - self.rect.centery, self.player.rect.centerx - self.rect.centerx)
                    speed = 18  # 弹道极快
                    self.vx = math.cos(angle) * speed
                    self.vy = math.sin(angle) * speed
                    self.draw_crystal(math.degrees(angle))
                    self.fired = True

            # 情况 B：因为玩家打碎了其中一根而解除 (奖励机制：停顿2秒，十字乱射)
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
                
            # 执行发射后的移动逻辑
            if self.fired:
                self.exact_x += self.vx
                self.exact_y += self.vy
                self.rect.x = int(self.exact_x)
                self.rect.y = int(self.exact_y)
                
                if hitbox.colliderect(self.player.rect):
                    self.player.take_damage(15)
                    print("📌 玩家被 Boss 巨型毒刺命中！")
                    self.kill()
                    
                if self.rect.y > 1000 or self.rect.y < -500 or self.rect.x < -1000 or self.rect.x > 3000:
                    self.kill()

# ----------------------------------------------------
# 最终 Boss：腐败萨满 (Rot Shaman)
# ----------------------------------------------------
class RotShaman(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        if x > 1100: x = 1100
        self.exact_x = float(x) 

        self.state = 'idle'            
        self.facing_right = False      
        self.animations = {
            'idle': [], 'walk': [], 'run': [], 
            'attack1': [], 'attack2': [], 'attack3': [], 
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
        self.walk_speed = 1.5
        self.run_speed = 7.0       
        self.attack_cooldown = 120 
        self.current_action_done = True
        self.has_fired = False

        self.is_hurt = False
        self.is_dead = False

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
            'hurt':    {'file': 'Hurt.png', 'frames': 3},
            'dead':    {'file': 'Dead.png', 'frames': 4}
        }
        scale = 2.0 
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
                # 依然保留紫块报错机制，没找到图就会变成紫块！
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
            
            if self.state in ['attack1', 'attack2', 'attack3', 'run']:
                self.current_action_done = True
                self.attack_cooldown = 90  # 技能后摇缩短，加快战斗节奏
            
            self.state = 'idle'
            self.frame_index = 0 

        img = self.animations[self.state][int(self.frame_index)]
        self.image = pygame.transform.flip(img, True, False) if not self.facing_right else img

    def update(self, player):
        if self.is_dead:
            self.update_animation()
            return

        if self.hp < self.last_hp:
            if self.hp <= 0:
                self.is_dead = True
                self.state = 'dead'
                self.frame_index = 0
            elif self.state in ['idle', 'walk']:
                self.is_hurt = True
                self.state = 'hurt'
                self.frame_index = 0
            self.last_hp = self.hp

        if not self.is_hurt:
            if player:
                distance = abs(self.rect.centerx - player.rect.centerx)
                if self.state not in ['attack1', 'attack2', 'attack3', 'run']:
                    self.facing_right = True if self.rect.centerx < player.rect.centerx else False
                
                # --- 【AI 重构】：概率调整 ---
                if self.current_action_done and self.attack_cooldown <= 0:
                    self.current_action_done = False
                    self.has_fired = False
                    self.frame_index = 0
                    
                    rand_val = random.random()
                    # 只有 20% 的几率触发大招！
                    if rand_val < 0.20:
                        print("💀 Boss 释放大招：追踪巨型毒刺！")
                        self.state = 'attack3'
                    # 40% 的几率触发散弹
                    elif rand_val < 0.60:
                        print("💀 Boss 释放技能 1: 深粉红散弹！")
                        self.state = 'attack1'
                    # 40% 的几率触发冲锋近战
                    else:
                        print("💀 Boss 释放技能 2: 致命冲锋！")
                        self.state = 'run'
                        
                elif self.current_action_done:
                    self.attack_cooldown -= 1
                    self.state = 'walk'
                    self.exact_x += self.walk_speed if self.facing_right else -self.walk_speed
                    self.rect.x = int(self.exact_x)

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
                        print("🩸 玩家受到 Boss 致命近战斩击！")
                    self.has_fired = True
                    
                if self.state == 'attack3' and int(self.frame_index) == 5 and not self.has_fired:
                    shared_state = {'tracking': True}
                    positions = ['top', 'bottom', 'left', 'right']
                    for pos in positions:
                        spike = TrackingSpike(pos, shared_state, player)
                        for group in self.groups(): group.add(spike)
                    self.has_fired = True

        self.update_animation()