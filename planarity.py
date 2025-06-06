import pygame

import random

# Initialize Pygame
pygame.init()

# Set screen dimensions
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Planarity")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0) # For win message

# Vertex and Edge data structures
# Vertices: list of (x, y) coordinates
# Edges: list of (vertex_index1, vertex_index2) pairs

def generate_random_planar_graph():
    """Generates a simple, fixed planar graph for now."""
    vertices = [
        (random.randint(50, screen_width - 50), random.randint(50, screen_height - 50)) for _ in range(4)
    ]
    # Ensure no overlapping coordinates for simplicity in this initial version
    # A more robust solution would check for overlaps and regenerate if necessary
    vertices = []
    while len(vertices) < 4:
        new_vertex = (random.randint(50, screen_width - 50), random.randint(50, screen_height - 50))
        too_close = False
        for v in vertices:
            if ((new_vertex[0] - v[0])**2 + (new_vertex[1] - v[1])**2)**0.5 < 50: # min distance
                too_close = True
                break
        if not too_close:
            vertices.append(new_vertex)


    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0)  # A square
    ]
    return vertices, edges

def draw_graph(screen, vertices, edges, radius=10):
    """Draws the graph on the screen."""
    # Draw edges
    for edge in edges:
        start_pos = vertices[edge[0]]
        end_pos = vertices[edge[1]]
        pygame.draw.line(screen, BLACK, start_pos, end_pos, 2)

    # Draw vertices
    for vertex_pos in vertices:
        pygame.draw.circle(screen, RED, vertex_pos, radius)

# Generate graph
graph_vertices, graph_edges = generate_random_planar_graph()

# Mouse interaction variables
selected_vertex_index = None
mouse_button_down = False
vertex_radius = 10 # Consistent radius

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left mouse button
                mouse_button_down = True
                mouse_x, mouse_y = event.pos
                for i, (vx, vy) in enumerate(graph_vertices):
                    # Simple distance check for clicking a vertex
                    if ((vx - mouse_x)**2 + (vy - mouse_y)**2)**0.5 < vertex_radius:
                        selected_vertex_index = i
                        break
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Left mouse button
                mouse_button_down = False
                selected_vertex_index = None
        elif event.type == pygame.MOUSEMOTION:
            if mouse_button_down and selected_vertex_index is not None:
                mouse_x, mouse_y = event.pos
                # Keep vertex within screen bounds
                clamped_x = max(vertex_radius, min(mouse_x, screen_width - vertex_radius))
                clamped_y = max(vertex_radius, min(mouse_y, screen_height - vertex_radius))
                graph_vertices[selected_vertex_index] = (clamped_x, clamped_y)

# --- Geometry Functions for Line Segment Intersection ---

def on_segment(p, q, r):
    """Given three collinear points p, q, r, check if point q lies on segment pr."""
    return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
            q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))

def orientation(p, q, r):
    """Find orientation of ordered triplet (p, q, r).
    Returns:
    0 -> p, q, r are collinear
    1 -> Clockwise
    2 -> Counterclockwise
    """
    val = (q[1] - p[1]) * (r[0] - q[0]) - \
          (q[0] - p[0]) * (r[1] - q[1])
    if val == 0: return 0  # Collinear
    return 1 if val > 0 else 2  # Clockwise or Counterclockwise

def do_lines_intersect(p1, q1, p2, q2):
    """Return true if line segment 'p1q1' and 'p2q2' intersect."""
    # Find the four orientations needed for general and special cases
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case
    if o1 != o2 and o3 != o4:
        return True

    # Special Cases for collinear points
    # p1, q1 and p2 are collinear and p2 lies on segment p1q1
    if o1 == 0 and on_segment(p1, p2, q1): return True
    # p1, q1 and q2 are collinear and q2 lies on segment p1q1
    if o2 == 0 and on_segment(p1, q2, q1): return True
    # p2, q2 and p1 are collinear and p1 lies on segment p2q2
    if o3 == 0 and on_segment(p2, p1, q2): return True
    # p2, q2 and q1 are collinear and q1 lies on segment p2q2
    if o4 == 0 and on_segment(p2, q1, q2): return True

    return False  # Doesn't fall in any of the above cases

def check_edge_crossings(vertices, edges):
    """Checks if any non-adjacent edges in the graph intersect.
    Returns True if crossings exist, False otherwise.
    """
    for i in range(len(edges)):
        for j in range(i + 1, len(edges)):
            edge1_v_indices = edges[i]
            edge2_v_indices = edges[j]

            # Skip if edges share a vertex
            if (edge1_v_indices[0] == edge2_v_indices[0] or
                edge1_v_indices[0] == edge2_v_indices[1] or
                edge1_v_indices[1] == edge2_v_indices[0] or
                edge1_v_indices[1] == edge2_v_indices[1]):
                continue

            p1 = vertices[edge1_v_indices[0]]
            q1 = vertices[edge1_v_indices[1]]
            p2 = vertices[edge2_v_indices[0]]
            q2 = vertices[edge2_v_indices[1]]

            if do_lines_intersect(p1, q1, p2, q2):
                return True # Crossings exist
    return False # No crossings

# --- End Geometry Functions ---

# Font for win message
try:
    pygame.font.init() # Ensure font module is initialized
    win_font = pygame.font.Font(None, 74) # Default font, size 74
except Exception as e:
    print(f"Font loading failed: {e}")
    win_font = None # Fallback if font loading fails


# Game state
# Initial check for crossings when the game starts
crossings_exist = check_edge_crossings(graph_vertices, graph_edges)

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left mouse button
                mouse_button_down = True
                mouse_x, mouse_y = event.pos
                for i, (vx, vy) in enumerate(graph_vertices):
                    if ((vx - mouse_x)**2 + (vy - mouse_y)**2)**0.5 < vertex_radius:
                        selected_vertex_index = i
                        break
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Left mouse button
                mouse_button_down = False
                if selected_vertex_index is not None: # Check if a vertex was being dragged
                    crossings_exist = check_edge_crossings(graph_vertices, graph_edges)
                selected_vertex_index = None
        elif event.type == pygame.MOUSEMOTION:
            if mouse_button_down and selected_vertex_index is not None:
                mouse_x, mouse_y = event.pos
                clamped_x = max(vertex_radius, min(mouse_x, screen_width - vertex_radius))
                clamped_y = max(vertex_radius, min(mouse_y, screen_height - vertex_radius))
                graph_vertices[selected_vertex_index] = (clamped_x, clamped_y)
                # Live update of crossing status while dragging
                crossings_exist = check_edge_crossings(graph_vertices, graph_edges)


    # Drawing
    screen.fill(WHITE)
    draw_graph(screen, graph_vertices, graph_edges, vertex_radius)

    if not crossings_exist and win_font:
        win_text = win_font.render("You Win!", True, GREEN)
        text_rect = win_text.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(win_text, text_rect)

    pygame.display.flip()

# Quit Pygame
pygame.quit()
