from tkinter import Misc, Tk, Canvas, Frame, BOTH
from random import randint
from numpy import array, matmul
import numpy as np
from math import sin,cos,pi,radians,atan,degrees,tan,hypot,atan2

# Algebra
# ----------------------------------------------------------------------------------

def add(v1,v2):
    result = [[],[]]
    result[0] = v1[0] + v2[0]
    result[1] = v1[1] + v2[1]
    return array(result)


# Engine
# ---------------------------------------------------------------------------------------
class Engine(Frame):

    def __init__(self,tk):
        self.current_polygons = []
        self.next_id = 0
        super().__init__() # Initiates Canvas
        self.root = tk
        self.initUI(tk) # Passes root into initUI
        
        self.INSIDE = 0  # 0000
        self.LEFT = 1  # 0001
        self.RIGHT = 2  # 0010
        self.BOTTOM = 4  # 0100
        self.TOP = 8  # 1000

        self.x_max = 1
        self.y_max = 1
        self.x_min = -1
        self.y_min = -1
        self.origin = [0,0]
        
    def initUI(self,tk):

        self.master.title("Engine") # Titles window
        self.pack(fill=BOTH, expand=1) 

        
        self.canvas = Canvas(tk, width=1920,height=1080) # Ties canvas to engine window
        self.camera = Camera(self)
        self.master.bind("<Key>",self.camera.keyHandler) # Binds keyboard actions to a handler function
        self.master.bind("<Motion>",self.camera.mouseHandler) # Binds mouse actions to a handler function
        self.focus_set() # Sets mouse and key focus to the window
        self.pack(fill=BOTH, expand=1) 

    def draw_point(self,point): # Draws a point given screen coords (Top left is (0,0))
        x = point[0]
        y = point[1]
        
        x1,y1 = x-1,y-1
        x2,y2 = x+1,y+1

        self.canvas.create_oval(x1,y1,x2,y2,fill="#000") # Creates a point
        self.canvas.pack(fill=BOTH, expand=1) # Updates the canvas

    def draw_line(self,a,b): # Draws a line between 2 points
        
        x1 = a[0]
        y1 = a[1]

        x2 = b[0]
        y2 = b[1]

        self.canvas.create_line(x1,y1,x2,y2,fill="#000") # Creates a line
        self.canvas.pack(fill=BOTH, expand=1) # Updates the canvas

    def draw_polygon(self,points,colour): # draws a polygon between points
        #print(points)
        
        
        self.canvas.create_polygon(points,fill=colour,outline='#000') # Creates a line
        self.canvas.pack(fill=BOTH, expand=1) # Updates the canvas

    def transforms(self): # Main transformation routine: raw 3d point -> 3d point relative to camera -> 3d point in perspective -> 2d screen point
        self.canvas.delete("all")
        camera = self.camera.get_camera_transform() # Gets camera transform
        can_view = self.camera.get_perspective_transform() # Gets perspective transform

        for object in self.current_polygons: # Loops through current objects

            # Drawing Points
            # ---------------------------------------------------------------------------------------------
            for point in object.vertices: # Gets each point in object
                
                new_point = matmul(camera,array(point.coords)) # Converts point to relative to camera
                if new_point[2] >= 0:
                    point.behind = False
                    can_point = matmul(can_view,new_point) 

                    view_point = np.divide(can_point,can_point[3]*np.ones(4)) # Converts point to perspective
                    
                    point.view_point = view_point

                    if self.check_in_cube(view_point) == True: # Checks if point should be visible
                        point.in_cube = True

                        screenpoint = self.convert_point(view_point) # Converts to 2d screen point
                        point.renderpoint = screenpoint

                        #self.draw_point(screenpoint) # Renders screen point

                    else:
                        point.in_cube = False
                else:
                    point.behind = True

            # Drawing Triangles
            # ----------------------------------------------------------------------------------------------
            
            order = self.get_order(object.planes,camera,can_view)
            
            for triangle in order:
                
                polygon_points = []
                    
                for line in triangle.lines:
                    if line.a.behind == False and line.b.behind == False:
                        
                        a,b,check = self.sutherland_clip(line.a.view_point,line.b.view_point)
                        
                        if check == True:
                            
                            line.a.renderpoint = self.convert_point(a)
                            line.a.in_cube = True
                            line.b.renderpoint = self.convert_point(b)
                            line.b.in_cube = True
                            self.draw_line(line.a.renderpoint,line.b.renderpoint)

                            polygon_points.append(line.a.renderpoint)
                            polygon_points.append(line.b.renderpoint)
                
                print(triangle.points)
                
                polygon_points = [list(t) for t in set(tuple(element) for element in polygon_points)]
                if polygon_points != []:
                    self.origin = polygon_points[0]

                    polygon_points = sorted(polygon_points,key=self.clockwiseangle_and_distance)


                    print(polygon_points)
                    if len(polygon_points) > 3:
                        
                        triangles = self.triangulate(polygon_points)
                        
                        print("triangles:",triangles)
                        for tri in triangles:
                            
                            self.draw_polygon(list(tri),triangle.plane.colour)
                            pass
                    else:
                        if polygon_points != []:
                            self.draw_polygon(polygon_points,triangle.plane.colour)
                            pass    
        # Centre marker 
        self.draw_point([960,540])

    def triangulate(self,poly):
        t = []
        for i in range(1,len(poly)-1):
            t.append([poly[0],poly[i],poly[i+1]])
        return t

    def clockwiseangle_and_distance(self,point):
        
        origin = self.origin

        refvec = [0,1]
        # Vector between point and the origin: v = p - o
        vector = [point[0]-origin[0], point[1]-origin[1]]
        # Length of vector: ||v||
        lenvector = hypot(vector[0], vector[1])
        # If length is zero there is no angle
        if lenvector == 0:
            return -pi, 0
        # Normalize vector: v/||v||
        normalized = [vector[0]/lenvector, vector[1]/lenvector]
        dotprod  = normalized[0]*refvec[0] + normalized[1]*refvec[1]     # x1*x2 + y1*y2
        diffprod = refvec[1]*normalized[0] - refvec[0]*normalized[1]     # x1*y2 - y1*x2
        angle = atan2(diffprod, dotprod)
        # Negative angles represent counter-clockwise angles so we need to subtract them 
        # from 2*pi (360 degrees)
        if angle < 0:
            return 2*pi+angle, lenvector
        # I return first the angle because that's the primary sorting criterium
        # but if two vectors have the same angle then the shorter distance should come first.
        return angle, lenvector

    def sutherland_clip(self,a,b):
        
        x1 = a[0]
        y1 = a[1]

        x2 = b[0]
        y2 = b[1]

        codea = self.get_region(a)
        codeb = self.get_region(b)
        accept = False

        a_out = [0,0]
        b_out = [0,0]
        

        if codea == self.INSIDE:
            a_out = [a[0],a[1]]
        if codeb == self.INSIDE:
            b_out = [b[0],b[1]]

        while True:

            # both in rectangle
            if codea == self.INSIDE and codeb == self.INSIDE:
                accept = True
                                
                break
            
            # both outside rectangle
            elif (codea & codeb) != self.INSIDE:
                a_out = [a[0],a[1]]
                b_out = [b[0],b[1]]
                break
            
            # some part in rectangle
            else:

                x = 1.0
                y = 1.0

                if codea != self.INSIDE:
                    code_out = codea
                else:
                    code_out = codeb

                if code_out & self.TOP:
                    # Point is above the clip rectangle
                    x = x1 + (x2 - x1) * (self.y_max - y1) / (y2 - y1)
                    y = self.y_max
                elif code_out & self.BOTTOM:
                    # Point is below the clip rectangle
                    x = x1 + (x2 - x1) * (self.y_min - y1) / (y2 - y1)
                    y = self.y_min
                elif code_out & self.RIGHT:
                    # Point is to the right of the clip rectangle
                    y = y1 + (y2 - y1) * (self.x_max - x1) / (x2 - x1)
                    x = self.x_max
                elif code_out & self.LEFT:
                    # Point is to the left of the clip rectangle
                    y = y1 + (y2 - y1) * (self.x_min - x1) / (x2 - x1)
                    x = self.x_min
    
                if code_out == codea:
                    a_out[0] = x
                    a_out[1] = y
                    codea = self.get_region(a_out)
                    
                else:
                    b_out[0] = x
                    b_out[1] = y
                    codeb = self.get_region(b_out)
                
                

        return a_out,b_out,accept    

    def get_region(self,point):
        code = self.INSIDE
        if point[0] < self.x_min:  # to the left of rectangle
            code |= self.LEFT
        elif point[0] > self.x_max:  # to the right of rectangle
            code |= self.RIGHT
        if point[1] < self.y_min:  # below the rectangle
            code |= self.BOTTOM
        elif point[1] > self.y_max:  # above the rectangle
            code |= self.TOP
        return code    

    def get_order(self,planes,cam,can):
        
        order = []
        for plane in planes:
            for triangle in plane.triangles:
            
                centre = array(triangle.centroid)
                point = matmul(cam,centre)
                can_point = matmul(can,point) 

                triangle.view_point = np.divide(can_point,can_point[3]*np.ones(4))

                # Sort planes by z
                if len(order) == 0:
                    order.append(triangle)
                else:
                    added = False
                    for i in range(0,len(order)):
                        print(triangle.view_point)
                        if triangle.view_point[2] > order[i].view_point[2]:
                            order.insert(i, triangle)
                            added = True
                            break
                        
                    if added == False:
                        order.append(triangle)  
        
        return order
        
    def convert_point(self,point): # Converts as perspective point to a 2d screen point to be displayed
        x = point[0] + 1
        y = -(point[1] - 1)

        new_x = x * 960
        new_y = y * 540

        
        return [new_x,new_y]

    def check_in_cube(self,point): # Checks if a point should be visible (ie is inside the canonical view volume)
        if point[0] > 1 or point[0] < -1:       
            return False
        elif point[1] > 1 or point[1] < -1:       
            return False
        elif point[2] > 1 or point[2] < -1:       
            return False
        else:
            return True
        

    def new_object(self,type,vertices,coords): # Creates a new object 
        
        object = Object(type,vertices,self.next_id,coords)

        self.current_polygons.append(object)
        self.next_id += 1


    @staticmethod
    def getRandColour():
        colour = "#"
        for i in range(0,3):
            colour += hex(randint(0,15)) # Random colour
            
        colour = colour.replace("0x","")
        return colour



