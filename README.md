# Rendering-Engine
A simply 3D rendering engine capable of displaying simple shapes. 

It is currently very inefficient due to being written and interpreted in Python. I am looking into transistioning into C++ using OpenGL, however I am not fully happy with how much I have achieved and believe it can be made more efficient while staying in Python.
Uses Tkinter to draw shapes and Numpy to process matrices.

So far:
- Drawing points in 3D Space with perspective
- Linking the points into lines
- Adding planes to make shapes
- Clipping lines and planes off-screen
- Draw order for planes (works the majority of the time, as long as the camera is not too close to the object)

Working on:
- Drawing planes using triangles
- Improving draw order and culling
- Adding other shapes than cuboids
- Using a z-buffer method to fix draw order issues

Issues:
- Splitting faces into triangles to be drawn currently results in the faces not being fully covered
- This is because the triangulation algorithm does not work as it should - looking into this

  Timeline of Files:
  - Engine (new clipping): original upload to Github, implemented clipping
  - Engine (polygons): changed faces to not randomly change colour every frame (was very annoying), added extraction of planes and lines from points given for a cuboid
  - Engine (Draw Order): CURRENT MOST UPDATED FILE! Fixed clipping algorithm to actually work, experimented with triangulation of faces, streamlined processing of points and removed drawing of lines since they are drawn using polygons anyway
