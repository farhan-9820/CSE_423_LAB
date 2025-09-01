from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_TIMES_ROMAN_24
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import sys
import random
import time
import math

frame_count = 0 
player=None
window_size_x = 1200
window_size_y = 800 
aspect_ratio = (window_size_x / window_size_y)
gun_pos=None
camera_angle = 0.0
camera_radius = 10
camera_height = 15
camera_pos = (
    camera_radius * math.cos(math.radians(camera_angle)),
    camera_radius * math.sin(math.radians(camera_angle)),
    camera_height,
)

game_state = "exploring" 
guardian = None


last_regen_time = 0
walls_to_draw = []

game_over_time = None
game_won = False 

HEAL=0
SPEED=0
DAMAGE=50
RESTORE=200
LIFE=200

BULLETS = []
game_over=False
camera_mode = 'orbit'  
GUNS=[]
fovY = 90 
keys = {}
items_manager=None

cheat_mode = False
cheat_start_time = 0
CHEAT_DURATION = 15

PLAYER_SPEED = 0.05                   #max speed = 0.6 
PLAYER_RADIUS = 0.5
PUNISHMENT_SPEED_MODIFIER = 0.5 

last_gun_regen_time = 0
last_item_regen_time = 0
freeze_end_time =0
MAZE_WIDTH = 10
MAZE_HEIGHT = 10
CELL_SIZE = 10.0  # size of a single maze cell
WALL_HEIGHT = 4.0
WALL_THICKNESS = 0.2
WALL_COLOR = (0.5, 0.5, 0.5)
SKY_COLOR = (0.3, 0.7, 1.0)
FLOOR_COLOR = (0.2, 0.2, 0.2)
START_COLOR = (0.0, 1.0, 0.0)
EXIT_COLOR = (1.0, 0.0, 0.0)


MAZE_REGEN_INTERVAL_SECONDS = 30.0
last_regen_time = 0


TRAP=[]
trap_type=[
   ("damage",(1.0, 0.6, 0.6)),
   ("Freeze",(0.6, 0.6, 1.0)),
   ("Unpick",(0.6, 1.0, 0.6))

]


ENEMIES = []
PROJECTILES = []
ENEMY_MELEE = "melee"
ENEMY_RANGED = "ranged"
ENEMY_RADIUS = 0.9
MELEE_SPEED = 0.06
RANGED_SPEED = 0.045
ENEMY_TURN_RATE = 2.0
ENEMY_VISION_FOV = 60.0
ENEMY_VISION_RANGE = 80.0
MELEE_HIT_RANGE = 2.0
MELEE_DAMAGE = 12
RANGED_DAMAGE = 2

PROJECTILE_SPEED = 0.7
PROJECTILE_BASE_RADIUS = 0.35
PROJECTILE_GROWTH_PER_UNIT = 0.02

def now():
    return glutGet(GLUT_ELAPSED_TIME) / 1000.0

def has_line_of_sight(maze, x0, y0, x1, y1, step=0.6):
    dx = x1 - x0
    dy = y1 - y0
    dist = math.hypot(dx, dy)
    if dist == 0:
        return True
    steps = int(dist / step)
    for i in range(1, steps + 1):
        px = x0 + dx * (i / steps)
        py = y0 + dy * (i / steps)
        if maze.would_collide(px, py, radius=0.08):
            return False
    return True