# Camera
# ----------------------------------------------------------------------------------------------

class Camera():
    def __init__(self,engine) -> None:
        self.__abspos = [0,0.5,0] # [x,y,z]
        self.__angles = [0,0,0] # For some reason I only got it to work with [y,z,x], but y and z are only angles changing so doesn't matter
        self.__fFOV = 90
        self.__aspect = 1.78
        self.__nearbuffer = 0.5
        self.__farbuffer = 50
        
        self.__engine = engine

        self.old_z = 1920/2
        self.old_y = 1080/2
        self.movespd = 0.1
    
    def angle_wrap(self):
        if self.__angles[1] >= 360:
            self.__angles[1] = self.__angles[1] - 360
        elif self.__angles[1] <= 0:
            self.__angles[1] = self.__angles[1] + 360

        if self.__angles[0] >= 360:
            self.__angles[0] = self.__angles[0] - 360
        elif self.__angles[0] <= 0:
            self.__angles[0] = self.__angles[0] + 360

    def mouseHandler(self,event): # Recieves the mouse actions (A bit janky but only way I could figure out to do it)
        current_z = event.x
        current_y = event.y

        if current_z > self.old_z: # Change Horizontal Angle
            self.__angles[1] += 1
        elif current_z < self.old_z:
            self.__angles[1] -= 1

        if current_y > self.old_y: # Change Vertical Angle
            self.__angles[0] -= 0.25
        elif current_y < self.old_y:
            self.__angles[0] += 0.25

        self.angle_wrap()

        self.old_z = current_z
        self.old_y = current_y
        
        #print("angles: ",self.__angles)
        self.__engine.transforms() # Updates screen
    

    def keyHandler(self,event): # Recieves keyboard actions

        key = event.char
        

        if key == "r": # press "r" to close window
            self.__engine.root.destroy()
            
        elif key == 'i' or key == 'k':
            if key == 'i':
                self.__abspos[1] += 0.5
            else:
                self.__abspos[1] -= 0.5
            
            self.__engine.transforms() # Updates screen
            
        else:
            if key == 'a':          
                mod = -90

            elif key == 'd':
                mod = 90
            
            elif key == 's':
                mod = 180
                
            elif key == 'w':
                mod = 0
            
            
            self.__abspos[0] += self.movespd * sin(radians(self.__angles[1] + mod))
            self.__abspos[2] += self.movespd * cos(radians(self.__angles[1] + mod))

            #print("pos: ",self.__abspos)

            self.__engine.transforms() # Updates screen
    
    def get_camera_transform(self): # Gets camera transform
        # Translation
        T = array([[1,0,0,-self.__abspos[0]],[0,1,0,-self.__abspos[1]],[0,0,1,-self.__abspos[2]],[0,0,0,1]])
        
        # Rotation
        x = -radians(self.__angles[0])
        y = -radians(self.__angles[1])
        z = -radians(self.__angles[2])
        x_matrix = array([[1,0,0,0],[0,cos(x),sin(x),0],[0,-sin(x),cos(x),0],[0,0,0,1]])
        y_matrix = array([[cos(y),0,sin(y),0],[0,1,0,0],[-sin(y),0,cos(y),0],[0,0,0,1]])
        z_matrix = array([[cos(z),-sin(z),0,0],[sin(z),cos(z),0,0],[0,0,1,0],[0,0,0,1]])

        

        R = matmul(x_matrix,y_matrix,z_matrix)
         
        # Overall Matrix
        C = matmul(R,T)
        
        return array(C)

    def get_perspective_transform(self): # Gets perspective transform
        n = self.__nearbuffer
        f = self.__farbuffer
        r = tan(radians(self.__fFOV/2)) * n
        t = tan(radians((self.__fFOV/self.__aspect)/2)) * n
        l = -r
        b = -t

        view_transform = array([[((2*n)/(r-l)),0,-((r+l)/(r-l)),0],[0,((2*n)/(t-b)),-((t+b)/(t-b)),0],[0,0,((f+n)/(f-n)),-((2*f*n)/(f-n))],[0,0,1,0]])

        return view_transform  
    

    @property
    def position(self):
        return self.__abspos
    


