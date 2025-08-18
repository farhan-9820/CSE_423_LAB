from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math 
import random

# Window size
WIDTH, HEIGHT = 1000, 800

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, 0, HEIGHT)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, WIDTH/HEIGHT, 1, 1000)  # fov, aspect, near, far
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    # Camera position
    gluLookAt(0, 5, 20, 0, 0, 0, 0, 1, 0)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setupCamera()

    # Example: draw a cube in the center
    glColor3f(0, 1, 0)
    glutWireCube(5)

    # Example: draw text
    draw_text(10, HEIGHT - 20, "3D OpenGL Template")

    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow(b"3D OpenGL Template")

    glEnable(GL_DEPTH_TEST)

    glutDisplayFunc(showScreen)
    glutIdleFunc(showScreen)
    glutMainLoop()

if __name__ == "__main__":
    main()
