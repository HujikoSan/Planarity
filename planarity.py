import pygame
import random

# Screen dimensions (constants)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0) # Used for text, maybe for default vertex color
RED_VERTEX = (255, 0, 0) # For vertices
GREEN_EDGE_NON_CROSSING = (0, 150, 0)
RED_EDGE_CROSSING = (200, 0, 0)
WIN_MESSAGE_COLOR = (0, 128, 0) # Darker green for win message

# Vertex and Edge data structures
# Vertices: list of (x, y) coordinates
# Edges: list of (vertex_index1, vertex_index2) pairs

# --- Global constants and utility functions that don't initialize Pygame ---
VERTEX_RADIUS = 10

DEFAULT_NUM_VERTICES = 6
MIN_VERTICES = 3 # A triangle is the smallest interesting cycle
MAX_VERTICES = 20

def get_num_vertices_from_user():
    """Prompts the user for the number of vertices and validates input."""
    num_vertices = DEFAULT_NUM_VERTICES
    try:
        raw_input = input(f"Enter the number of vertices ({MIN_VERTICES}-{MAX_VERTICES}, default: {DEFAULT_NUM_VERTICES}): ")
        val = int(raw_input)
        if MIN_VERTICES <= val <= MAX_VERTICES:
            num_vertices = val
            print(f"Using {num_vertices} vertices.")
        else:
            print(f"Input out of range. Using default: {DEFAULT_NUM_VERTICES} vertices.")
            num_vertices = DEFAULT_NUM_VERTICES
    except ValueError:
        print(f"Invalid integer input. Using default: {DEFAULT_NUM_VERTICES} vertices.")
        num_vertices = DEFAULT_NUM_VERTICES
    except EOFError:
        print(f"No input received (EOF). Using default: {DEFAULT_NUM_VERTICES} vertices.")
        num_vertices = DEFAULT_NUM_VERTICES
    return num_vertices

def generate_random_planar_graph(num_vertices):
    """Generates a graph with a specified number of vertices."""
    _vertices = []
    min_dist_sq = 50**2 # Minimum distance squared for faster checks

    for _ in range(num_vertices):
        placed = False
        # Try a few times to place a vertex before giving up or expanding area (not implemented here)
        for _ in range(100): # Max 100 attempts to find a spot
            new_vertex = (random.randint(VERTEX_RADIUS, SCREEN_WIDTH - VERTEX_RADIUS),
                          random.randint(VERTEX_RADIUS, SCREEN_HEIGHT - VERTEX_RADIUS))
            too_close = False
            for v_coord in _vertices:
                dist_sq = (new_vertex[0] - v_coord[0])**2 + (new_vertex[1] - v_coord[1])**2
                if dist_sq < min_dist_sq:
                    too_close = True
                    break
            if not too_close:
                _vertices.append(new_vertex)
                placed = True
                break
        if not placed:
            # Fallback: just append even if it's too close, or could raise error
            # For this game, it might be okay if some vertices overlap initially.
            # Or, we could implement a more robust placement strategy (e.g., force field, spiral)
            print(f"Warning: Could not place vertex {_ + 1} without being too close. Consider increasing screen or reducing vertices.")
            # _vertices.append(new_vertex) # Decide if we add it anyway or fail
            # If we couldn't place all, the graph might be smaller than requested.
            # For now, let's proceed with what we have, even if fewer than num_vertices.

    # Create a cycle graph: (0,1), (1,2), ..., (n-1,0)
    actual_num_vertices = len(_vertices)
    if actual_num_vertices < MIN_VERTICES: # Should not happen if placement always succeeds for MIN_VERTICES
        print(f"Error: Generated fewer than {MIN_VERTICES} vertices. Aborting or using default.")
        # Fallback to a default simple graph if generation is problematic
        _vertices = [(50,50), (150,50), (100,150)]
        actual_num_vertices = 3

    edges = []
    if actual_num_vertices >= 2: # Need at least 2 vertices for an edge
        for i in range(actual_num_vertices -1):
            edges.append((i, i + 1))
        if actual_num_vertices > 2: # Close the cycle for 3+ vertices
             edges.append((actual_num_vertices - 1, 0))
        # elif actual_num_vertices == 2: # Only one edge for 2 vertices, already added
            # pass

    return _vertices, edges