# Objects
# ------------------------------------------------------------------------------------------

class Object():
    def __init__(self,type,points,id,coords) -> None:
        self.centrepos = coords
        self.vertices = []
        self.lines = []
        self.planes = []
        self.__id = id
        self.__type = type

        for point in points:
            x = point[0] + coords[0]
            y = point[1] + coords[1]
            z = point[2] + coords[2]
            
            self.vertices.append(Point([x,y,z,1]))

        if self.__type == "cuboid": # Calculates lines for rectangle rather than having to type them all in (will sort other shapes later)
            #print(self.vertices)
            # Bottom Plane
            self.lines.extend([Line(self.vertices[0],self.vertices[1]),Line(self.vertices[0],self.vertices[2]),Line(self.vertices[1],self.vertices[3]),Line(self.vertices[2],self.vertices[3])])

            # Top Plane
            self.lines.extend([Line(self.vertices[4],self.vertices[5]),Line(self.vertices[4],self.vertices[6]),Line(self.vertices[5],self.vertices[7]),Line(self.vertices[6],self.vertices[7])])

            # Connectors
            self.lines.extend([Line(self.vertices[0],self.vertices[4]),Line(self.vertices[1],self.vertices[5]),Line(self.vertices[2],self.vertices[6]),Line(self.vertices[3],self.vertices[7])])

            # Planes
            # - Bottom
            self.planes.append(Plane([self.vertices[0],self.vertices[1],self.vertices[3],self.vertices[2]],"Bottom"))
            # - Top
            self.planes.append(Plane([self.vertices[4],self.vertices[5],self.vertices[7],self.vertices[6]],"Top"))
            # - Front
            self.planes.append(Plane([self.vertices[0],self.vertices[1],self.vertices[5],self.vertices[4]],"Front"))
            # - Back
            self.planes.append(Plane([self.vertices[2],self.vertices[3],self.vertices[7],self.vertices[6]],"Back"))
            # - Left
            self.planes.append(Plane([self.vertices[0],self.vertices[4],self.vertices[6],self.vertices[2]],"Left"))
            # - Right
            self.planes.append(Plane([self.vertices[1],self.vertices[5],self.vertices[7],self.vertices[3]],"Right"))

    @property
    def get_vertices(self):
        return self.vertices
    

