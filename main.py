from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
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
PLAYER_SPEED = 0.1

freeze_end_time =0
MAZE_WIDTH = 20
MAZE_HEIGHT = 20
CELL_SIZE = 10.0  # Size of a single maze cell
WALL_HEIGHT = 4.0
WALL_THICKNESS = 0.2
WALL_COLOR = (0.5, 0.5, 0.5)
SKY_COLOR = (0.3, 0.7, 1.0)
FLOOR_COLOR = (0.2, 0.2, 0.2)
START_COLOR = (0.0, 1.0, 0.0)
EXIT_COLOR = (1.0, 0.0, 0.0)

# Dynamic maze settings
MAZE_REGEN_INTERVAL_SECONDS = 30.0
last_regen_time = 0


TRAP=[]
trap_type=[
   ("damage",(1.0, 0.6, 0.6)),
   ("Freeze",(0.6, 0.6, 1.0)),
   ("Unpick",(0.6, 1.0, 0.6))

]

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
        self.z = y
        self.rotate = rotate
        self.game_over = False
        self.quadric = gluNewQuadric()
        self.radius = 1.0
        self.gun=False
    def update(self):
            speed = PLAYER_SPEED
            rotate_speed = 2.0
            yaw_rad = math.radians(self.rotate)
            fwd_x = math.sin(yaw_rad)
            fwd_y = math.cos(yaw_rad)

            new_x, new_y = self.x, self.y

   
            if b'w' in keys and keys[b'w']:
                nx = self.x + fwd_x * speed
                ny = self.y + fwd_y * speed
             
                if not maze.would_collide(nx, self.y, self.radius):
                    new_x = nx
             
                if not maze.would_collide(self.x, ny, self.radius):
                    new_y = ny

         
            if b's' in keys and keys[b's']:
                nx = self.x - fwd_x * speed
                ny = self.y - fwd_y * speed
                if not maze.would_collide(nx, self.y, self.radius):
                    new_x = nx
                if not maze.would_collide(self.x, ny, self.radius):
                    new_y = ny

            if b'd' in keys and keys[b'd']:
                self.rotate += rotate_speed
            if b'a' in keys and keys[b'a']:
                self.rotate -= rotate_speed

            half_maze_x = (MAZE_WIDTH * CELL_SIZE) / 2
            half_maze_y = (MAZE_HEIGHT * CELL_SIZE) / 2
            new_x = max(-half_maze_x, min(new_x, half_maze_x))
            new_y = max(-half_maze_y, min(new_y, half_maze_y))

            
            self.x, self.y = new_x, new_y



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

            # Gun attached to player
            glPushMatrix()
            gun_length = scale * 2.0        
            gun_thickness = scale * 0.25    
            chest_z = scale * 1
            forward_offset = scale + gun_length * 0.5  
            glTranslatef(0.0, forward_offset, chest_z)
            glScalef(gun_thickness, gun_length, gun_thickness)
            glColor3f(0.8, 0.8, 0.1)
            glutSolidCube(1.0)
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
def regen_guns(value=0):
    global GUNS, maze
    GUNS.clear()
    for _ in range(4): 
        gun_pos = generate_gun(maze, offset=15)
        GUNS.append({'pos': gun_pos, 'picked': False})
    glutTimerFunc(30000, regen_guns, 0)

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
    def __init__(self,maze, regen_interval=15000, offset=15):
        self.maze = maze
        self.regen_interval = regen_interval
        self.offset = offset   
        self.items = []
        self.item_types = ["heal", "damage", "speed", "restore"]
        self.generate_items()        
        glutTimerFunc(self.regen_interval, self.regen_items, 0)
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

    def regen_items(self, value=0):
            self.generate_items()
            glutTimerFunc(self.regen_interval, self.regen_items, 0)

    def update(self):
            for item in self.items:
                item['float_offset'] = math.sin(glutGet(GLUT_ELAPSED_TIME) * 0.003) * 0.2

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
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = []
        self.regen_time = 0 

    def generate(self):
        """Generates a new maze using a recursive backtracking algorithm."""
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

                if direction == 'up':           # neighbor = (x, y-1), i.e. world -Y
                    self.grid[current_x][current_y]['walls']['down'] = False
                    self.grid[next_x][next_y]['walls']['up'] = False
                elif direction == 'down':       # neighbor = (x, y+1), i.e. world +Y
                    self.grid[current_x][current_y]['walls']['up'] = False
                    self.grid[next_x][next_y]['walls']['down'] = False
                elif direction == 'left':       # neighbor = (x-1, y), i.e. world -X
                    self.grid[current_x][current_y]['walls']['left'] = False
                    self.grid[next_x][next_y]['walls']['right'] = False
                elif direction == 'right':      # neighbor = (x+1, y), i.e. world +X
                    self.grid[current_x][current_y]['walls']['right'] = False
                    self.grid[next_x][next_y]['walls']['left'] = False
                
                else:
                    stack.pop()

                self.grid[next_x][next_y]['visited'] = True
                stack.append((next_x, next_y))
            else:
                stack.pop()

        # Guarantee entry/exit
        self.grid[0][0]['walls']['left'] = False
        self.grid[self.width - 1][self.height - 1]['walls']['right'] = False

    def get_walls_vertices(self):
        """Return wall vertices aligned with Z as up-axis."""
        walls = []
        for x in range(self.width):
            for y in range(self.height):
                cell = self.grid[x][y]

                cx = (x - self.width / 2) * CELL_SIZE
                cy = (y - self.height / 2) * CELL_SIZE
                cz = 0  # ground level

                if cell['walls']['up']:
                    walls.extend([
                        (cx - CELL_SIZE/2, cy + CELL_SIZE/2, cz),
                        (cx + CELL_SIZE/2, cy + CELL_SIZE/2, cz),
                        (cx + CELL_SIZE/2, cy + CELL_SIZE/2, cz + WALL_HEIGHT),
                        (cx - CELL_SIZE/2, cy + CELL_SIZE/2, cz + WALL_HEIGHT),
                    ])
                if cell['walls']['down']:
                    walls.extend([
                        (cx + CELL_SIZE/2, cy - CELL_SIZE/2, cz),
                        (cx - CELL_SIZE/2, cy - CELL_SIZE/2, cz),
                        (cx - CELL_SIZE/2, cy - CELL_SIZE/2, cz + WALL_HEIGHT),
                        (cx + CELL_SIZE/2, cy - CELL_SIZE/2, cz + WALL_HEIGHT),
                    ])
                if cell['walls']['left']:
                    walls.extend([
                        (cx - CELL_SIZE/2, cy - CELL_SIZE/2, cz),
                        (cx - CELL_SIZE/2, cy + CELL_SIZE/2, cz),
                        (cx - CELL_SIZE/2, cy + CELL_SIZE/2, cz + WALL_HEIGHT),
                        (cx - CELL_SIZE/2, cy - CELL_SIZE/2, cz + WALL_HEIGHT),
                    ])
                if cell['walls']['right']:
                    walls.extend([
                        (cx + CELL_SIZE/2, cy + CELL_SIZE/2, cz),
                        (cx + CELL_SIZE/2, cy - CELL_SIZE/2, cz),
                        (cx + CELL_SIZE/2, cy - CELL_SIZE/2, cz + WALL_HEIGHT),
                        (cx + CELL_SIZE/2, cy + CELL_SIZE/2, cz + WALL_HEIGHT),
                    ])
        return walls
    def would_collide(self, x, y, radius):
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                # translate world coordinates into cell indices 
                fx = (x / CELL_SIZE) + (self.width / 2)
                fy = (y / CELL_SIZE) + (self.height / 2)
                cell_x = int(math.floor(fx)) + dx
                cell_y = int(math.floor(fy)) + dy

                
                cell_x = max(0, min(self.width - 1, cell_x))
                cell_y = max(0, min(self.height - 1, cell_y))

                cell = self.grid[cell_x][cell_y]

                # position in cell relative to cell center
                center_x = (cell_x - self.width / 2) * CELL_SIZE
                center_y = (cell_y - self.height / 2) * CELL_SIZE
                dx_local = x - center_x
                dy_local = y - center_y
                half = CELL_SIZE / 2.0
                pad = radius + (WALL_THICKNESS / 2.0)

                # Right wall at x = center_x + half
                if cell['walls']['right']:
                    dist = (center_x + half) - x  # >0 when inside cell
                    if 0 <= dist <= pad and abs(dy_local) <= half:
                        return True

                # Left wall at x = center_x - half
                if cell['walls']['left']:
                    dist = x - (center_x - half)
                    if 0 <= dist <= pad and abs(dy_local) <= half:
                        return True

                # Up wall at y = center_y + half
                if cell['walls']['up']:
                    dist = (center_y + half) - y
                    if 0 <= dist <= pad and abs(dx_local) <= half:
                        return True

                # Down wall at y = center_y - half
                if cell['walls']['down']:
                    dist = y - (center_y - half)
                    if 0 <= dist <= pad and abs(dx_local) <= half:
                        return True

        return False
    

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
    keys[key.lower() if isinstance(key, bytes) else key.lower().encode()] = True