class Projectile:
    def __init__(self, x, y, dir_x, dir_y, kind='fire'):
        self.x = x
        self.y = y
        self.z = 1.0
        l = math.hypot(dir_x, dir_y) or 1.0
        self.dx = dir_x / l
        self.dy = dir_y / l
        self.kind = kind
        self.start_x = x
        self.start_y = y
        self.alive = True
        self.color = (1.0, 0.2, 0.1) if kind == 'fire' else (0.2, 0.6, 1.0)

    def traveled(self):
        return math.hypot(self.x - self.start_x, self.y - self.start_y)

    def radius(self):
        return PROJECTILE_BASE_RADIUS + PROJECTILE_GROWTH_PER_UNIT * self.traveled()

    def update(self, maze, player):
        if not self.alive:
            return
        nx = self.x + self.dx * PROJECTILE_SPEED
        ny = self.y + self.dy * PROJECTILE_SPEED
        # collide with walls
        if maze.would_collide(nx, ny, self.radius()):
            self.alive = False
            return
        self.x, self.y = nx, ny
        # collide with player
        if player and math.hypot(player.x - self.x, player.y - self.y) <= (player.radius + self.radius()):
            
            try:
                if self.kind == 'fire':
                    # damage + burn
                    if hasattr(player, 'apply_status'):
                        player.apply_status('burn', duration=4)
                    
                else:
                    if hasattr(player, 'apply_status'):
                        player.apply_status('freeze', duration=2)
            except Exception:
                pass
            
            if hasattr(player, 'hp'):
                player.hp = max(0, player.hp - (RANGED_DAMAGE if self.kind == 'fire' else max(1, RANGED_DAMAGE//2)))
            else:
                
                try:
                    from __main__ import LIFE
                    if self.kind == 'fire':
                        LIFE -= RANGED_DAMAGE
                    else:
                        LIFE -= max(1, RANGED_DAMAGE//2)
                except Exception:
                    pass
            self.alive = False

    def draw(self):
        if not self.alive:
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glColor3fv(self.color)
        glutSolidSphere(self.radius(), 12, 12)
        glPopMatrix()

class Enemy:
    def __init__(self, x, y, etype='melee'):
        self.x = x
        self.y = y
        self.z = 0.0
        self.rotate = random.uniform(0, 360)
        self.type = etype
        self.radius = ENEMY_RADIUS
        self.speed = MELEE_SPEED if etype == 'melee' else RANGED_SPEED
        self._next_attack_time = 0.0
        self.hp = 1   # enemy dies after 1 hit (tweakable)

    def forward(self):
        r = math.radians(self.rotate)
        return math.sin(r), math.cos(r)

    def face_towards(self, tx, ty, rate=ENEMY_TURN_RATE):
        desired = math.degrees(math.atan2(tx - self.x, ty - self.y))
        diff = (desired - self.rotate + 180) % 360 - 180
        if diff > rate: diff = rate
        if diff < -rate: diff = -rate
        self.rotate = (self.rotate + diff) % 360

    def patrol_move(self, maze):
        fx, fy = self.forward()
        nx = self.x + fx * self.speed
        ny = self.y + fy * self.speed
        moved = False
        if not maze.would_collide(nx, self.y, self.radius):
            self.x = nx
            moved = True
        else:
            self.rotate += ENEMY_TURN_RATE * 2
        if not maze.would_collide(self.x, ny, self.radius):
            self.y = ny
            moved = True
        else:
            self.rotate += ENEMY_TURN_RATE * 2
        if not moved:
            self.rotate += random.choice([-30, 30, 60, -60])

    def can_see_player(self, maze, player):
        if not player:
            return False
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > ENEMY_VISION_RANGE:
            return False
        facing = math.degrees(math.atan2(dx, dy)) % 360
        diff = abs(((facing - self.rotate + 180) % 360) - 180)
        if diff > ENEMY_VISION_FOV * 0.5:
            return False
        
        return has_line_of_sight(maze, self.x, self.y, player.x, player.y)

    def try_attack(self, maze, player):
        t = now()
        if t < self._next_attack_time: return
        if self.type == 'melee':
            if player and math.hypot(player.x - self.x, player.y - self.y) <= MELEE_HIT_RANGE:
                # melee hit -> apply status on player if function exists
                if hasattr(player, 'apply_status'):
                    # choose poison or bleed (no stacking inside apply_status)
                    if random.random() < 0.5:
                        player.apply_status('poison', duration=4.0)
                    else:
                        player.apply_status('bleed', duration=3.0)
                # fallback global damage
                try:
                    from __main__ import LIFE
                    LIFE -= MELEE_DAMAGE
                except Exception:
                    pass
                self._next_attack_time = t + 1.0
        else:
            # ranged: shoot a projectile if has LOS
            if self.can_see_player(maze, player):
                dx = player.x - self.x
                dy = player.y - self.y
                kind = 'fire' if random.random() < 0.6 else 'ice'
                PROJECTILES.append(Projectile(self.x, self.y, dx, dy, kind=kind))
                self._next_attack_time = t + 1.2

    def update(self, maze, player):
        if self.can_see_player(maze, player):
            self.face_towards(player.x, player.y)
            fx, fy = self.forward()
            step = self.speed * 0.9
            nx = self.x + fx * step
            ny = self.y + fy * step
            if not maze.would_collide(nx, self.y, self.radius): self.x = nx
            if not maze.would_collide(self.x, ny, self.radius): self.y = ny
            self.try_attack(maze, player)
        else:
            self.patrol_move(maze)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotate, 0, 0, 1)
        scale = 1.2
        if self.type == ENEMY_MELEE:
            glColor3f(0.2, 0.7, 0.2)
        else:
            glColor3f(0.9, 0.9, 0.2)
        glutSolidCube(scale)
        # head
        glPushMatrix()
        glTranslatef(0, 0, scale*0.9)
        glColor3f(0.1, 0.1, 0.1)
        glutSolidSphere(scale*0.32, 10, 10)
        glPopMatrix()
        # ranged indicator: small triangle on head
        if self.type == ENEMY_RANGED:
            glPushMatrix()
            glTranslatef(0,0,scale*1.5)
            glRotatef(-90,1,0,0)
            glColor3f(0.8,0.2,0.2)
            glutSolidCone(scale*0.18, scale*0.25, 8, 1)
            glPopMatrix()
        glPopMatrix()

# spawn helper: requires a maze instance
def random_open_pos(maze, offset=6.0):
    for _ in range(200):
        cx = random.randint(0, maze.width - 1)
        cy = random.randint(0, maze.height - 1)
        cell = maze.grid[cx][cy]
        if all(cell['walls'].values()):
            continue
        x = (cx - maze.width / 2) * (maze.width > 0 and maze.width or 1) * 0 + (cx - maze.width / 2) * 10 + 5
        
        try:
            from __main__ import CELL_SIZE, MAZE_WIDTH, MAZE_HEIGHT
            x = (cx - MAZE_WIDTH / 2) * CELL_SIZE + CELL_SIZE/2
            y = (cy - MAZE_HEIGHT / 2) * CELL_SIZE + CELL_SIZE/2
            if cell['walls']['left']:  x += offset
            if cell['walls']['right']: x -= offset
            if cell['walls']['up']:    y -= offset
            if cell['walls']['down']:  y += offset
            if not maze.would_collide(x, y, ENEMY_RADIUS):
                return x, y
        except Exception:
            # fallback simple placement
            y = (cy - maze.height / 2) * 10 + 5
            if not maze.would_collide(x, y, ENEMY_RADIUS):
                return x, y
    # fallback center
    return 0.0, 0.0

def spawn_enemies(maze, count=6):
    ENEMIES.clear()
    for i in range(count):
        etype = ENEMY_MELEE if random.random() < 0.6 else ENEMY_RANGED
        x,y = random_open_pos(maze, offset=6.0)
        ENEMIES.append(Enemy(x,y,etype))





def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)  
    glRasterPos2f(0, 0)  

    glWindowPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

class Player:
    def __init__(self, startX, startY, y=WALL_HEIGHT/2, rotate=0.0):
        self.startX = startX
        self.startY = startY
        self.x = startX
        self.y = startY  
        self.z = 0
        self.rotate = rotate
        self.game_over = False
        self.quadric = gluNewQuadric()
        self.speed_modifier = 1.0
        self.radius = 1.0
        self.gun=False
        
        self.status = None
        self.status_timer = 0.0
        self.can_move = True
        self.burn_damage = 0.0
    
    
    def take_damage(self, damage):
        global game_state
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            game_state = "game_over"  # set game_state to "game_over"
            return True
        return False
    
    def reset(self):
        self.x = self.startX
        self.y = self.startY
        self.health = 100
        self.speed_modifier = 1.0
        self.can_one_shot = True
    

    
    def update(self):
        global maze, game_state,camera_mode,cheat_mode
        if game_state == "talking":
            return
        
        self.update_status()
            # Block movement if frozen
        if not self.can_move:
                self.update_status()
                return

        speed = PLAYER_SPEED * self.speed_modifier
        rotate_speed = 1.0
        yaw_rad = math.radians(self.rotate)
        if camera_mode == "orbit":
            fwd_x = math.cos(yaw_rad)
            fwd_y = math.sin(yaw_rad)
        if camera_mode == "player":
            fwd_x = math.sin(yaw_rad)
            fwd_y = math.cos(yaw_rad)

        move_dx = 0.0
        move_dy = 0.0

        if b'w' in keys and keys[b'w']:
            move_dx += fwd_x * speed
            move_dy += fwd_y * speed
        if b's' in keys and keys[b's']:
            move_dx -= fwd_x * speed
            move_dy -= fwd_y * speed
        if camera_mode == "orbit":
            if b'd' in keys and keys[b'd']:
                self.rotate = (self.rotate - rotate_speed)
            if b'a' in keys and keys[b'a']:
                self.rotate = (self.rotate + rotate_speed)
        elif camera_mode == "player":
            if b'd' in keys and keys[b'd']:
                self.rotate = (self.rotate + rotate_speed)
            if b'a' in keys and keys[b'a']:
                self.rotate = (self.rotate - rotate_speed)

        # resolve collisions
        proposed_x = self.x + move_dx
        proposed_y = self.y + move_dy
        if cheat_mode:
            self.x=proposed_x
            self.y=proposed_y
        else:    
            if maze is not None and not maze.would_collide(proposed_x, self.y, PLAYER_RADIUS):
                self.x = proposed_x

            proposed_y = self.y + move_dy
            if maze is not None and not maze.would_collide(self.x, proposed_y, PLAYER_RADIUS):
                self.y = proposed_y

        # clamp to maze bounds
        half_maze_x = (MAZE_WIDTH * CELL_SIZE) / 2
        half_maze_y = (MAZE_HEIGHT * CELL_SIZE) / 2
        self.x = max(-half_maze_x, min(self.x, half_maze_x))
        self.y = max(-half_maze_y, min(self.y, half_maze_y))



    def draw(self):
            scale = CELL_SIZE / 5 

            glPushMatrix()
            glTranslatef(self.x, self.y, self.z)  
            glRotatef(self.rotate, 0, 0, 1)      

            # Body
            glPushMatrix()
            glTranslatef(0, 0, scale) 
            glColor3f(0, 0.5, 0)
            glutSolidCube(scale)
            glPopMatrix()

            # Head
            glPushMatrix()
            glTranslatef(0, 0, scale * 2.0)  
            glColor3f(0, 0, 0)
            gluSphere(self.quadric, scale/2.5, 10, 10)
            glPopMatrix()

            # Left leg
            glPushMatrix()
            glTranslatef(-scale/4, 0, 0)  # legs start at ground
            glColor3f(0, 0, 1)
            gluCylinder(self.quadric, scale/10, scale/10, scale/2, 10, 10)
            glPopMatrix()

            # Right leg
            glPushMatrix()
            glTranslatef(scale/4, 0, 0)
            glColor3f(0, 0, 1)
            gluCylinder(self.quadric, scale/10, scale/10, scale/2, 10, 10)
            glPopMatrix()

            hand_len = scale * 0.5        # same small length as before
            hand_radius = scale / 10.0    # keep the original thin radius

            # Left hand
            glPushMatrix()
            glTranslatef(-scale * 0.5, -hand_len * 0.5, scale)   # X: left, Y: shift back half the length so it's centered, Z: body mid
            glRotatef(-90, 1, 0, 0)                              # rotate so cylinder's +Z becomes +Y (points forward)
            glColor3f(0.2, 0.2, 0.2)
            gluCylinder(self.quadric, hand_radius, hand_radius, hand_len, 10, 2)
            glPopMatrix()

            # Right hand
            glPushMatrix()
            glTranslatef(scale * 0.5, -hand_len * 0.5, scale)    # mirror on X
            glRotatef(-90, 1, 0, 0)
            glColor3f(0.2, 0.2, 0.2)
            gluCylinder(self.quadric, hand_radius, hand_radius, hand_len, 10, 2)
            glPopMatrix()


            if self.gun:
                glPushMatrix()
                gun_length = scale * 1.5        
                gun_thickness = scale * 0.25    

                chest_z = scale * 1.2

                forward_offset = scale + gun_length * 0.5  

                glTranslatef(0.0, forward_offset, chest_z)
                glScalef(gun_thickness, gun_length, gun_thickness)

                glColor3f(0.8, 0.8, 0.1)
                glutSolidCube(1.0)
                glPopMatrix()



            glPopMatrix() 
            
    def apply_status(self, status, duration=3.0):
        """Apply a status effect. Effects don't stack (if already active, ignored)."""
        if self.status is not None:
            return
        self.status = status
        self.status_timer = float(duration)
        if status == "freeze":
            self.can_move = False
        elif status == "burn":
            self.burn_damage = 2.0

    def update_status(self):
        """Tick status effects each frame. Uses global LIFE to keep consistent with other code."""
        global LIFE
        if self.status_timer > 0.0:
            # reduce timer (assume ~60 FPS)
            self.status_timer -= 1.0 / 60.0
            if self.status == "burn":
                LIFE -= self.burn_damage * 0.1
            elif self.status == "poison":
                LIFE -= 0.05
            elif self.status == "bleed":
                LIFE -= 0.1

            # clamp life
            if LIFE < 0:
                LIFE = 0
        else:
            # effect ended
            if self.status == "freeze":
                self.can_move = True
            self.status = None
            self.status_timer = 0.0


class Guardian:
    """The guardian at the maze's end, handling the quiz."""
    def __init__(self, x, y, z=WALL_HEIGHT/2):
        self.x = x
        self.y = y
        self.z = z
        self.is_active = True
        self.conversation_active = False
        self.rotate = 0.0
        self.health = 100
        self.is_chasing = False
        self.questions = [
            {"q": "Is the sky blue? (y/n)", "a": b"y"},
            {"q": "Is the Earth flat? (y/n)", "a": b"n"},
            {"q": "Is this a difficult maze? (y/n)", "a": b"y"},
            {"q": "Do you lie in real life? (y/n)", "a": b"y"},
            {"q": "Does the moon revolve around the earth? (y/n)", "a": b"y"},
            {"q": "Do you think you can escape this maze? (y/n)", "a": b"y"}
        ]
        self.current_question_index = 0
        self.chase_speed = 0.1
        self.radius = 2.0

    def update(self):
        if not self.is_chasing:
            return

        # Chase the player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            self.x += (dx / dist) * self.chase_speed
            self.y += (dy / dist) * self.chase_speed

    def check_collision_with_player(self):
        distance = math.sqrt((self.x - player.x)**2 + (self.y - player.y)**2)
        if distance < self.radius + PLAYER_RADIUS:
            return True
        return False

    def can_see_player(self):
        return maze.check_line_of_sight(self.x, self.y, player.x, player.y)

    def draw(self):
        if not self.is_active:
            return

        scale = CELL_SIZE / 3
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(guardian.rotate, 0, 0, 1)

        # Body
        glPushMatrix()
        glTranslatef(0, 0, scale)
        glColor3f(0, 0.5, 0)
        glutSolidCube(scale)
        glPopMatrix()

        # Head
        glPushMatrix()
        glTranslatef(0, 0, scale * 2.0)
        glColor3f(0, 0, 0)
        gluSphere(gluNewQuadric(), scale / 2.5, 10, 10)
        glPopMatrix()


        # Sphere at the end of the leg
        glColor3f(0.8, 1, 0.8)
        glPushMatrix()
        glTranslatef(-2, 0, 0)
        glutSolidSphere(1.5, 20, 20) # Draw a sphere for the foot
        glPopMatrix()
        
                
        # Left hand
        glPushMatrix()
        glTranslatef(0, -scale / 2, scale) # Position at the side of the body
        glRotatef(90, 0, 1, 0)             # Point outwards along the Y-axis
        glColor3f(0.2, 0.2, 0.2)
        gluCylinder(gluNewQuadric(), scale / 10, scale / 10, scale* 1.3, 10, 10)                     #argNames=('quad', 'base', 'top', 'height', 'slices', 'stacks')
        glPopMatrix()

        # Right hand
        glPushMatrix()
        glTranslatef(0, scale / 2, scale) # Position at the side of the body
        glRotatef(90, 0, 1, 0)             # Point outwards along the Y-axis
        glColor3f(0.2, 0.2, 0.2)
        gluCylinder(gluNewQuadric(), scale / 10, scale / 10, scale * 1.3, 10, 10)
        glPopMatrix()

        glPopMatrix()

        if self.conversation_active:
            question = self.questions[self.current_question_index]["q"]
            draw_3d_text(question, self.x, self.y, self.z + 7)

def draw_3d_text(text, x, y, z):
    """Renders 3D text using GLUT strokes."""
    glRasterPos3f(x, y, z)
    glColor3f(1, 1, 1) # White text
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))