class Plane():
    def __init__(self,points,name) -> None:

        self.points = points
        self.view_points = []
        self.colour = Engine.getRandColour()
        self.name = name
        self.triangles = []

        if len(self.points) == 3:
            self.triangles.append(Triangle(self.points,self))
        elif len(self.points) == 4:
            self.triangles.append(Triangle([self.points[0],self.points[1],self.points[2]],self))
            self.triangles.append(Triangle([self.points[0],self.points[2],self.points[3]],self))
    
    def __repr__(self) -> str:
        return self.name

class Triangle():
    def __init__(self,points,plane) -> None:
        self.points = points
        self.plane = plane
        self.centroid = [(points[0].coords[0]+points[1].coords[0]+points[2].coords[0])/3,(points[0].coords[1]+points[1].coords[1]+points[2].coords[1])/3,(points[0].coords[2]+points[1].coords[2]+points[2].coords[2])/3,1]
        self.view_point = [0,0,0,1]

        self.lines = [Line(points[0],points[1]),Line(points[1],points[2]),Line(points[2],points[0])]

    def __repr__(self) -> str:
        return str(self.view_point[2]) + self.plane.name
class Line():
    def __init__(self,a,b):
        self.a = a
        self.b = b
        
class Point():
    def __init__(self,coords):
        self.coords = coords
        self.in_cube = False
        self.renderpoint = array([0,0,0,1])
        self.viewpoint = array([0,0,0,1])
        self.behind = False
    
    def __repr__(self) -> str:
        return str(self.coords)

# Main
# -------------------------------------------------------------------------------------------  

def main():
    root = Tk() # Initialises tkinter etc
    
    engine = Engine(root)
    root.geometry("1920x1080") # Initialises window with dimensions 1920 by 1080

    # clockwise order
    vertices = [[-1,-1,-1],[1,-1,-1],[-1,-1,1],[1,-1,1],[-1,1,-1],[1,1,-1],[-1,1,1],[1,1,1]]

    engine.new_object("cuboid",vertices,[1,1,1]) # Creates cuboid

    

    #vertices1 = [[0,0,-1],[-1,0,-1],[0,0,-2],[-1,0,-2],[-0,3,-1],[-1,3,-1],[0,3,-2],[-1,3,-2]]
    #engine.new_object("cuboid",vertices1,[-10,0,-15]) # Creates cuboid

    engine.transforms()

    root.mainloop()
    
    

if __name__ == '__main__':
    
    main()


