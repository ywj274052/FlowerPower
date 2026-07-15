import pygame
import sys
import math
import random
import os
from settings import *
from player import Player, SeedShot
from enemy import Level2Scene
from level3_elements import PoisonGasSystem, ToxicSludge, SwampMoth, PoisonToad, Hecate, BossWarningEffect, BossHealthBar, HitEffect, LevelBanner

# ---------- 全局变量 ----------
game_state = "TITLE"
tutorial_timer = 0 
show_tutorial = True  
portal = None
show_portal = False
level1_complete = False
flower_timer = 0
show_flower = False
flower_grow_complete = False

# ---------- 彗星类 ----------
class Comet(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 彗星大小
        self.size = 60
        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        # 初始位置：屏幕右上角外部
        self.rect.x = SCREEN_WIDTH + 50
        self.rect.y = -100
        
        # 速度
        self.vx = -6
        self.vy = 4
        
        # 旋转角度
        self.angle = 0
        self.rotation_speed = 5  # 每帧旋转角度
        
        # 是否已经撞击
        self.has_crashed = False
        
        # ⭐ 拖尾粒子
        self.tail_particles = []
        
        # 更新彗星图像
        self.update_image()

    def update_image(self):
        """根据当前角度绘制彗星"""
        # 清空表面
        self.image.fill((0, 0, 0, 0))
        
        center_x = self.size
        center_y = self.size
        
        # ----- 彗星头部（发光的球） -----
        # 外发光
        for radius in range(30, 0, -3):
            alpha = 30 + int(40 * (radius / 30))
            color = (255, 200, 50, alpha)
            pygame.draw.circle(self.image, color, (center_x, center_y), radius)
        
        # 核心
        pygame.draw.circle(self.image, (255, 255, 220), (center_x, center_y), 20)
        pygame.draw.circle(self.image, (255, 220, 100), (center_x, center_y), 14)
        pygame.draw.circle(self.image, (255, 255, 255), (center_x, center_y), 8)
        
        # 高光
        pygame.draw.circle(self.image, (255, 255, 255, 150), (center_x - 6, center_y - 6), 5)
        
        # ----- 彗星尾巴（拖尾） -----
        # 主尾巴 - 三角形
        tail_length = 80
        tail_width_start = 25
        tail_width_end = 5
        
        # 尾巴方向：指向彗星运动方向的反方向
        # 因为彗星向右下飞，尾巴在左上方
        points = [
            (center_x, center_y),  # 尾部起点（彗星位置）
            (center_x - tail_length, center_y - tail_width_start),  # 尾巴上侧
            (center_x - tail_length - 20, center_y),  # 尾巴末端
            (center_x - tail_length, center_y + tail_width_start)  # 尾巴下侧
        ]
        
        # 主尾巴（半透明）
        pygame.draw.polygon(self.image, (255, 200, 50, 120), points)
        
        # 内层尾巴（更亮）
        inner_points = [
            (center_x - 10, center_y),
            (center_x - tail_length + 20, center_y - tail_width_start // 2),
            (center_x - tail_length, center_y),
            (center_x - tail_length + 20, center_y + tail_width_start // 2)
        ]
        pygame.draw.polygon(self.image, (255, 255, 200, 150), inner_points)
        
        # 尾巴光晕（细长发光）
        for i in range(3):
            alpha = 60 - i * 15
            offset = i * 15
            glow_points = [
                (center_x - offset, center_y),
                (center_x - tail_length - offset, center_y - tail_width_start + i * 4),
                (center_x - tail_length - 10 - offset, center_y),
                (center_x - tail_length - offset, center_y + tail_width_start - i * 4)
            ]
            pygame.draw.polygon(self.image, (255, 150, 50, alpha), glow_points)
        
        # ----- 旋转整个彗星 -----
        # 保存中心点
        center = (self.size, self.size)
        # 旋转
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        # 获取旋转后的矩形
        rotated_rect = rotated_image.get_rect(center=center)
        # 创建新表面
        new_image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        new_image.blit(rotated_image, rotated_rect.topleft)
        self.image = new_image

    def update(self):
        """更新彗星位置、旋转和拖尾"""
        if not self.has_crashed:
            # 移动
            self.rect.x += self.vx
            self.rect.y += self.vy
            
            # 旋转
            self.angle += self.rotation_speed
            if self.angle > 360:
                self.angle -= 360
            
            # 更新图像（旋转）
            self.update_image()
            
            # 生成拖尾粒子
            for _ in range(5):
                # 粒子在彗星尾部位置
                tail_x = self.rect.centerx - self.vx * 2 + random.randint(-15, 15)
                tail_y = self.rect.centery - self.vy * 2 + random.randint(-15, 15)
                self.tail_particles.append({
                    'x': tail_x,
                    'y': tail_y,
                    'life': random.randint(20, 40),
                    'max_life': 40,
                    'size': random.randint(4, 12),
                    'speed_x': random.uniform(-1, 1),
                    'speed_y': random.uniform(0.5, 2),
                    'color': random.choice([
                        (255, 200, 50),
                        (255, 150, 50),
                        (255, 100, 50),
                        (255, 200, 100)
                    ])
                })
            
            # 更新粒子
            for p in self.tail_particles[:]:
                p['life'] -= 1
                p['x'] += p['speed_x']
                p['y'] += p['speed_y']
                p['size'] *= 0.97  # 逐渐缩小
                if p['life'] <= 0 or p['size'] < 0.5:
                    self.tail_particles.remove(p)
            
            # 限制粒子数量
            if len(self.tail_particles) > 200:
                self.tail_particles = self.tail_particles[-150:]
            
            # 检测是否撞击地面
            if self.rect.bottom >= GROUND_Y:
                self.has_crashed = True
                self.rect.bottom = GROUND_Y
                return "CRASH"
        
        return None

    def draw_tail(self, screen):
        """绘制彗星拖尾"""
        for p in self.tail_particles:
            alpha = int(255 * (p['life'] / p['max_life']))
            color = (p['color'][0], p['color'][1], p['color'][2], alpha)
            size = max(1, p['size'])
            # 发光效果
            pygame.draw.circle(screen, color[:3], (int(p['x']), int(p['y'])), int(size))
            if size > 3:
                glow_color = (255, 200, 100, alpha // 3)
                pygame.draw.circle(screen, glow_color[:3], (int(p['x']), int(p['y'])), int(size * 2))

class Portal(pygame.sprite.Sprite):
    """传送门类 - 连接 Level 1 到 Level 2"""
    def __init__(self, x, y):
        super().__init__()
        self.size = 60
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.animation_timer = 0
        self.active = False
        self.update_image()
    
    def update_image(self):
        """绘制传送门（紫色发光圈）"""
        self.image.fill((0, 0, 0, 0))
        center = self.size // 2
        
        # 外圈发光
        for radius in range(28, 10, -2):
            alpha = 30 + int(50 * (radius / 28))
            color = (150, 50, 255, alpha)
            pygame.draw.circle(self.image, color, (center, center), radius)
        
        # 主圈
        pygame.draw.circle(self.image, (100, 50, 200, 180), (center, center), 24)
        pygame.draw.circle(self.image, (150, 80, 255, 200), (center, center), 18)
        pygame.draw.circle(self.image, (200, 150, 255, 220), (center, center), 10)
        
        # 内圈亮点
        pygame.draw.circle(self.image, (255, 255, 255, 150), (center - 6, center - 6), 5)
        
        # 旋转粒子效果
        self.animation_timer += 1
        angle = self.animation_timer * 0.1
        for i in range(8):
            px = center + int(20 * math.cos(angle + i * math.pi / 4))
            py = center + int(20 * math.sin(angle + i * math.pi / 4))
            alpha = 100 + int(155 * abs(math.sin(angle + i * math.pi / 4)))
            pygame.draw.circle(self.image, (200, 150, 255, alpha), (px, py), 4)
    
    def update(self):
        """更新传送门动画"""
        self.update_image()
    
    def activate(self):
        """激活传送门"""
        self.active = True
        print("🚪 传送门已激活！")

# ---------- 绘制函数 ----------
def draw_title_screen(screen):
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        t = y / SCREEN_HEIGHT
        r = int(12 + 12 * t)
        g = int(72 + 55 * t)
        b = int(44 + 8 * t)
        pygame.draw.line(background, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # Original painted forest silhouettes for the title page. This avoids reusing any
    # level owner's background asset while still matching the flora theme.
    for i in range(12):
        x = i * 145 - 80
        trunk_color = (35, 48, 24) if i % 2 else (42, 58, 30)
        pygame.draw.rect(background, trunk_color, (x + 48, 92 + (i % 3) * 18, 36, SCREEN_HEIGHT), border_radius=18)
        pygame.draw.circle(background, (12, 72, 42), (x + 70, 105), 92)
        pygame.draw.circle(background, (16, 86, 48), (x + 20, 145), 72)
        pygame.draw.circle(background, (18, 95, 55), (x + 120, 150), 78)
    for i in range(18):
        x = i * 92
        pygame.draw.polygon(
            background,
            (9, 60, 35),
            [(x - 35, 230), (x + 40, 90 + (i % 4) * 18), (x + 115, 230)],
        )
    screen.blit(background, (0, 0))

    # Dark forest-green wash so the title reads clearly over the artwork.
    wash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    wash.fill((7, 42, 25, 135))
    screen.blit(wash, (0, 0))

    # Soft radial glow behind the logo.
    glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for radius in range(360, 40, -20):
        alpha = max(0, 46 - radius // 10)
        pygame.draw.circle(glow, (142, 255, 177, alpha), (SCREEN_WIDTH // 2, 290), radius)
    screen.blit(glow, (0, 0))

    ticks = pygame.time.get_ticks()
    for i in range(26):
        x = (i * 97 + int(ticks * 0.018)) % SCREEN_WIDTH
        y = 105 + int(70 * math.sin(ticks * 0.0012 + i * 0.75)) + (i * 23) % 420
        size = 2 + (i % 3)
        alpha = 55 + int(45 * abs(math.sin(ticks * 0.002 + i)))
        pygame.draw.circle(screen, (190, 255, 188, alpha), (x, y), size)

    try:
        title_font = pygame.font.Font(None, 172)
        subtitle_font = pygame.font.Font(None, 58)
        prompt_font = pygame.font.Font(None, 42)
        small_font = pygame.font.Font(None, 28)
    except:
        title_font = pygame.font.SysFont("Georgia", 172, bold=True)
        subtitle_font = pygame.font.SysFont("Georgia", 58, bold=True)
        prompt_font = pygame.font.SysFont("Arial", 42, bold=True)
        small_font = pygame.font.SysFont("Arial", 28)

    title = "FlowerPower"
    shadow_text = title_font.render(title, True, (7, 20, 12))
    shadow_rect = shadow_text.get_rect(center=(SCREEN_WIDTH // 2 + 7, 250 + 8))
    screen.blit(shadow_text, shadow_rect)

    title_text = title_font.render(title, True, (248, 255, 232))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
    screen.blit(title_text, title_rect)

    # Thin gold underline, more polished than a flat text stack.
    underline_width = int(title_rect.width * 0.62)
    underline_y = title_rect.bottom + 4
    pygame.draw.line(
        screen,
        (255, 219, 82),
        (SCREEN_WIDTH // 2 - underline_width // 2, underline_y),
        (SCREEN_WIDTH // 2 + underline_width // 2, underline_y),
        4,
    )

    subtitle_text = subtitle_font.render("Bloom Guardian", True, (255, 225, 90))
    subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 380))
    screen.blit(subtitle_text, subtitle_rect)

    tag_text = small_font.render("A flora-themed side-scrolling adventure", True, (208, 235, 205))
    tag_rect = tag_text.get_rect(center=(SCREEN_WIDTH // 2, 426))
    screen.blit(tag_text, tag_rect)

    alpha = 128 + int(127 * abs(math.sin(pygame.time.get_ticks() / 500)))
    prompt_box = pygame.Rect(0, 0, 390, 62)
    prompt_box.center = (SCREEN_WIDTH // 2, 535)
    pygame.draw.rect(screen, (9, 45, 25), prompt_box, border_radius=18)
    pygame.draw.rect(screen, (242, 213, 93), prompt_box, 2, border_radius=18)

    prompt_text = prompt_font.render("Press ENTER to Start", True, (255, 245, 175))
    prompt_text.set_alpha(alpha)
    prompt_rect = prompt_text.get_rect(center=prompt_box.center)
    screen.blit(prompt_text, prompt_rect)

    hint_text = small_font.render("2: Level 2 Test    3: Level 3 Test    Esc: Quit", True, (174, 208, 170))
    hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 588))
    screen.blit(hint_text, hint_rect)

    # Foreground ground strip and flowers frame the screen without feeling empty.
    pygame.draw.rect(screen, (11, 62, 30), (0, SCREEN_HEIGHT - 88, SCREEN_WIDTH, 88))
    pygame.draw.rect(screen, (37, 118, 52), (0, SCREEN_HEIGHT - 96, SCREEN_WIDTH, 12))
    for x in range(0, SCREEN_WIDTH, 34):
        blade_h = 14 + (x * 7) % 28
        pygame.draw.line(screen, (62, 155, 67), (x, SCREEN_HEIGHT - 84), (x + 10, SCREEN_HEIGHT - 84 - blade_h), 3)

    flower_positions = [
        (125, SCREEN_HEIGHT - 60, (255, 208, 67), 1.1),
        (205, SCREEN_HEIGHT - 118, (255, 111, 166), 0.95),
        (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 64, (255, 208, 67), 1.1),
        (SCREEN_WIDTH - 230, SCREEN_HEIGHT - 118, (255, 111, 166), 0.95),
        (SCREEN_WIDTH // 2 - 440, SCREEN_HEIGHT - 44, (177, 233, 97), 0.75),
        (SCREEN_WIDTH // 2 + 440, SCREEN_HEIGHT - 44, (177, 233, 97), 0.75),
    ]
    for x, y, color, scale in flower_positions:
        draw_flower(screen, x, y, color, scale)


def draw_flower(screen, x, y, color, scale=1.0):
    petal = max(5, int(10 * scale))
    offset = max(7, int(12 * scale))
    center = max(4, int(8 * scale))
    pygame.draw.line(screen, (69, 150, 63), (x, y + offset + 18), (x, y + 8), max(2, int(4 * scale)))
    pygame.draw.circle(screen, color, (x, y - offset), petal)
    pygame.draw.circle(screen, color, (x + offset, y), petal)
    pygame.draw.circle(screen, color, (x, y + offset), petal)
    pygame.draw.circle(screen, color, (x - offset, y), petal)
    pygame.draw.circle(screen, (255, 246, 52), (x, y), center)


def draw_comet_scene(screen, comet, background):
    """绘制彗星坠落场景"""
    screen.blit(background, (0, 0))
    pygame.draw.rect(screen, GREEN, (0, GROUND_Y, SCREEN_WIDTH, GROUND_HEIGHT))
    pygame.draw.rect(screen, BROWN, (0, GROUND_Y, SCREEN_WIDTH, 5))
    
    # 先画拖尾粒子
    comet.draw_tail(screen)
    
    # 再画彗星本体
    screen.blit(comet.image, comet.rect)
    
    try:
        font = pygame.font.Font(None, 40)
    except:
        font = pygame.font.SysFont("Arial", 40)
    
    alpha = 128 + int(127 * abs(math.sin(pygame.time.get_ticks() / 300)))
    warning_text = font.render("⚠️ A Blight Comet is falling!", True, (255, 100, 100))
    warning_text.set_alpha(alpha)
    warning_rect = warning_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
    screen.blit(warning_text, warning_rect)


def draw_shake_effect(screen, background, comet, shake_frames):
    """绘制屏幕震动效果"""
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-10, 10)
    
    screen.blit(background, (offset_x, offset_y))
    pygame.draw.rect(screen, GREEN, (offset_x, GROUND_Y + offset_y, SCREEN_WIDTH, GROUND_HEIGHT))
    pygame.draw.rect(screen, BROWN, (offset_x, GROUND_Y + offset_y, SCREEN_WIDTH, 5))
    
    # 画拖尾和彗星
    comet.draw_tail(screen)
    screen.blit(comet.image, (comet.rect.x + offset_x, comet.rect.y + offset_y))
    
    flash_alpha = min(255, (60 - shake_frames) * 8)
    if flash_alpha > 0:
        flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        flash.fill((255, 255, 255))
        flash.set_alpha(flash_alpha // 2)
        screen.blit(flash, (0, 0))
    
    try:
        font = pygame.font.Font(None, 60)
    except:
        font = pygame.font.SysFont("Arial", 60)
    
    if shake_frames > 30:
        impact_text = font.render("💥 CRASH!", True, (255, 200, 50))
        impact_rect = impact_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(impact_text, impact_rect)

#member 3 UI, HP
def draw_ui(screen, player, score):
    """绘制UI(HP条、弹药、飞行能量、分数) - 整合了 Member 3 的任务"""
    try:
        # 使用基础英文字体，加粗使其更清晰
        font = pygame.font.SysFont("arial", 36, bold=True)
        small_font = pygame.font.SysFont("arial", 24, bold=True)
    except:
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
    
    # 提取预设颜色 (确保文件开头定义了这些常量)
    WHITE = (255, 255, 255)
    BLUE = (0, 0, 255)
    LIGHT_GREEN = (144, 238, 144)

    # ==========================================
    # 1. HP 条 (Member 3 任务)
    # ==========================================
    hp_bar_width = 300
    hp_bar_height = 25
    hp_bar_x = 20
    hp_bar_y = 20
    
    # 背景
    pygame.draw.rect(screen, (50, 50, 50), (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height))
    
    # HP 颜色（绿色 → 黄色 → 红色）
    hp_progress = player.get_hp_progress()
    if hp_progress > 0.5:
        color = (50, 205, 50)  # 绿色
    elif hp_progress > 0.25:
        color = (255, 255, 0)  # 黄色
    else:
        color = (255, 0, 0)  # 红色
    
    # 填充
    fill_width = int(hp_bar_width * hp_progress)
    pygame.draw.rect(screen, color, (hp_bar_x + 2, hp_bar_y + 2, fill_width - 4, hp_bar_height - 4))
    
    # 边框
    pygame.draw.rect(screen, WHITE, (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), 2)
    
    # HP 文字 (移除了导致乱码的 Emoji)
    hp_text = font.render(f"HP: {player.hp}/{player.max_hp}", True, WHITE)
    screen.blit(hp_text, (hp_bar_x + 10, hp_bar_y + 2))
    
    # HP 百分比（右侧）
    percent_text = small_font.render(f"{player.get_hp_percent()}%", True, WHITE)
    percent_rect = percent_text.get_rect(right=hp_bar_x + hp_bar_width - 10, centery=hp_bar_y + hp_bar_height // 2)
    screen.blit(percent_text, percent_rect)

    # ==========================================
    # 2. 分数显示 (Member 3 专属任务)
    # ==========================================
    score_text = font.render(f"Score: {score}", True, WHITE)
    score_rect = score_text.get_rect(topright=(screen.get_width() - 20, 20))
    screen.blit(score_text, score_rect)
    
    # ==========================================
    # 3. 飞行能量条（保留 Member 1 的逻辑，移除 Emoji）
    # ==========================================
    fly_bar_width = 150
    fly_bar_height = 15
    fly_bar_x = 20
    fly_bar_y = hp_bar_y + hp_bar_height + 10
    
    pygame.draw.rect(screen, (50, 50, 50), (fly_bar_x, fly_bar_y, fly_bar_width, fly_bar_height))
    
    fly_progress = player.get_fly_progress()
    if fly_progress > 0:
        fill_width = int(fly_bar_width * fly_progress)
        if fly_progress < 0.5:
            color = BLUE
        else:
            color = (255, 200, 0)
        pygame.draw.rect(screen, color, (fly_bar_x + 2, fly_bar_y + 2, fill_width - 4, fly_bar_height - 4))
    
    pygame.draw.rect(screen, WHITE, (fly_bar_x, fly_bar_y, fly_bar_width, fly_bar_height), 2)
    fly_text = small_font.render("FLY", True, WHITE)
    screen.blit(fly_text, (fly_bar_x + 5, fly_bar_y - 1))
    
    if player.is_flying:
        status_text = small_font.render("FLYING", True, (100, 200, 255))
        screen.blit(status_text, (fly_bar_x + fly_bar_width + 10, fly_bar_y - 2))
    
    # ==========================================
    # 4. 种子弹药 (移除 Emoji)
    # ==========================================
    seed_y = fly_bar_y + fly_bar_height + 15
    # 假设主文件里定义了全局变量 SEED_SHOT_MAX
    # 如果报错，可以直接改成固定的 3
    seed_text = font.render(f"Seeds: {player.seed_count}/3", True, WHITE) 
    screen.blit(seed_text, (20, seed_y))
    
    # ==========================================
    # 5. 回血状态 (移除 Emoji)
    # ==========================================
    if player.is_healing:
        heal_text = small_font.render("Healing...", True, LIGHT_GREEN)
        screen.blit(heal_text, (20, seed_y + 35))
    
    # ==========================================
    # 6. 受伤闪红边框 (保留 Member 1 逻辑)
    # ==========================================
    if player.get_hp_progress() < 0.25 and not player.is_healing:
        alpha = 50 + int(50 * abs(pygame.time.get_ticks() / 200 % 2 - 1))
        # 根据屏幕大小生成警告层
        warning = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        warning.fill((255, 0, 0, alpha))
        screen.blit(warning, (0, 0))

# member3 bgm function
def play_level_bgm(level_num):
    """根据关卡编号切换并循环播放背景音乐"""
    # 自动获取 main.py 的上一级目录 (也就是 FlowerPower 根目录)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 自动拼接绝对路径，兼容 Windows 和 Mac
    bgm_tracks = {
        1: os.path.join(base_dir, "assets", "audio", "bgm_level1.ogg"),
        2: os.path.join(base_dir, "assets", "audio", "bgm_level2.ogg"),
        3: os.path.join(base_dir, "assets", "audio", "bgm_level3.ogg"),
        4: os.path.join(base_dir, "assets", "audio", "bgm_level4.ogg")
    }
    
    if level_num in bgm_tracks:
        try:
            pygame.mixer.music.load(bgm_tracks[level_num])
            pygame.mixer.music.play(-1)  # -1 代表无限循环
        except pygame.error as e:
            print(f"BGM 加载失败，请检查路径: {e}")

def draw_tutorial_text(screen):
    """绘制教程文字（游戏开始时显示）"""
    try:
        font = pygame.font.Font(None, 32)
        small_font = pygame.font.Font(None, 24)
    except:
        font = pygame.font.SysFont("Arial", 32)
        small_font = pygame.font.SysFont("Arial", 24)
    
    # 半透明背景
    bg_width = 420
    bg_height = 280
    bg_x = SCREEN_WIDTH // 2 - bg_width // 2
    bg_y = SCREEN_HEIGHT - 300
    
    bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
    bg_surface.fill((0, 0, 0, 180))
    pygame.draw.rect(bg_surface, (255, 255, 255, 60), (0, 0, bg_width, bg_height), 2)
    screen.blit(bg_surface, (bg_x, bg_y))
    
    title_text = font.render("🎮 Controls", True, (255, 215, 0))
    screen.blit(title_text, (bg_x + 20, bg_y + 12))
    
    controls = [
        ("<-/->", "Move"),
        ("Space", "Jump"),
        ("W", "Fly"),
        ("X", "Seed Shot (Ranged)"),
        ("K", "Open Portal (Level 1)")
    ]
    
    y_offset = 52
    line_height = 28  
    for key, action in controls:
        key_text = small_font.render(key, True, (255, 200, 50))
        screen.blit(key_text, (bg_x + 20, bg_y + y_offset))
        action_text = small_font.render(f"→ {action}", True, (220, 220, 220))
        screen.blit(action_text, (bg_x + 100, bg_y + y_offset))
        y_offset += line_height
    
    alpha = 100 + int(155 * abs(math.sin(pygame.time.get_ticks() / 500)))
    hint_text = small_font.render("Press H to test damage", True, (255, 100, 100))
    hint_text.set_alpha(alpha)
    screen.blit(hint_text, (bg_x + 20, bg_y + y_offset + 5))
    
    #  按 O 键开关教程
    toggle_text = small_font.render("Press O to toggle this tutorial", True, (200, 200, 200))
    screen.blit(toggle_text, (bg_x + 20, bg_y + y_offset + 30))

def draw_game_over_screen(screen, player):
    """绘制 Game Over 画面"""
    # 半透明黑色遮罩
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(180)
    screen.blit(overlay, (0, 0))
    
    try:
        title_font = pygame.font.Font(None, 120)
        big_font = pygame.font.Font(None, 80)
        medium_font = pygame.font.Font(None, 50)
        small_font = pygame.font.Font(None, 36)
    except:
        title_font = pygame.font.SysFont("Arial", 120)
        big_font = pygame.font.SysFont("Arial", 80)
        medium_font = pygame.font.SysFont("Arial", 50)
        small_font = pygame.font.SysFont("Arial", 36)
    
    # GAME OVER 标题
    game_over_text = title_font.render("GAME OVER", True, RED)
    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
    screen.blit(game_over_text, game_over_rect)
    
    # 死亡信息
    dead_text = big_font.render("💀 You have died!", True, WHITE)
    dead_rect = dead_text.get_rect(center=(SCREEN_WIDTH // 2, 320))
    screen.blit(dead_text, dead_rect)
    
    # 最终 HP
    hp_text = medium_font.render(f"HP: {player.hp} / {player.max_hp}", True, RED)
    hp_rect = hp_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
    screen.blit(hp_text, hp_rect)
    
    # 重新开始提示（闪烁）
    alpha = 128 + int(127 * abs(math.sin(pygame.time.get_ticks() / 400)))
    restart_text = medium_font.render("Press R to Restart", True, (255, 255, 200))
    restart_text.set_alpha(alpha)
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 500))
    screen.blit(restart_text, restart_rect)
    
    # 退出提示
    quit_text = small_font.render("Press ESC to Quit", True, (128, 128, 128))
    quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, 560))
    screen.blit(quit_text, quit_rect)

def draw_flower_grow_animation(screen, timer):
    """绘制花生长动画"""
    # 半透明背景（淡入效果）
    if timer < 30:
        alpha = int(255 * (timer / 30))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 255 - alpha))
        screen.blit(overlay, (0, 0))
    
    # 花的位置（屏幕中央偏下）
    center_x = SCREEN_WIDTH // 2
    center_y = GROUND_Y - 60
    
    # 根据时间计算花的生长进度
    grow_progress = min(1.0, timer / 90)
    
    # 花的大小（从 0 逐渐长大）
    flower_scale = 0.3 + 0.7 * grow_progress
    
    # 绘制发光效果
    glow_radius = int(80 * flower_scale)
    glow_alpha = int(80 * (1 - timer / 120))
    glow = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 200, 100, glow_alpha), (glow_radius, glow_radius), glow_radius)
    screen.blit(glow, (center_x - glow_radius, center_y - glow_radius))
    
    # 绘制花
    draw_flower_big(screen, center_x, center_y, flower_scale, timer)
    
    # 绘制粒子效果（花瓣飘落）
    if timer > 30:
        for i in range(10):
            angle = timer * 0.05 + i * 2.5
            x = center_x + int(120 * math.cos(angle + i) * flower_scale)
            y = center_y - 50 + int(80 * math.sin(angle * 0.7 + i) * flower_scale) + timer * 0.5
            size = int(3 + 4 * (1 - timer / 180))
            if size > 1 and y < SCREEN_HEIGHT - 50:
                color = (255, 200, 100 + i * 10)
                pygame.draw.circle(screen, color, (x, int(y)), size)
    
    # 文字提示（闪烁）
    if timer > 60:
        alpha = 128 + int(127 * abs(math.sin(timer * 0.05)))
        try:
            font = pygame.font.Font(None, 40)
        except:
            font = pygame.font.SysFont("Arial", 40)
        text = font.render("🌸 A flower is blooming...", True, (255, 255, 200))
        text.set_alpha(alpha)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(text, text_rect)


def draw_flower_big(screen, x, y, scale, timer):
    """绘制一朵大花（用于花变玩家动画）"""
    petal_size = int(30 * scale)
    center_size = int(15 * scale)
    
    # 花茎（从地面长出）
    stem_height = int(40 * scale)
    stem_color = (50, 180, 70)
    pygame.draw.line(screen, stem_color, (x, y + stem_height), (x, y), max(3, int(4 * scale)))
    
    # 叶片（随时间展开）
    if timer > 20:
        leaf_angle = math.sin(timer * 0.03) * 0.3
        for side in [-1, 1]:
            leaf_x = x + side * int(20 * scale)
            leaf_y = y + int(20 * scale)
            pygame.draw.ellipse(
                screen,
                (60, 200, 80),
                (leaf_x - side * int(15 * scale), leaf_y - int(5 * scale), int(20 * scale), int(12 * scale))
            )
    
    # 花瓣（6片）
    colors = [
        (255, 180, 200),
        (255, 150, 180),
        (255, 200, 180),
        (255, 160, 210),
        (255, 210, 160),
        (255, 130, 190)
    ]
    
    for i in range(6):
        angle = math.radians(i * 60 + timer * 0.5)
        px = x + int(petal_size * 1.2 * math.cos(angle))
        py = y + int(petal_size * 1.2 * math.sin(angle) * 0.7)
        
        # 花瓣形状（椭圆）
        petal_rect = pygame.Rect(
            px - petal_size // 2,
            py - petal_size // 3,
            petal_size,
            int(petal_size * 0.7)
        )
        pygame.draw.ellipse(screen, colors[i % len(colors)], petal_rect)
    
    # 花蕊（发光）
    for r in range(center_size, 0, -2):
        alpha = 150 + int(50 * abs(math.sin(timer * 0.05)))
        color = (255, 215, 50 + r * 2)
        pygame.draw.circle(screen, color, (x, y), r)
    
    # 花蕊中心高光
    pygame.draw.circle(screen, (255, 255, 200), (x - 2, y - 2), int(center_size * 0.3))
    
    # 金色光晕
    glow = pygame.Surface((center_size * 4, center_size * 4), pygame.SRCALPHA)
    glow_alpha = 50 + int(30 * abs(math.sin(timer * 0.03)))
    pygame.draw.circle(glow, (255, 200, 50, glow_alpha), (center_size * 2, center_size * 2), center_size * 2)
    screen.blit(glow, (x - center_size * 2, y - center_size * 2))

def draw_level_complete_text(screen):
    """绘制关卡完成提示"""
    try:
        font = pygame.font.Font(None, 60)
        small_font = pygame.font.Font(None, 36)
    except:
        font = pygame.font.SysFont("Arial", 60)
        small_font = pygame.font.SysFont("Arial", 36)
    
    bg_width = 500
    bg_height = 150
    bg_x = SCREEN_WIDTH // 2 - bg_width // 2
    bg_y = 200
    
    bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
    bg_surface.fill((0, 0, 0, 180))
    pygame.draw.rect(bg_surface, (255, 215, 0, 80), (0, 0, bg_width, bg_height), 3)
    screen.blit(bg_surface, (bg_x, bg_y))
    
    title_text = font.render("🎉 Level 1 Complete!", True, (255, 215, 0))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 260))
    screen.blit(title_text, title_rect)
    
    hint_text = small_font.render("Walk into the portal to enter Level 2!", True, WHITE)
    hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 320))
    screen.blit(hint_text, hint_rect)    


# ---------- 主函数 ----------
def main():
    global game_state, tutorial_timer, show_tutorial, current_level, GROUND_Y, camera_locked, current_wave, enemies, level_progress
    global portal, show_portal, level1_complete, flower_timer, show_flower, flower_grow_complete
    
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("FlowerPower")
    clock = pygame.time.Clock()
    
    tutorial_timer = 0
    show_tutorial = True

    portal = None
    show_portal = False
    level1_complete = False

    flower_timer = 0
    show_flower = False
    flower_grow_complete = False
    
    background = pygame.image.load(BACKGROUND_FILE).convert()
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    
    player = None
    comet = None
    shake_frames = 0
    swamp_bg = None
    bg_x = 0

    score = 0
    current_level = 1  # [新增] 游戏默认从第一关开始
    level2_scene = Level2Scene()

    # Member 3: 实例化毒气
    enemies = pygame.sprite.Group()

    # Member 3: 初始化打击特效精灵组
    hit_effects = pygame.sprite.Group()

    # Member 3: 初始化毒气系统
    poison_gas = PoisonGasSystem(1280, 720)

    # Member 3: 初始化 Boss 相关的 UI 和警告特效
    boss_warning = BossWarningEffect(SCREEN_WIDTH, SCREEN_HEIGHT) # 如果没定义 SCREEN_WIDTH，直接写 1280, 720
    boss_ui = BossHealthBar()
    active_boss = None

    # Member 3: 初始化关卡开场字样横幅
    level_banner = LevelBanner("Level 3", 1280)

    def enter_level2(player_obj):
        global current_level, GROUND_Y, camera_locked, current_wave, level_progress
        current_level = 2
        GROUND_Y = SCREEN_HEIGHT - GROUND_HEIGHT
        camera_locked = False
        current_wave = 1
        level_progress = 0
        enemies.empty()
        level2_scene.reset(player_obj)
        play_level_bgm(2)
        print("🌲 Level 2 loaded: Dark Forest - Member 2 scene")

    def enter_level3(player_obj):
        nonlocal swamp_bg, bg_x, active_boss
        global current_level, GROUND_Y, camera_locked, current_wave, level_progress

        current_level = 3
        print("🌀 Level 3 loaded: Swamp Ruins")
        play_level_bgm(3)

        GROUND_Y = 670
        if player_obj:
            player_obj.ground_y = 670
            player_obj.rect.bottom = 670

        camera_locked = False
        current_wave = 1
        level_progress = 0
        enemies.empty()
        active_boss = None

        swamp_bg = pygame.image.load("assets/sprites/backgrounds/1_game_background.png").convert()
        swamp_bg = pygame.transform.scale(swamp_bg, (1280, 720))
        bg_x = 0
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                # 按 O 键开关教程文字
                if event.key == pygame.K_o and game_state == "PLAYING":
                    show_tutorial = not show_tutorial
                    if show_tutorial:
                        print("📖 教程文字已开启")
                        tutorial_timer = 0
                    else:
                        print("📖 教程文字已关闭")

                # Game Over 状态：按 R 重启
                if game_state == "GAME_OVER" and event.key == pygame.K_r:
                    print("🔄 重新开始游戏！")
                    game_state = "TITLE"
                    player = None
                    comet = None
                    show_tutorial = True
                    tutorial_timer = 0

                if event.key == pygame.K_h and game_state == "PLAYING":
                    if player:
                        result = player.take_damage(10)
                        if result == "GAME_OVER":
                            print("💀 玩家死亡！游戏结束！")
                            game_state = "GAME_OVER"

                # Member 2 shortcut: jump directly into Level 2 from title or gameplay.
                if event.key in (pygame.K_2, pygame.K_KP2) and game_state in ("TITLE", "PLAYING"):
                    if player is None:
                        player = Player(100, GROUND_Y - 128)
                    game_state = "PLAYING"
                    show_tutorial = False
                    tutorial_timer = 0
                    enter_level2(player)

                # Developer shortcut: jump directly into Level 3.
                if event.key in (pygame.K_3, pygame.K_KP3) and game_state in ("TITLE", "PLAYING"):
                    if player is None:
                        player = Player(100, GROUND_Y - 128)
                    game_state = "PLAYING"
                    show_tutorial = False
                    tutorial_timer = 0
                    enter_level3(player)
                
                if game_state == "TITLE" and event.key == pygame.K_RETURN:
                    print("☄️ 彗星坠落事件启动！")
                    game_state = "COMET"
                    comet = Comet()
                    player = Player(100, GROUND_Y - 128)
                    show_tutorial = True
                    tutorial_timer = 0
                
        # ----- 更新 -----
        if game_state == "COMET":
            if comet:
                result = comet.update()
                if result == "CRASH":
                    print("💥 彗星撞击地面！屏幕震动！")
                    game_state = "SHAKE"
                    shake_frames = 60
        
        elif game_state == "SHAKE":
            shake_frames -= 1
            if shake_frames <= 0:
                print("🌸 花之诞生！")
                game_state = "FLOWER"  # ⭐ 先进入花的状态
                show_flower = True
                flower_timer = 0
                flower_grow_complete = False
                play_level_bgm(1)
        
        elif game_state == "FLOWER":
            flower_timer += 1
            # 花生长动画持续 2 秒（120帧），然后变成玩家
            if flower_timer >= 120:
                flower_grow_complete = True
                game_state = "PLAYING"
                print("🌱 花变成了 Florina！")
                # 创建玩家（如果还没有）
                if player is None:
                    player = Player(SCREEN_WIDTH // 2 - 64, GROUND_Y - 128)
                # 重置花状态
                show_flower = False

        
        elif game_state == "PLAYING":
            if player:
                player.update()

                if current_level == 1:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_k] and not level1_complete:
                        level1_complete = True
                        show_portal = True
                        portal = Portal(SCREEN_WIDTH - 150, GROUND_Y - 60)
                        portal.activate()
                        print("🎯 Level 1 完成！传送门已出现！")
                    
                    if portal:
                        portal.update()
                        if portal.active and player.rect.colliderect(portal.rect):
                            print("🚪 进入 Level 2！")
                            enter_level2(player)
                            portal = None
                            show_portal = False
                            level1_complete = False

                if current_level == 2:
                    level_score, transition = level2_scene.update(player)
                    score += level_score
                    if transition == "LEVEL_COMPLETE":
                        enter_level3(player)
                
                # 背景滚动与锁屏逻辑
                if current_level == 3:
                # 假设玩家按了右键且相机没被锁住，背景向左移动
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_RIGHT] and not camera_locked:
                        bg_x -= 3  # 这里的 3 是背景滚动的速度，可以调节
                        level_progress += 3  # 记录累计行走距离

                # 【全新波次管理器】走 -> 锁屏打怪 -> 解锁 -> 走
                if current_level == 3:
                    VISUAL_GROUND = GROUND_Y - 35
                
                    # 不管锁没锁屏，只要屏幕上有怪（或者毒刺），就更新它们
                    enemies.update(player)
                
                    # 状态 A：没锁屏，玩家在跑图。到达指定距离就触发锁屏和刷怪
                    if not camera_locked:
                        if level_progress >= 800 and current_wave == 1:
                            camera_locked = True
                            print("🔒 触发警报！第 1 区域锁定！")
                            poison_gas.start_wave()  # 开启本波毒气 10 秒倒计时

                            enemies.add(ToxicSludge(player.rect.x + 200, VISUAL_GROUND))
                            enemies.add(ToxicSludge(player.rect.x + 400, VISUAL_GROUND))
                            enemies.add(ToxicSludge(player.rect.x + 600, VISUAL_GROUND))
                            enemies.add(ToxicSludge(player.rect.x - 1300, VISUAL_GROUND))
                            enemies.add(ToxicSludge(player.rect.x - 1600, VISUAL_GROUND))
                            enemies.add(ToxicSludge(player.rect.x - 1800, VISUAL_GROUND))
                        
                        elif level_progress >= 1600 and current_wave == 2:
                            camera_locked = True
                            print("🔒 触发警报！第 2 区域锁定！")
                            poison_gas.start_wave()  # 开启本波毒气 10 秒倒计时

                            enemies.add(ToxicSludge(player.rect.x + 200, VISUAL_GROUND))
                            enemies.add(ToxicSludge(player.rect.x + 400, VISUAL_GROUND))
                            enemies.add(ToxicSludge(player.rect.x - 1300, VISUAL_GROUND))
                            enemies.add(SwampMoth(player.rect.x + 300, VISUAL_GROUND - 150))
                            enemies.add(SwampMoth(player.rect.x - 1400, VISUAL_GROUND - 250))
                            enemies.add(SwampMoth(player.rect.x - 1600, VISUAL_GROUND - 350))
                        
                        elif level_progress >= 2400 and current_wave == 3:
                            camera_locked = True
                            print("🔒 触发警报！第 3 区域锁定！")
                            poison_gas.start_wave()  # 【新增】开启本波毒气 10 秒倒计时

                            enemies.add(ToxicSludge(player.rect.x + 200, VISUAL_GROUND))
                            enemies.add(ToxicSludge(player.rect.x + 400, VISUAL_GROUND))
                            enemies.add(ToxicSludge(player.rect.x - 1300, VISUAL_GROUND))
                            enemies.add(SwampMoth(player.rect.x + 300, VISUAL_GROUND - 130))
                            enemies.add(SwampMoth(player.rect.x + 500, VISUAL_GROUND - 170))
                            enemies.add(SwampMoth(player.rect.x - 1400, VISUAL_GROUND - 210))
                            enemies.add(SwampMoth(player.rect.x - 1600, VISUAL_GROUND - 250))
                            enemies.add(PoisonToad(player.rect.x + 250, VISUAL_GROUND))
                            enemies.add(PoisonToad(player.rect.x - 1450, VISUAL_GROUND))
                        
                        elif level_progress >= 3200 and current_wave == 4:
                            camera_locked = True
                            print("⚠️ 最终区域锁定! Boss HECATE 降临！")

                            # 1. 创建 Boss 并存入专属变量，方便血条系统随时读取它的血量
                            active_boss = Hecate(player.rect.x - 600, VISUAL_GROUND)
                        
                            # 2. 把 Boss 加入普通怪物组，让它能正常被打到和渲染
                            enemies.add(active_boss)
                        
                            # 3. 触发屏幕两侧爆红光特效！
                            boss_warning.trigger()
                        
                    # 状态 B：已锁屏，玩家在战斗。怪物全死光就解锁
                    else:
                        if len(enemies) == 0:
                            camera_locked = False

                            # 锁屏结束，调用毒气系统的结束方法，返还被扣掉的血量！
                            poison_gas.end_wave(player)

                            current_wave += 1
                            if current_wave > 4:
                                print("🎉 沼泽区域完全肃清！准备进入下一关！")
                            else:
                                print("🔓 区域肃清！屏幕解锁，继续前进！")
                    
                    # 关键：当第一张图完全移出左侧屏幕 (-1280) 时，重置坐标实现无限循环
                    if bg_x <= -1280:
                        bg_x = 0
                
                if show_tutorial:
                    tutorial_timer += 1
                    if tutorial_timer >= 600:
                        show_tutorial = False
                
                if player.is_dead:
                    game_state = "GAME_OVER"
        
        # ----- 渲染 -----
        if game_state == "TITLE":
            draw_title_screen(screen)
        
        elif game_state == "COMET":
            if comet:
                draw_comet_scene(screen, comet, background)
        
        elif game_state == "SHAKE":
            if comet:
                draw_shake_effect(screen, background, comet, shake_frames)

        elif game_state == "FLOWER":
            screen.blit(background, (0, 0))
            pygame.draw.rect(screen, GREEN, (0, GROUND_Y, SCREEN_WIDTH, GROUND_HEIGHT))
            draw_flower_grow_animation(screen, flower_timer)
        
        elif game_state == "PLAYING":
            screen.blit(background, (0, 0))
            pygame.draw.rect(screen, GREEN, (0, GROUND_Y, SCREEN_WIDTH, GROUND_HEIGHT))

            # Member 2: Dark Forest scene.
            if current_level == 2:
                level2_scene.draw(screen)

            # Member 3: 绘制毒沼泽
            if current_level == 3:
                # 画第一张图
                screen.blit(swamp_bg, (bg_x, 0))
                # 画第二张图，紧紧贴在第一张图的右边
                screen.blit(swamp_bg, (bg_x + 1280, 0))

                # 更新并绘制 Level 3 开场大字
                level_banner.update()
                level_banner.draw(screen)
                
                enemies.draw(screen)

                for enemy in enemies:
                    if hasattr(enemy, 'draw_health_bar'):
                        enemy.draw_health_bar(screen)

                # 更新并绘制所有的打击特效！ (建议放在怪物上面画，不要被怪物贴图挡住)
                hit_effects.update()
                hit_effects.draw(screen)
            
            if player:
                for seed in player.seed_shots:
                    seed.draw_trail(screen)
                for seed in player.seed_shots:
                    screen.blit(seed.image, seed.rect)

                # 远程种子(子弹)与怪物的碰撞检测
                for enemy in enemies:
                    # 必须用 [:] 切片来遍历，因为我们要在循环中删除击中的种子
                    for seed in player.seed_shots[:]: 
                        # 检测种子的矩形框是否碰到了怪物的矩形框
                        if seed.rect.colliderect(enemy.rect):
                    
                            # 1. 种子击中后要销毁（从列表里删掉，防止穿透打一串）
                            if seed in player.seed_shots:
                                player.seed_shots.remove(seed)
                    
                            # 2. 怪物扣血 (假设一颗种子伤害为 10)
                            enemy.hp -= 10
                            print(f"🎯 种子精准命中！敌人剩余 HP: {enemy.hp}")

                            # 检查怪物是否死亡，如果死了就加上对应的分数
                            if enemy.hp <= 0 and not getattr(enemy, 'score_given', False):
                                score += getattr(enemy, 'score_value', 0)
                                enemy.score_given = True  # 标记为已加过分，防止重复触发
                                print(f"🎯 击杀成功！获得 {enemy.score_value} 分！当前总分: {score}")

                            # 在怪物身体的中心点，生成打击闪光！
                            hit_effects.add(HitEffect(enemy.rect.centerx, enemy.rect.centery))
                    
                            # 3. 怪物死亡检测
                            if enemy.hp <= 0:
                                enemy.kill()
                                print("💀 敌人被种子击败！")
                                break # 这个怪死了，直接跳出内层循环，不再吃其他种子的伤害
                    
                #member 3
                player.draw_healing_aura(screen)

                screen.blit(player.image, player.rect)
                if player.is_attacking:
                    hitbox = player.create_attack_hitbox()

                    # 强行把红框的高度往下延伸 40 像素，变成“扫地攻击”！
                    hitbox.height += 40

                    pygame.draw.rect(screen, RED, hitbox, 2)

                    # 遍历当前关卡的所有敌人，检测是否被红框击中
                    for enemy in enemies:
                        # 使用 colliderect 检测红框和敌人的矩形是否重叠
                        if hitbox.colliderect(enemy.rect):
                            enemy.hp -= 5  # 玩家攻击力设为 5
                            print(f"💥 击中敌人！敌人剩余 HP: {enemy.hp}")
                        
                            # 如果敌人血量归零，将其从怪物组中移除
                            if enemy.hp <= 0:
                                enemy.kill()
                                print("💀 敌人被击败！")

                if current_level == 1 and show_portal and portal:
                    screen.blit(portal.image, portal.rect)
                    try:
                        font = pygame.font.Font(None, 30)
                    except:
                        font = pygame.font.SysFont("Arial", 30)
                    alpha = 128 + int(127 * abs(math.sin(pygame.time.get_ticks() / 400)))
                    portal_text = font.render("🚪 Press K to complete Level 1", True, (200, 150, 255))
                    portal_text.set_alpha(alpha)
                    text_rect = portal_text.get_rect(center=(portal.rect.centerx, portal.rect.top - 30))
                    screen.blit(portal_text, text_rect)

                # 显示 Level 1 完成提示
                if current_level == 1 and level1_complete:
                    draw_level_complete_text(screen)                

                draw_ui(screen, player, score)
                
                if show_tutorial:
                    draw_tutorial_text(screen)
        
        elif game_state == "GAME_OVER":
            screen.blit(background, (0, 0))
            pygame.draw.rect(screen, GREEN, (0, GROUND_Y, SCREEN_WIDTH, GROUND_HEIGHT))
            if player:
                screen.blit(player.image, player.rect)
            draw_game_over_screen(screen, player)
        
        # 更新并绘制全屏毒气特效
        poison_gas.update(player)
        poison_gas.draw(screen)

        # 1. 渲染红色警告特效
        boss_warning.draw(screen)
        
        # 2. 渲染 Boss 血条
        if active_boss and not active_boss.is_dead:
            boss_ui.draw(screen, active_boss)

        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