def regen_guns(value=0):
    global GUNS, maze,last_gun_regen_time
    now = time.time()
    force=False
    if force or (now - last_gun_regen_time >= 30.0):
        GUNS.clear()
        for i in range(4):
            gun_pos = generate_gun(maze, offset=15)
            GUNS.append({'pos': gun_pos, 'picked': False})
        last_gun_regen_time = now


def generate_gun(maze, offset=15):
    while True:
        cx = random.randint(0, MAZE_WIDTH - 1)
        cy = random.randint(0, MAZE_HEIGHT - 1)
        cell = maze.grid[cx][cy]

        if all(cell['walls'].values()):
            continue

        cell_center_x = (cx - MAZE_WIDTH / 2) * CELL_SIZE + CELL_SIZE / 2
        cell_center_y = (cy - MAZE_HEIGHT / 2) * CELL_SIZE + CELL_SIZE / 2

        if cell['walls']['left']:
            cell_center_x += offset
        if cell['walls']['right']:
            cell_center_x -= offset
        if cell['walls']['up']:
            cell_center_y -= offset
        if cell['walls']['down']:
            cell_center_y += offset

        half_maze_x = (MAZE_WIDTH * CELL_SIZE) / 2 - offset
        half_maze_y = (MAZE_HEIGHT * CELL_SIZE) / 2 - offset
        cell_center_x = max(-half_maze_x, min(cell_center_x, half_maze_x))
        cell_center_y = max(-half_maze_y, min(cell_center_y, half_maze_y))

        return (cell_center_x, cell_center_y)


