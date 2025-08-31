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
PLAYER_SPEED = 0.5

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




class Maze:
    """Handles the logical generation of the maze and provides rendering data."""
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
        eye_x = player.x - 5
        eye_y = player.y
        eye_z = head_height + 4
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
    global window_size_x, window_size_y, walls_to_draw, maze
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, window_size_x, window_size_y)

    setupCamera()
    draw_floor()
    draw_start_exit_points()
    draw_walls(walls_to_draw)

    
    glutSwapBuffers()


def idle_func():
    global last_regen_time, walls_to_draw,player

    # Check for maze regeneration
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
        
    glutPostRedisplay()


def main():
    
    global walls_to_draw, maze, last_regen_time,player
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
    
    glutIdleFunc(idle_func)
    glutMainLoop()

if __name__ == "__main__":
    main()





