import pygame
import os

# ---------- 路径设置 ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 主角精灵表路径
SPRITE_FILE = os.path.join(BASE_DIR, "assets", "sprites", "player", "Fairy_03_WALK_000.png")

# ⭐ 玩家图片文件夹路径（新增！）
PLAYER_FOLDER = os.path.join(BASE_DIR, "assets", "sprites", "player")

# 背景图片路径
BACKGROUND_FILE = os.path.join(BASE_DIR, "assets", "sprites", "backgrounds", "orig.png")

# 攻击图片文件夹路径
ATTACK_FOLDER = os.path.join(BASE_DIR, "assets", "sprites", "effects")

# ---------- 窗口设置 ----------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# ---------- 颜色 ----------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
GREEN = (34, 139, 34)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)      
ORANGE = (255, 165, 0)      
BLUE = (100, 150, 255)
LIGHT_GREEN = (100, 255, 100) 
DARK_RED = (180, 0, 0)   
DARK_GRAY = (40, 40, 40)   
GRAY = (128, 128, 128)              

# ---------- 地面设置 ----------
GROUND_HEIGHT = 100
GROUND_Y = SCREEN_HEIGHT - GROUND_HEIGHT

# ---------- 玩家移动设置 ----------
PLAYER_SPEED = 5
PLAYER_JUMP_POWER = -12
GRAVITY = 0.6

# 飞行设置
FLY_SPEED = -6
MAX_FLY_TIME = 180
FLY_RECHARGE_SPEED = 1

# ---------- 精灵表设置 ----------
FRAME_WIDTH = 32
FRAME_HEIGHT = 32
SPRITE_COLS = 8
SPRITE_ROWS = 10

# ---------- 攻击设置 ----------
ATTACK_COOLDOWN = 20
SEED_SHOT_MAX = 3
SEED_SHOT_RECHARGE = 120
SEED_SHOT_SPEED = 10
SEED_SHOT_DAMAGE = 15
VINE_WHIP_DAMAGE = 10
VINE_WHIP_RANGE = 80
ATTACK_DURATION = 15

#HP 系统设置
MAX_HP = 100
IDLE_HEAL_AMOUNT = 5      # 每秒回复 HP
IDLE_HEAL_DELAY = 180     # 站立 3 秒后开始回血（60fps × 3）
HURT_FLASH_DURATION = 10  # 受伤闪红帧数

# 传送门设置
PORTAL_ACTIVATE_DELAY = 60  # 传送门出现后的等待帧数