def spawn_traps(maze,trap):
    offset=2.0
    while True:
        cx = random.randint(0, MAZE_WIDTH - 1)
        cy = random.randint(0, MAZE_HEIGHT - 1)
        cell = maze.grid[cx][cy]

        if all(cell['walls'].values()):
            continue

    
        cell_center_x = (cx - MAZE_WIDTH / 2) * CELL_SIZE + CELL_SIZE / 2
        cell_center_y = (cy - MAZE_HEIGHT / 2) * CELL_SIZE + CELL_SIZE / 2


        if cell['walls']['left'] == False:
            cell_center_x -= offset
        if cell['walls']['right'] == False:
            cell_center_x += offset
        if cell['walls']['up'] == False:
            cell_center_y += offset
        if cell['walls']['down'] == False:
            cell_center_y -= offset

        half_cell = CELL_SIZE / 2
        cell_center_x = max((cx - MAZE_WIDTH/2) * CELL_SIZE + 1, min(cell_center_x, (cx - MAZE_WIDTH/2) * CELL_SIZE + CELL_SIZE - 1))
        cell_center_y = max((cy - MAZE_HEIGHT/2) * CELL_SIZE + 1, min(cell_center_y, (cy - MAZE_HEIGHT/2) * CELL_SIZE + CELL_SIZE - 1))

        return {
            "pos": (cell_center_x, cell_center_y),
            "type": trap[0],
            "color": trap[1],
            "active": True
        }
def draw_traps():
    global TRAP
    for trap in TRAP:
        if trap["active"]==False:
            continue
        else:
            x,y=trap["pos"]
            z = 0.05     
            glPushMatrix()
            glTranslatef(x, y, z)
            glColor3fv(trap["color"])
            
            radius = CELL_SIZE * 0.3
            slices = 16  
            stacks = 16  
            gluSphere(gluNewQuadric(), radius, slices, stacks)

        glPopMatrix()