def draw_graph(screen_surface, graph_verts, graph_edges_list, vert_radius, crossing_edges_param=None):
    """Draws the graph on the screen_surface.
    Edges in crossing_edges_param are drawn in RED_EDGE_CROSSING color.
    Other edges are drawn in GREEN_EDGE_NON_CROSSING color.
    Vertices are drawn in RED_VERTEX color.
    """
    if crossing_edges_param is None:
        crossing_edges_param = set() # Default to empty set if not provided

    for edge_tuple in graph_edges_list: # Renamed 'edge' to 'edge_tuple' for clarity
        start_pos = graph_verts[edge_tuple[0]]
        end_pos = graph_verts[edge_tuple[1]]

        # Determine edge color
        if edge_tuple in crossing_edges_param:
            edge_color = RED_EDGE_CROSSING
        else:
            edge_color = GREEN_EDGE_NON_CROSSING

        pygame.draw.line(screen_surface, edge_color, start_pos, end_pos, 2) # Edge thickness 2

    for vertex_pos in graph_verts:
        pygame.draw.circle(screen_surface, RED_VERTEX, vertex_pos, vert_radius) # Use RED_VERTEX

# --- Geometry Functions (safe for global scope) ---
def on_segment(p, q, r):
    return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
            q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))

def orientation(p, q, r):
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if val == 0: return 0  # Collinear
    return 1 if val > 0 else 2  # Clockwise or Counterclockwise

def do_lines_intersect(p1, q1, p2, q2):
    # Standard line segment intersection check logic
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    if o1 != o2 and o3 != o4:
        return True

    if o1 == 0 and on_segment(p1, p2, q1): return True
    if o2 == 0 and on_segment(p1, q2, q1): return True
    if o3 == 0 and on_segment(p2, p1, q2): return True
    if o4 == 0 and on_segment(p2, q1, q2): return True # p2, q2, q1 are collinear and q1 lies on segment p2q2
    return False # Segments do not intersect

def get_crossing_edges(graph_verts, graph_edges_list):
    """
    Checks for edge crossings in the graph.
    Returns a set of edge tuples that are involved in at least one crossing.
    Edges are stored as the original tuples from graph_edges_list.
    """
    crossing_edges_set = set()
    num_edges = len(graph_edges_list)

    for i in range(num_edges):
        for j in range(i + 1, num_edges):
            edge1_indices = graph_edges_list[i]
            edge2_indices = graph_edges_list[j]

            # Skip if edges share a common vertex
            if (edge1_indices[0] == edge2_indices[0] or
                edge1_indices[0] == edge2_indices[1] or
                edge1_indices[1] == edge2_indices[0] or
                edge1_indices[1] == edge2_indices[1]):
                continue

            p1 = graph_verts[edge1_indices[0]]
            q1 = graph_verts[edge1_indices[1]]
            p2 = graph_verts[edge2_indices[0]]
            q2 = graph_verts[edge2_indices[1]]

            if do_lines_intersect(p1, q1, p2, q2):
                # Add both edges to the set as they are involved in a crossing
                crossing_edges_set.add(edge1_indices)
                crossing_edges_set.add(edge2_indices)

    return crossing_edges_set

# --- Main Game Function ---
def main_game():
    # --- Get user input for number of vertices ---
    # This should happen before pygame.init() if input is via console without a Pygame window active.
    # However, input() will work fine here before the main loop starts.
    num_vertices = get_num_vertices_from_user()

    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Planarity")

    win_font = None
    try:
        win_font = pygame.font.Font(None, 74)
    except Exception as e:
        print(f"Font loading failed in main_game: {e}")

    graph_vertices, graph_edges = generate_random_planar_graph(num_vertices)

    selected_vertex_index = None
    mouse_button_down = False
    crossing_edges_set = get_crossing_edges(graph_vertices, graph_edges) # Store the set of crossing edges

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_button_down = True
                    mouse_x, mouse_y = event.pos
                    for i, (vx, vy) in enumerate(graph_vertices):
                        if ((vx - mouse_x)**2 + (vy - mouse_y)**2)**0.5 < VERTEX_RADIUS:
                            selected_vertex_index = i
                            break
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_button_down = False
                    if selected_vertex_index is not None:
                        crossing_edges_set = get_crossing_edges(graph_vertices, graph_edges) # Update set
                    selected_vertex_index = None
            elif event.type == pygame.MOUSEMOTION:
                if mouse_button_down and selected_vertex_index is not None:
                    mouse_x, mouse_y = event.pos
                    clamped_x = max(VERTEX_RADIUS, min(mouse_x, SCREEN_WIDTH - VERTEX_RADIUS))
                    clamped_y = max(VERTEX_RADIUS, min(mouse_y, SCREEN_HEIGHT - VERTEX_RADIUS))
                    graph_vertices[selected_vertex_index] = (clamped_x, clamped_y)
                    crossing_edges_set = get_crossing_edges(graph_vertices, graph_edges) # Update set

        screen.fill(WHITE)
        # Pass the set of crossing edges to draw_graph
        draw_graph(screen, graph_vertices, graph_edges, VERTEX_RADIUS, crossing_edges_set)

        if not crossing_edges_set and win_font: # Check if the set is empty
            win_text_surface = win_font.render("You Win!", True, WIN_MESSAGE_COLOR)
            text_rect = win_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(win_text_surface, text_rect)

        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main_game()