def keyboardUpListener(key, x, y):
    keys[key.lower() if isinstance(key, bytes) else key.lower().encode()] = False

    if key == b'b' and player.gun:
        create_bullets()


def draw_start_exit_points():
    """Renders the starting and exit squares on the floor."""
    glPushMatrix()

    # Draw the start point
    start_x = (-MAZE_WIDTH / 2) * CELL_SIZE + CELL_SIZE
    start_y = (-MAZE_HEIGHT / 2) * CELL_SIZE + CELL_SIZE
    glColor3fv(START_COLOR)
    glBegin(GL_QUADS)
    glVertex3f(start_x - CELL_SIZE/2, start_y - CELL_SIZE/2, 0)
    glVertex3f(start_x + CELL_SIZE/2, start_y - CELL_SIZE/2, 0)
    glVertex3f(start_x + CELL_SIZE/2, start_y + CELL_SIZE/2, 0)
    glVertex3f(start_x - CELL_SIZE/2, start_y + CELL_SIZE/2, 0)
    glEnd()

    # Draw the exit point
    exit_x = (MAZE_WIDTH / 2) * CELL_SIZE - CELL_SIZE
    exit_z = (MAZE_HEIGHT / 2) * CELL_SIZE - CELL_SIZE
    glColor3fv(EXIT_COLOR)
    glBegin(GL_QUADS)
    glVertex3f(exit_x - CELL_SIZE/2,  exit_z - CELL_SIZE/2, 0)
    glVertex3f(exit_x + CELL_SIZE/2,  exit_z - CELL_SIZE/2, 0)
    glVertex3f(exit_x + CELL_SIZE/2,  exit_z + CELL_SIZE/2, 0)
    glVertex3f(exit_x - CELL_SIZE/2,  exit_z + CELL_SIZE/2, 0)
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
        # Toggle camera mode between orbit and player-head view
        camera_mode = 'player' if camera_mode == 'orbit' else 'orbit'
        glutPostRedisplay()