def draw_guns():
    for gun in GUNS:
        if gun['picked']:
            continue  

        x, y =gun["pos"]
        z = 0.5 

        glPushMatrix()
        glTranslatef(x, y, z)

        # --- Gun Body ---
        glPushMatrix()
        glColor3f(0.8, 0.8, 0.1)  
        glScalef(4.0, 1.0, 1.0)   
        glutSolidCube(1.0)
        glPopMatrix()

        # --- Barrel ---
        glPushMatrix()
        glTranslatef(4.0, 0.0, 0.0) 
        glColor3f(0.2, 0.2, 0.2)     
        glScalef(2.5, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()

        
        glPushMatrix()
        glTranslatef(-1.0, 0.0, -1.0) 
        glColor3f(0.4, 0.2, 0.0)      
        glScalef(0.5, 0.5, 2.0)       
        glutSolidCube(1.0)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(1.5, 0.0, 1.0)
        glColor3f(0.1, 0.1, 0.1)
        glScalef(0.5, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()

        glPopMatrix()

def create_bullets():
    global BULLETS
    scale = CELL_SIZE / 5
    gun_length = scale * 1.5      
    chest_z = scale * 1.2         

    rd = math.radians(player.rotate)
    dx = math.sin(rd)
    dy = math.cos(rd)
    
    
    forward_offset = scale + gun_length  
    d_x = player.x + dx * forward_offset
    d_y = player.y + dy * forward_offset
    d_z = player.z + chest_z

    BULLETS.append([[d_x, d_y, d_z], [dx, dy], True])



def draw_bullet():
    global game_over
    if game_over==False:
        for bullet in BULLETS:
            if not bullet[2]:
              continue
            x, y, z = bullet[0]
            glPushMatrix()
            glTranslatef(x, y, z)
            glColor3f(1.0, 0.5, 0.0)
            glutSolidCube(0.1) 
            glPopMatrix()
            
            
def update_bullets():
    global BULLETS, maze
    speed = 0.5
    for bullet in BULLETS:
        if not bullet[2]:
            continue
        bullet[0][0] += bullet[1][0] * speed
        bullet[0][1] += bullet[1][1] * speed

        x, y, _ = bullet[0]
        if maze.would_collide(x, y, 0.2):
            bullet[2] = False



class Items:
    def __init__(self, maze, regen_interval=15, offset=15):
        self.maze = maze
        self.regen_interval = regen_interval   # seconds instead of ms
        self.offset = offset
        self.items = []
        self.item_types = ["heal", "damage", "speed", "restore"]
        self.last_regen_time = time.time()     
        self.generate_items()

    def generate_item_at_random_cell(self, item_type):
        while True:
            cx = random.randint(0, self.maze.width - 1)
            cy = random.randint(0, self.maze.height - 1)
            cell = self.maze.grid[cx][cy]

            if all(cell['walls'].values()):
                continue  

            cell_center_x = (cx - self.maze.width / 2) * CELL_SIZE + CELL_SIZE / 2
            cell_center_y = (cy - self.maze.height / 2) * CELL_SIZE + CELL_SIZE / 2

            if cell['walls']['left']:
                cell_center_x += self.offset
            if cell['walls']['right']:
                cell_center_x -= self.offset
            if cell['walls']['up']:
                cell_center_y -= self.offset
            if cell['walls']['down']:
                cell_center_y += self.offset

            half_maze_x = (self.maze.width * CELL_SIZE) / 2 - self.offset
            half_maze_y = (self.maze.height * CELL_SIZE) / 2 - self.offset
            cell_center_x = max(-half_maze_x, min(cell_center_x, half_maze_x))
            cell_center_y = max(-half_maze_y, min(cell_center_y, half_maze_y))

            color = {
                "heal": (0.0, 1.0, 0.0),
                "damage": (1.0, 0.0, 0.0),
                "speed": (0.0, 0.0, 1.0),
                "restore": (1.0, 1.0, 0.0)
            }[item_type]

            return {
                "pos": (cell_center_x, cell_center_y),
                "type": item_type,
                "color": color,
                "picked": False,
                "float_offset": 0.0
            }

    def generate_items(self):
        self.items.clear()
        for item_type in self.item_types:
            for i in range(2):
                self.items.append(self.generate_item_at_random_cell(item_type))

    def update(self):
        for item in self.items:
            item['float_offset'] = math.sin(glutGet(GLUT_ELAPSED_TIME) * 0.003) * 0.2

        now = time.time()
        if now - self.last_regen_time >= self.regen_interval:
            self.generate_items()
            self.last_regen_time = now

    def draw(self):
        for item in self.items:
            if item['picked']:
                continue
            x, y = item['pos']
            z = 0.5 + item['float_offset']
            glPushMatrix()
            glTranslatef(x, y, z)
            glColor3fv(item['color'])
            glutSolidCube(1)
            glPopMatrix()



class Maze:
    """Handles the logical generation of the maze and provides rendering data."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = []
        self.regen_time = 0

    def generate(self):
        self.grid = [[{'walls': {'up': True, 'down': True, 'left': True, 'right': True}, 'visited': False}
                      for _ in range(self.height)] for _ in range(self.width)]
        stack = []
        start_cell = (0, 0)
        self.grid[start_cell[0]][start_cell[1]]['visited'] = True
        stack.append(start_cell)

        while stack:
            current_x, current_y = stack[-1]
            neighbors = []
            if current_y > 0 and not self.grid[current_x][current_y - 1]['visited']:
                neighbors.append((current_x, current_y - 1, 'up'))
            if current_y < self.height - 1 and not self.grid[current_x][current_y + 1]['visited']:
                neighbors.append((current_x, current_y + 1, 'down'))
            if current_x > 0 and not self.grid[current_x - 1][current_y]['visited']:
                neighbors.append((current_x - 1, current_y, 'left'))
            if current_x < self.width - 1 and not self.grid[current_x + 1][current_y]['visited']:
                neighbors.append((current_x + 1, current_y, 'right'))

            if neighbors:
                next_x, next_y, direction = random.choice(neighbors)
                if direction == 'up':
                    self.grid[current_x][current_y]['walls']['down'] = False
                    self.grid[next_x][next_y]['walls']['up'] = False
                elif direction == 'down':
                    self.grid[current_x][current_y]['walls']['up'] = False
                    self.grid[next_x][next_y]['walls']['down'] = False
                elif direction == 'left':
                    self.grid[current_x][current_y]['walls']['left'] = False
                    self.grid[next_x][next_y]['walls']['right'] = False
                elif direction == 'right':
                    self.grid[current_x][current_y]['walls']['right'] = False
                    self.grid[next_x][next_y]['walls']['left'] = False
                
                self.grid[next_x][next_y]['visited'] = True
                stack.append((next_x, next_y))
            else:
                stack.pop()

        self.grid[0][0]['walls']['left'] = False
        self.grid[self.width - 1][self.height - 1]['walls']['right'] = False

    def get_walls_vertices(self):
        walls = []
        for x in range(self.width):
            for y in range(self.height):
                cell = self.grid[x][y]
                cx = (x - self.width / 2) * CELL_SIZE
                cy = (y - self.height / 2) * CELL_SIZE
                cz = 0
                if cell['walls']['up']:
                    walls.extend([
                        (cx - CELL_SIZE / 2, cy + CELL_SIZE / 2, cz),
                        (cx + CELL_SIZE / 2, cy + CELL_SIZE / 2, cz),
                        (cx + CELL_SIZE / 2, cy + CELL_SIZE / 2, cz + WALL_HEIGHT),
                        (cx - CELL_SIZE / 2, cy + CELL_SIZE / 2, cz + WALL_HEIGHT),
                    ])
                if cell['walls']['down']:
                    walls.extend([
                        (cx + CELL_SIZE / 2, cy - CELL_SIZE / 2, cz),
                        (cx - CELL_SIZE / 2, cy - CELL_SIZE / 2, cz),
                        (cx - CELL_SIZE / 2, cy - CELL_SIZE / 2, cz + WALL_HEIGHT),
                        (cx + CELL_SIZE / 2, cy - CELL_SIZE / 2, cz + WALL_HEIGHT),
                    ])
                if cell['walls']['left']:
                    walls.extend([
                        (cx - CELL_SIZE / 2, cy - CELL_SIZE / 2, cz),
                        (cx - CELL_SIZE / 2, cy + CELL_SIZE / 2, cz),
                        (cx - CELL_SIZE / 2, cy + CELL_SIZE / 2, cz + WALL_HEIGHT),
                        (cx - CELL_SIZE / 2, cy - CELL_SIZE / 2, cz + WALL_HEIGHT),
                    ])
                if cell['walls']['right']:
                    walls.extend([
                        (cx + CELL_SIZE / 2, cy + CELL_SIZE / 2, cz),
                        (cx + CELL_SIZE / 2, cy - CELL_SIZE / 2, cz),
                        (cx + CELL_SIZE / 2, cy - CELL_SIZE / 2, cz + WALL_HEIGHT),
                        (cx + CELL_SIZE / 2, cy + CELL_SIZE / 2, cz + WALL_HEIGHT),
                    ])
        return walls

    def would_collide(self, x, y, radius):
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                fx = (x / CELL_SIZE) + (self.width / 2)
                fy = (y / CELL_SIZE) + (self.height / 2)
                cell_x = int(math.floor(fx)) + dx
                cell_y = int(math.floor(fy)) + dy
                cell_x = max(0, min(self.width - 1, cell_x))
                cell_y = max(0, min(self.height - 1, cell_y))
                cell = self.grid[cell_x][cell_y]
                center_x = (cell_x - self.width / 2) * CELL_SIZE
                center_y = (cell_y - self.height / 2) * CELL_SIZE
                dx_local = x - center_x
                dy_local = y - center_y
                half = CELL_SIZE / 2.0
                pad = radius + (WALL_THICKNESS / 2.0)
                if cell['walls']['right']:
                    dist = (center_x + half) - x
                    if 0 <= dist <= pad and abs(dy_local) <= half:
                        return True
                if cell['walls']['left']:
                    dist = x - (center_x - half)
                    if 0 <= dist <= pad and abs(dy_local) <= half:
                        return True
                if cell['walls']['up']:
                    dist = (center_y + half) - y
                    if 0 <= dist <= pad and abs(dx_local) <= half:
                        return True
                if cell['walls']['down']:
                    dist = y - (center_y - half)
                    if 0 <= dist <= pad and abs(dx_local) <= half:
                        return True
        return False

    def check_line_of_sight(self, start_x, start_y, end_x, end_y):
        """Checks if there's a clear path between two points."""
        num_steps = 100
        for i in range(num_steps + 1):
            t = i / float(num_steps)
            check_x = start_x + (end_x - start_x) * t
            check_y = start_y + (end_y - start_y) * t
            if self.would_collide(check_x, check_y, 0.5):
                return False
        return True
    

def draw_floor():
    """Renders the ground plane of the maze."""
    glPushMatrix()
    glColor3fv(FLOOR_COLOR)
    glBegin(GL_QUADS)
    
    size_x = MAZE_WIDTH * CELL_SIZE
    size_z = MAZE_HEIGHT * CELL_SIZE
    
    
    glVertex3f(-size_x / 2 - CELL_SIZE/2, -size_z / 2 - CELL_SIZE/2, 0)
    glVertex3f(size_x / 2 - CELL_SIZE/2, -size_z / 2 - CELL_SIZE/2, 0)
    glVertex3f(size_x / 2 - CELL_SIZE/2, size_z / 2 - CELL_SIZE/2, 0)
    glVertex3f(-size_x / 2 - CELL_SIZE/2, size_z / 2 - CELL_SIZE/2, 0)
    
    
    glEnd()
    glPopMatrix()


def draw_walls(vertices):
    """Render walls aligned with z-axis height."""
    glPushMatrix()
    glColor3fv(WALL_COLOR)
    glBegin(GL_QUADS)
    for i in range(0, len(vertices), 4):
        
        glVertex3fv(vertices[i])
        glVertex3fv(vertices[i+1])
        glVertex3fv(vertices[i+2])
        glVertex3fv(vertices[i+3])
        
        
        
        # for i in range(0, len(vertices), 4):
        # # Get the vertices for the quad
        # x1, y1, z1 = vertices[i]
        # x2, y2, z2 = vertices[i+1]
        # x3, y3, z3 = vertices[i+2]
        # x4, y4, z4 = vertices[i+3]

        # # Draw the quad using glVertex3f
        # glVertex3f(x1, y1, z1)
        # glVertex3f(x2, y2, z2)
        # glVertex3f(x3, y3, z3)
        # glVertex3f(x4, y4, z4)
        
    glEnd()
    glPopMatrix()
    
    
def keyboardListener(key, x, y):
    global keys, game_state, guardian, player,cheat_mode, cheat_start_time
    keys[key.lower() if isinstance(key, bytes) else key.lower().encode()] = True
    if key.lower() == b'c':
        cheat_mode = True
        cheat_start_time = time.time()
        print("Cheat mode activated! You can pass through walls for 15 seconds.")
    
    if game_state == "talking":
        if key.lower() == b'y':
            handle_answer(b'y')
        elif key.lower() == b'n':
            handle_answer(b'n')
    elif key.lower() == b'i':
        end_x = (MAZE_WIDTH / 2) * CELL_SIZE - CELL_SIZE
        end_y = (MAZE_HEIGHT / 2) * CELL_SIZE - CELL_SIZE
        distance_to_guardian = math.sqrt((player.x - end_x)**2 + (player.y - end_y)**2)
        if distance_to_guardian < 5.0 and game_state == "exploring":
            print("Interaction initiated. Answering questions.")
            game_state = "talking"
            guardian.conversation_active = True
    elif key.lower() == b'f' and game_state == "punishment":
        if player.can_one_shot and player.health > 0 and guardian.is_active:
            if maze.check_line_of_sight(player.x, player.y, guardian.x, guardian.y):
                print("You got a clear shot! Guardian defeated.")
                guardian.is_active = False
                game_state = "finished"

    elif key.lower() == b'\x1b':
        glutLeaveMainLoop()
    
    
    keys[key.decode('ascii').lower()] = True
     
    if key == b'r' and game_state == "game_over":
        restart_game()

def keyboardUpListener(key, x, y):
    global keys
    keys[key.lower() if isinstance(key, bytes) else key.lower().encode()] = False

    if key == b'b' and player.gun:
        create_bullets()



def handle_answer(answer):
    global guardian, game_state, player
    
    if guardian.current_question_index < len(guardian.questions):
        correct_answer = guardian.questions[guardian.current_question_index]["a"]
        if answer == correct_answer:
            print("Correct!")
            guardian.current_question_index += 1
            if guardian.current_question_index >= len(guardian.questions):
                print("All questions answered correctly! The Guardian vanishes.")
                guardian.is_active = False
                game_state = "finished"
                guardian.conversation_active = False
        else:
            print("Incorrect! The guardian punishes you.")
            punish_player_and_reset()

def punish_player_and_reset():
    global maze, player, game_state, guardian
    
    player.reset()
    player.speed_modifier = PUNISHMENT_SPEED_MODIFIER
    player.can_one_shot = False
    
    # Reset guardian state and begin chasing
    guardian.is_chasing = True
    guardian.x = (MAZE_WIDTH / 2) * CELL_SIZE - CELL_SIZE
    guardian.y = (MAZE_HEIGHT / 2) * CELL_SIZE - CELL_SIZE
    guardian.conversation_active = False
    
    print(f"you have been hit with penalty! Your speed is now {player.speed_modifier * 100}% and you cannot one-shot.")
    game_state = "punishment"



def draw_start_exit_points():
    """Renders the starting and exit squares on the floor."""
    glPushMatrix()

    # Draw the start point
    start_x = (-MAZE_WIDTH / 2) * CELL_SIZE + CELL_SIZE
    start_y = (-MAZE_HEIGHT / 2) * CELL_SIZE + CELL_SIZE
    glColor3fv(START_COLOR)
    glBegin(GL_QUADS)
    glVertex3f(start_x - CELL_SIZE/2, start_y - CELL_SIZE/2, 0.1)
    glVertex3f(start_x + CELL_SIZE/2, start_y - CELL_SIZE/2, 0.1)
    glVertex3f(start_x + CELL_SIZE/2, start_y + CELL_SIZE/2, 0.1)
    glVertex3f(start_x - CELL_SIZE/2, start_y + CELL_SIZE/2, 0.1)
    glEnd()

    # Draw the exit point
    exit_x = (MAZE_WIDTH / 2) * CELL_SIZE - CELL_SIZE
    exit_z = (MAZE_HEIGHT / 2) * CELL_SIZE - CELL_SIZE
    glColor3fv(EXIT_COLOR)
    glBegin(GL_QUADS)
    glVertex3f(exit_x - CELL_SIZE/2,  exit_z - CELL_SIZE/2, 0.1)
    glVertex3f(exit_x + CELL_SIZE/2,  exit_z - CELL_SIZE/2, 0.1)
    glVertex3f(exit_x + CELL_SIZE/2,  exit_z + CELL_SIZE/2, 0.1)
    glVertex3f(exit_x - CELL_SIZE/2,  exit_z + CELL_SIZE/2, 0.1)
    glEnd()
    
    glPopMatrix()

def setupCamera():
    global fovY, aspect_ratio, camera_pos, camera_mode, player
    glMatrixMode(GL_PROJECTION)  
    glLoadIdentity()  
    gluPerspective(fovY, aspect_ratio, 0.1, 5500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if camera_mode == 'player' and player is not None:
        scale = CELL_SIZE / 5
        head_height = player.z + (scale * 2.0) 
        yaw_rad = math.radians(player.rotate)
        look_dir_x = math.sin(yaw_rad)
        look_dir_y = math.cos(yaw_rad)
        eye_x = player.x -4
        eye_y = player.y
        eye_z = head_height + 5
        look_at_offset = 100
        center_x = eye_x + look_dir_x * look_at_offset
        center_y = eye_y + look_dir_y * look_at_offset
        center_z = eye_z 
        gluLookAt(eye_x, eye_y, eye_z,
                  center_x, center_y, center_z,
                  0, 0, 1)
    else:
        x, y, z = camera_pos
        gluLookAt(x, y, z,   # Camera position
                  0, 0, 0,   # Look-at target
                  0, 0, 1)   # Up vector (z-axis)


def specialKeyListener(key, x, y):                  
    global camera_angle, camera_pos, camera_radius, camera_height
    angle_increment = 3.0
    height_step = 5.0
    min_height = 10.0
    max_height = 100.0

    # orbit left/right
    if key == GLUT_KEY_LEFT:
        camera_angle = (camera_angle + angle_increment)
    if key == GLUT_KEY_RIGHT:
        camera_angle = (camera_angle - angle_increment)

    if key == GLUT_KEY_UP:
        camera_height = min(max_height, camera_height + height_step)
    if key == GLUT_KEY_DOWN:
        camera_height = max(min_height, camera_height - height_step)

    angle_rad = math.radians(camera_angle)
    new_x = camera_radius * math.cos(angle_rad)
    new_y = camera_radius * math.sin(angle_rad)
    new_z = camera_height

    camera_pos = (new_x, new_y, new_z)
    glutPostRedisplay()


def mouseListener(button, state, x, y):
    global camera_mode
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = 'player' if camera_mode == 'orbit' else 'orbit'
        glutPostRedisplay()


def restart_game():
    global maze, walls_to_draw, last_regen_time, player, GUNS, TRAP, BULLETS, game_state, guardian
    
    # reset game state
    game_state = "exploring"

    # reset player
    player.reset()
    
    # regenerate the maze
    maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)
    maze.generate()
    walls_to_draw = maze.get_walls_vertices()
    
    # clear the players starting cell from walls
    px = int((player.x / CELL_SIZE) + (MAZE_WIDTH / 2))
    py = int((player.y / CELL_SIZE) + (MAZE_HEIGHT / 2))
    if 0 <= px < MAZE_WIDTH and 0 <= py < MAZE_HEIGHT:
        maze.grid[px][py]['walls'] = {'up': False, 'down': False, 'left': False, 'right': False}

    # reset the guardian to its original spawn point
    exit_x = (MAZE_WIDTH / 2) * CELL_SIZE - CELL_SIZE
    exit_y = (MAZE_HEIGHT / 2) * CELL_SIZE - CELL_SIZE
    guardian = Guardian(exit_x, exit_y, 0)
    
    # clear and respawn other game elements
    GUNS.clear()
    TRAP.clear()
    BULLETS.clear()

    #revert the game elem to og 
    for i in range(4):
        gun_pos = generate_gun(maze)
        GUNS.append({'pos': (gun_pos), 'picked': False})
    
    for trap in trap_type:
        for i in range(3):
            TRAP.append(spawn_traps(maze, trap))
            
    last_regen_time = time.time()
    


def showScreen():
    global window_size_x, window_size_y, walls_to_draw, maze,items_manager, guardian, game_state
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, window_size_x, window_size_y)

    setupCamera()
    draw_floor()
    draw_traps() 
    draw_start_exit_points()
    draw_walls(walls_to_draw)
    draw_guns()
    draw_bullet()
    glColor3f(1, 1, 1)
    draw_text(10, 770, f"LIFE: {LIFE}")
    draw_text(10, 740, f"SPEED: {PLAYER_SPEED:.2f}")
    draw_text(10, 710, f"DAMAGE: {DAMAGE}")
    items_manager.draw()
    
    for e in ENEMIES:
        e.draw()
    # draw projectiles
    for p in PROJECTILES:
        p.draw()
        
    player.draw()
    guardian.draw()
    
    if game_state == "exploring":
        end_x = (MAZE_WIDTH / 2) * CELL_SIZE - CELL_SIZE
        end_y = (MAZE_HEIGHT / 2) * CELL_SIZE - CELL_SIZE
        distance_to_guardian = math.sqrt((player.x - end_x)**2 + (player.y - end_y)**2)
        if distance_to_guardian < 5.0:
            draw_3d_text("Press 'I' to talk to the guardian.", end_x, end_y, WALL_HEIGHT + 2)
            
    
    if game_state == "finished":
        draw_3d_text("Congratulations! You have finished the maze.", player.x, player.y, player.z + 5)
    elif game_state == "punishment":
        draw_3d_text("Escape the guardian!", player.x, player.y, player.z + 5)
    elif game_state == "game_over":
        draw_3d_text("Game Over!", player.x, player.y, player.z + 5)
    
    
    glutSwapBuffers()


def idle_func():
    global last_regen_time, walls_to_draw,player,items_manager,PLAYER_SPEED,DAMAGE,LIFE,RESTORE,game_over,freeze_end_time, guardian,game_state ,cheat_start_time,cheat_mode, game_won, game_over_time
    
    player.update()
    items_manager.update() 
    update_bullets() 
    #---------------------sakib
    #  Bullet vs Enemy collision
    for bullet in BULLETS[:]:
        if not bullet[2]:
            continue
        bx, by, bz = bullet[0]
        for enemy in ENEMIES[:]:
            dist = math.hypot(bx - enemy.x, by - enemy.y)
            if dist <= (0.5 + enemy.radius):  # 0.5 ~ bullet size
                enemy.hp -= 1
                if enemy.hp <= 0:
                    ENEMIES.remove(enemy)
                bullet[2] = False  # deactivate bullet
                break
    # update enemies
    for e in ENEMIES:
        e.update(maze, player)
    # update projectiles
    for p in PROJECTILES:
        p.update(maze, player)
    # remove dead projectiles
    PROJECTILES[:] = [p for p in PROJECTILES if p.alive]
    
    
    
    

    
    exit_x = (MAZE_WIDTH / 2) * CELL_SIZE - CELL_SIZE
    exit_y = (MAZE_HEIGHT / 2) * CELL_SIZE - CELL_SIZE
    if not game_won:
        distance_to_exit = math.sqrt((player.x - exit_x)**2 + (player.y - exit_y)**2)
        if distance_to_exit < PLAYER_RADIUS + 2:  
            game_won = True
            game_state = "game_won"
            game_over_time = time.time()
            print("You have completed the game!")

    # If the game is won, check the delay
    if game_won:
        if time.time() - game_over_time >= 5:
            glutLeaveMainLoop()
        else:
            glutPostRedisplay()
            return 
    
    if game_state == "game_over":
        # Game is over, stop all updates
        glutPostRedisplay()
        return
    
    
    if game_state != "game_over":
        player.update()
        items_manager.update() 
        update_bullets() 
    
    if game_state == "punishment":
        guardian.update()
        if guardian.is_active and guardian.check_collision_with_player():
            print("The guardian has caught you! Game over.")
            game_state = "game_over"
    
    dx = player.x - guardian.x
    dy = player.y - guardian.y
    guardian.rotate = math.degrees(math.atan2(dy, dx))

    current_time = time.time()
    if current_time - last_regen_time >= MAZE_REGEN_INTERVAL_SECONDS:
        print("Generating new maze...")
        maze.generate()
        walls_to_draw = maze.get_walls_vertices()
        last_regen_time = current_time
    
        px = int((player.x / CELL_SIZE) + (MAZE_WIDTH / 2))
        py = int((player.y / CELL_SIZE) + (MAZE_HEIGHT / 2))
        
        
        
        if 0 <= px < MAZE_WIDTH and 0 <= py < MAZE_HEIGHT:
                maze.grid[px][py]['walls'] = {'up': False, 'down': False, 'left': False, 'right': False}
                
                # symmetrically open adjacent cells corresponding walls
                # Up neighbor
                if py + 1 < MAZE_HEIGHT:
                    maze.grid[px][py + 1]['walls']['down'] = False
                # Down neighbor
                if py - 1 >= 0:
                    maze.grid[px][py - 1]['walls']['up'] = False
                # Left neighbor
                if px - 1 >= 0:
                    maze.grid[px - 1][py]['walls']['right'] = False
                # Right neighbor
                if px + 1 < MAZE_WIDTH:
                    maze.grid[px + 1][py]['walls']['left'] = False
                
                # player.x = (px - MAZE_WIDTH / 2) * CELL_SIZE + CELL_SIZE / 2
                # player.y = (py - MAZE_HEIGHT / 2) * CELL_SIZE + CELL_SIZE / 2
                
                # update walls_to_draw after modifications
                walls_to_draw = maze.get_walls_vertices()
        
        # px = int((player.x / CELL_SIZE) + (MAZE_WIDTH / 2))
        # py = int((player.y / CELL_SIZE) + (MAZE_HEIGHT / 2))
        # if 0 <= px < MAZE_WIDTH and 0 <= py < MAZE_HEIGHT:
        #     # Open all walls in a 3x3 area
        #     for dx in [-1, 0, 1]:
        #         for dy in [-1, 0, 1]:
        #             nx = px + dx
        #             ny = py + dy
        #             if 0 <= nx < MAZE_WIDTH and 0 <= ny < MAZE_HEIGHT:
        #                 maze.grid[nx][ny]['walls'] = {'up': False, 'down': False, 'left': False, 'right': False}
        #     player.x = (px - MAZE_WIDTH / 2) * CELL_SIZE + CELL_SIZE / 2
        #     player.y = (py - MAZE_HEIGHT / 2) * CELL_SIZE + CELL_SIZE / 2
        #     walls_to_draw = maze.get_walls_vertices()

    if player.gun==False:
        for g in GUNS:
            if g["picked"]==False:
                x,y=g["pos"]
                dist = math.sqrt((player.x - x)**2 + (player.y - y)**2)
                if dist<4:
                    g["picked"]=True
                    player.gun=True
                    print("Player picked the GUN")
                    break
    if freeze_end_time > 0 and time.time() > freeze_end_time:
            PLAYER_SPEED = 0.1 # restore normal speed
            freeze_end_time = 0
            print("Player unfrozen!")
    for trap in TRAP:
        if trap["active"]==False:
            continue
        else:
            x,y=trap["pos"]
            dist = math.sqrt((player.x -x)**2 + (player.y - y)**2)   
            if dist<=3:
                trap['active'] = False       
                print(f"Player hit a {trap['type']} trap\n")
                if trap["type"] == "damage":
                    LIFE -= 20
                    LIFE = max(LIFE, 0)
                    print("player lost 20 life point")
                if trap["type"] == "Freeze":
                     PLAYER_SPEED = 0
                     freeze_end_time = time.time() + 10   
                     print("Player is frozen")
    
                if trap["type"]=="Unpick":
                    if player.gun:
                        player.gun=False
                        print("player dropped the gun")
                        
                                     
    for item in items_manager.items:
        if item['picked']:
            continue
        it_x,it_y=item['pos']
        dist = math.sqrt((player.x -it_x)**2 + (player.y - it_y)**2)
        if dist<1.5:
            item['picked'] = True
            if item['type']=='speed':
                PLAYER_SPEED+=0.1
                print("Speed increased:", PLAYER_SPEED)
                PLAYER_SPEED = min(PLAYER_SPEED ,0.5)
            elif item['type'] == "damage":
                DAMAGE += 50
                DAMAGE= min(DAMAGE,100)
                print("Damage increased:", DAMAGE)

            elif item['type'] == "heal":
                LIFE += 50
                LIFE =min(LIFE,200)
                print("Life increased:", LIFE)

            elif item['type'] == "restore":
                LIFE = RESTORE  
                print("Life fully restored:", LIFE)    

    if cheat_mode:
        elapsed = time.time() - cheat_start_time
        if elapsed >= 10.0:   
            cheat_mode = False
            print("Cheat mode deactivated!")
    regen_guns()
    items_manager.update()
    glutPostRedisplay()


def main():
    global walls_to_draw, maze, last_regen_time,player,gun_pos,items_manager, guardian
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_size_x, window_size_y)
    glutInitWindowPosition(500, 50)
    glutCreateWindow(b"Great Escape") 
    glClearColor(*SKY_COLOR, 1.0)
    glEnable(GL_DEPTH_TEST)

    maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)
    maze.generate()
    walls_to_draw = maze.get_walls_vertices()
    start_x = ((-MAZE_WIDTH / 2) * CELL_SIZE + CELL_SIZE)
    start_y = ((-MAZE_HEIGHT / 2) * CELL_SIZE + CELL_SIZE)
    player = Player(start_x, start_y)
    
    
    exit_x = (MAZE_WIDTH / 2) * CELL_SIZE - CELL_SIZE
    exit_y = (MAZE_HEIGHT / 2) * CELL_SIZE - CELL_SIZE
    guardian = Guardian(exit_x, exit_y, 0)
    
    spawn_enemies(maze, count=8)   # choose count as you like
    for e in ENEMIES: print("ENEMY", e.type, e.x, e.y)
    
    glutDisplayFunc(showScreen)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    for i in range(4):
        gun_pos = generate_gun(maze)
        GUNS.append({'pos': (gun_pos), 'picked': False})
    regen_guns()  
    for trap in trap_type:
        for i in range(3):  
            TRAP.append(spawn_traps(maze, trap))
    glutIdleFunc(idle_func)
    items_manager = Items(maze)
    
    glutKeyboardFunc(keyboardListener)      
    glutKeyboardUpFunc(keyboardUpListener)  
    glutMainLoop()

if __name__ == "__main__":
    main()