def showScreen():
    global window_size_x, window_size_y, walls_to_draw, maze,items_manager
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
    player.draw()
    glutSwapBuffers()


def idle_func():
    global last_regen_time, walls_to_draw,player,items_manager,PLAYER_SPEED,DAMAGE,LIFE,RESTORE,game_over,freeze_end_time 
    player.update()
    items_manager.update() 
    update_bullets() 

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

    for trap in TRAP:
        if trap["active"]==False:
            continue
        else:
            x,y=trap["pos"]
            dist = math.sqrt((player.x -x)**2 + (player.y - y)**2)   
            if dist<3:
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
                if freeze_end_time > 0 and time.time() > freeze_end_time:
                        PLAYER_SPEED = 0.1 
                        freeze_end_time = 0
                if trap["type"]=="unpick":
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
                PLAYER_SPEED+=0.5
                print("Speed increased:", PLAYER_SPEED)
                PLAYER_SPEED = min(PLAYER_SPEED ,2)
            elif item['type'] == "damage":
                DAMAGE += 50
                DAMGE= min(DAMAGE,100)
                print("Damage increased:", DAMAGE)

            elif item['type'] == "heal":
                LIFE += 50
                LIFE =min(LIFE,200)
                print("Life increased:", LIFE)

            elif item['type'] == "restore":
                LIFE = RESTORE  
                print("Life fully restored:", LIFE)    


    glutPostRedisplay()


def main():
    global walls_to_draw, maze, last_regen_time,player,gun_pos,items_manager
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_size_x, window_size_y)
    glutInitWindowPosition(500, 50)
    glutCreateWindow(b"Great Escape") 

    glClearColor(*SKY_COLOR, 1.0)

    maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)
    maze.generate()
    walls_to_draw = maze.get_walls_vertices()
    
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
    start_x = ((-MAZE_WIDTH / 2) * CELL_SIZE + CELL_SIZE)
    start_y = ((-MAZE_HEIGHT / 2) * CELL_SIZE + CELL_SIZE)
    player = Player(start_x, start_y)
    player.z = 0 
    player.rotate = 0 
    glutKeyboardFunc(keyboardListener)      
    glutKeyboardUpFunc(keyboardUpListener)  
    glutMainLoop()

if __name__ == "__main__":
    main()
