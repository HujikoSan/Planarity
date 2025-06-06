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

def generate_random_planar_graph(n): # n is num_vertices
    """
    Generates a random planar graph, starting with a triangulation.
    For n < 3, generates specific simple graphs.
    For n >= 3, generates a triangulation using incremental face splitting.
    Returns: list of vertex (x,y) coordinates, list of edge (idx1, idx2) tuples.
    """
    vertices = []
    edges = []

    # --- Vertex Placement ---
    min_dist_sq = 50**2
    for i in range(n):
        placed = False
        for _ in range(100): # Max attempts to find a spot
            new_vertex_pos = (random.randint(VERTEX_RADIUS, SCREEN_WIDTH - VERTEX_RADIUS),
                              random.randint(VERTEX_RADIUS, SCREEN_HEIGHT - VERTEX_RADIUS))
            too_close = False
            for v_pos in vertices:
                dist_sq = (new_vertex_pos[0] - v_pos[0])**2 + (new_vertex_pos[1] - v_pos[1])**2
                if dist_sq < min_dist_sq:
                    too_close = True
                    break
            if not too_close:
                vertices.append(new_vertex_pos)
                placed = True
                break
        if not placed:
            print(f"Warning: Could not place vertex {i+1} ideally. Appending possibly overlapping vertex.")
            vertices.append(new_vertex_pos) # Add it anyway for now

    if len(vertices) != n:
        # This case should ideally not be reached if placement always succeeds or appends.
        # If it does, it means some vertices failed to be added even as a fallback.
        print(f"Error: Only {len(vertices)} out of {n} vertices were generated. Graph may be smaller.")
        n = len(vertices) # Adjust n to actual number of vertices

    # --- Edge Generation ---
    # Base Cases for n < 3
    if n == 0:
        return [], []
    if n == 1:
        # vertices list is already populated if n=1
        return vertices, []
    if n == 2:
        # vertices list populated
        if len(vertices) == 2: # Ensure we have 2 vertices
             edges.append(tuple(sorted((0,1))))
        return vertices, edges

    # Triangulation for n >= 3
    # Ensure canonical edge representation (min_idx, max_idx) to simplify set operations if needed later
    # and to avoid duplicate edges like (0,1) and (1,0) if not careful.

    # Initial triangle (v0, v1, v2)
    # Sort indices to ensure canonical form for edges
    v0, v1, v2 = 0, 1, 2
    initial_edges = [
        tuple(sorted((v0, v1))),
        tuple(sorted((v1, v2))),
        tuple(sorted((v2, v0)))
    ]
    edges.extend(initial_edges)

    # List of faces, where each face is a tuple of 3 vertex indices
    # For now, we only care about the internal faces for triangulation
    faces = [(v0, v1, v2)] # Represents the initial triangle face

    # Incremental triangulation: add vertices v_k from k=3 to n-1
    for k in range(3, n):
        if not faces:
            # This should not happen in a proper triangulation process
            print(f"Error: No faces available to insert vertex {k}. Stopping triangulation early.")
            break

        # Pick a random face to insert the new vertex v_k into
        face_to_split_idx = random.randrange(len(faces))
        a, b, c = faces.pop(face_to_split_idx) # Remove the chosen face

        v_k = k # The new vertex being added

        # Add 3 new edges connecting v_k to the vertices of the chosen face
        edges.append(tuple(sorted((v_k, a))))
        edges.append(tuple(sorted((v_k, b))))
        edges.append(tuple(sorted((v_k, c))))

        # Add 3 new faces formed by v_k and the edges of the old face
        faces.append((v_k, a, b))
        faces.append((v_k, b, c))
        faces.append((v_k, c, a))
        # Note: The order of vertices in face tuples (a,b,c) might matter for strict geometric
        # interpretations (e.g., winding order), but for tracking connectivity to split faces,
        # it's mainly about having the three vertices.

    # Remove duplicate edges if any were accidentally created (e.g. if face list wasn't managed perfectly)
    # Using tuple(sorted(...)) for edges already helps prevent (0,1) and (1,0) type duplicates.
    # A set conversion can remove exact duplicates if the list construction had issues.
    # However, the described algorithm for triangulation shouldn't produce duplicates if faces are managed correctly.
    # For now, we assume the list `edges` is correct as generated.

    final_edges = list(set(edges)) # Ensure unique edges from triangulation

    # --- Edge Removal to make the graph not necessarily a full triangulation ---
    if n >= 3: # Only apply removal if we started with a triangulation
        min_edges_for_connected = n - 1 if n > 0 else 0

        # Target between 80% and 100% of the triangulation edges, but not less than n-1
        # len(final_edges) is effectively 3n-6 for n>=3 at this point
        num_edges_target = int(random.uniform(0.8, 1.0) * len(final_edges))
        num_edges_target = max(min_edges_for_connected, num_edges_target)

        num_to_remove = len(final_edges) - num_edges_target

        if num_to_remove > 0:
            # Create a list of edges to consider for removal, shuffle it
            potential_edges_to_remove = list(final_edges) # Operate on a copy
            random.shuffle(potential_edges_to_remove)

            current_edges_for_check = list(final_edges) # Start with all triangulation edges

            removed_count = 0
            MIN_DEGREE_TO_ALLOW_REMOVAL = 3 # Edge can be removed only if endpoint degrees are > 3

            for edge_candidate in potential_edges_to_remove:
                if removed_count >= num_to_remove:
                    break # Removed enough edges

                if len(current_edges_for_check) <= min_edges_for_connected: # Safety break
                    break

                # Check if this edge is still in the graph (it might have been added back and then re-selected)
                # This check is implicitly handled if current_edges_for_check.remove(edge_candidate) raises ValueError,
                # but explicit check is safer if potential_edges_to_remove contains duplicates or stale entries.
                # However, potential_edges_to_remove is a shuffled copy of initial final_edges.
                # An edge is only processed once from potential_edges_to_remove.
                # If it's put back, it's into current_edges_for_check, not potential_edges_to_remove. So this is fine.

                u, v = edge_candidate

                # Calculate current degrees of u and v based on current_edges_for_check
                degree_u = sum(1 for edge in current_edges_for_check if u in edge)
                degree_v = sum(1 for edge in current_edges_for_check if v in edge)

                # Apply Degree Constraint:
                # If removing this edge would make degree_u or degree_v <= 2 (i.e. current degree is <=3)
                # then this edge cannot be removed.
                if degree_u <= MIN_DEGREE_TO_ALLOW_REMOVAL or degree_v <= MIN_DEGREE_TO_ALLOW_REMOVAL:
                    continue # Skip to the next candidate edge

                # Try removing the edge (if degree constraint passes)
                current_edges_for_check.remove(edge_candidate)

                if is_connected(current_edges_for_check, n):
                    # Removal is successful (maintains connectivity and degree constraint met)
                    removed_count += 1
                else:
                    # Removal failed (disconnected graph), add it back
                    current_edges_for_check.append(edge_candidate)

            final_edges = current_edges_for_check

    return vertices, final_edges


# --- Connectivity Check (BFS) ---
def is_connected(edges_list, num_vertices):
    if num_vertices == 0:
        return True
    if not edges_list and num_vertices > 1: # No edges but multiple vertices
        return False
    if num_vertices == 1 and not edges_list: # Single vertex is connected
        return True


    adj = [[] for _ in range(num_vertices)]
    has_edges = False
    for u, v in edges_list:
        adj[u].append(v)
        adj[v].append(u)
        has_edges = True

    if not has_edges: # No edges in the list
        return num_vertices <= 1 # Connected if 0 or 1 vertex, disconnected otherwise

    # Start BFS from vertex 0 (assuming vertices are 0 to num_vertices-1)
    # Vertex 0 is guaranteed to exist if num_vertices > 0.
    # If vertex 0 is isolated but other components exist, BFS won't visit all.
    start_node = 0
    q = [start_node]
    visited = {start_node}
    count = 0

    head = 0
    while head < len(q):
        u = q[head]
        head += 1
        count += 1
        for v_neighbor in adj[u]:
            if v_neighbor not in visited:
                visited.add(v_neighbor)
                q.append(v_neighbor)

    return count == num_vertices


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

# --- Main Game Session Function ---
def main_game_session(screen, num_vertices, common_win_font, common_stats_font):
    graph_vertices, graph_edges = generate_random_planar_graph(num_vertices)

    selected_vertex_index = None
    mouse_button_down = False
    crossing_edges_set = get_crossing_edges(graph_vertices, graph_edges)

    start_time = pygame.time.get_ticks()
    elapsed_time_seconds = 0.0
    game_won = False
    is_paused = False
    pause_start_ticks = 0

    # Button Rects - will be defined dynamically when needed
    retry_button_rect = None
    pause_reset_button_rect = None
    pause_quit_button_rect = None

    # Pre-render static text surfaces if fonts are available
    retry_button_text_surface = common_stats_font.render("Retry", True, BLACK) if common_stats_font else None
    paused_text_surface = common_win_font.render("Paused", True, BLACK) if common_win_font else None
    pause_reset_text_surface = common_stats_font.render("Reset", True, BLACK) if common_stats_font else None
    pause_quit_text_surface = common_stats_font.render("Quit", True, BLACK) if common_stats_font else None

    running_session = True
    while running_session:
        current_ticks = pygame.time.get_ticks()

        if not game_won and not is_paused:
            elapsed_time_seconds = (current_ticks - start_time) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    is_paused = not is_paused
                    if is_paused:
                        pause_start_ticks = current_ticks
                    else: # Resuming
                        pause_duration = current_ticks - pause_start_ticks
                        start_time += pause_duration

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    if game_won and retry_button_rect and retry_button_rect.collidepoint(event.pos):
                        return "RESTART"

                    if is_paused:
                        if pause_reset_button_rect and pause_reset_button_rect.collidepoint(event.pos):
                            return "RESTART"
                        if pause_quit_button_rect and pause_quit_button_rect.collidepoint(event.pos):
                            return "QUIT"
                    elif not game_won: # Only process game clicks if not paused and not won
                        mouse_button_down = True
                        mouse_x, mouse_y = event.pos
                        for i, (vx, vy) in enumerate(graph_vertices):
                            if ((vx - mouse_x)**2 + (vy - mouse_y)**2)**0.5 < VERTEX_RADIUS:
                                selected_vertex_index = i
                                break
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_button_down = False # Always release mouse button
                    if not game_won and not is_paused and selected_vertex_index is not None:
                        crossing_edges_set = get_crossing_edges(graph_vertices, graph_edges)
                    # Deselect regardless of pause/win state if mouse is up
                    selected_vertex_index = None
            elif event.type == pygame.MOUSEMOTION:
                if not game_won and not is_paused and mouse_button_down and selected_vertex_index is not None:
                    mouse_x, mouse_y = event.pos
                    clamped_x = max(VERTEX_RADIUS, min(mouse_x, SCREEN_WIDTH - VERTEX_RADIUS))
                    clamped_y = max(VERTEX_RADIUS, min(mouse_y, SCREEN_HEIGHT - VERTEX_RADIUS))
                    graph_vertices[selected_vertex_index] = (clamped_x, clamped_y)
                    crossing_edges_set = get_crossing_edges(graph_vertices, graph_edges)

        screen.fill(WHITE)
        draw_graph(screen, graph_vertices, graph_edges, VERTEX_RADIUS, crossing_edges_set)

        if not game_won and not is_paused and not crossing_edges_set: # Game just won
            game_won = True
            # Define retry button properties here, once game is won
            if retry_button_text_surface:
                button_width = retry_button_text_surface.get_width() + 40
                button_height = retry_button_text_surface.get_height() + 20
                button_y = SCREEN_HEIGHT // 2 + 2*45 + 30
                retry_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, button_y, button_width, button_height)

        if game_won: # Display Win Message, Stats, and Retry Button
            win_messages = [
                "You Win!",
                f"Vertices: {len(graph_vertices)}",
                f"Edges: {len(graph_edges)}",
                f"Time: {elapsed_time_seconds:.1f} seconds"
            ]
            current_y = SCREEN_HEIGHT // 2 - (len(win_messages) * 40 + (retry_button_text_surface.get_height() + 20 if retry_button_text_surface else 0)) // 2

            for i, msg in enumerate(win_messages):
                font_to_use = common_win_font if i == 0 else common_stats_font
                if not font_to_use: continue
                text_surface = font_to_use.render(msg, True, WIN_MESSAGE_COLOR)
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, current_y))
                screen.blit(text_surface, text_rect)
                current_y += 45

            if retry_button_rect and retry_button_text_surface: # retry_button_rect is defined when game_won becomes true
                pygame.draw.rect(screen, (200, 200, 200), retry_button_rect)
                pygame.draw.rect(screen, BLACK, retry_button_rect, 2)
                text_rect = retry_button_text_surface.get_rect(center=retry_button_rect.center)
                screen.blit(retry_button_text_surface, text_rect)

        if not game_won and not is_paused and common_stats_font: # Live timer
            timer_surface = common_stats_font.render(f"Time: {elapsed_time_seconds:.1f}", True, BLACK)
            screen.blit(timer_surface, (10, 10))

        if is_paused:
            overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay_surface.fill((0, 0, 0, 180)) # Semi-transparent black
            screen.blit(overlay_surface, (0,0))

            if paused_text_surface:
                paused_rect = paused_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
                screen.blit(paused_text_surface, paused_rect)

            button_width_pause = 150
            button_height_pause = 50

            # Reset button
            if pause_reset_text_surface:
                pause_reset_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width_pause // 2, SCREEN_HEIGHT // 2, button_width_pause, button_height_pause)
                pygame.draw.rect(screen, (200,200,200), pause_reset_button_rect)
                pygame.draw.rect(screen, BLACK, pause_reset_button_rect, 2)
                reset_text_rect = pause_reset_text_surface.get_rect(center=pause_reset_button_rect.center)
                screen.blit(pause_reset_text_surface, reset_text_rect)

            # Quit button
            if pause_quit_text_surface:
                pause_quit_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width_pause // 2, SCREEN_HEIGHT // 2 + 70, button_width_pause, button_height_pause)
                pygame.draw.rect(screen, (200,200,200), pause_quit_button_rect)
                pygame.draw.rect(screen, BLACK, pause_quit_button_rect, 2)
                quit_text_rect = pause_quit_text_surface.get_rect(center=pause_quit_button_rect.center)
                screen.blit(pause_quit_text_surface, quit_text_rect)

        pygame.display.flip()

    return "QUIT" # Default action if loop exits unexpectedly


# --- Main Application Runner ---
def main_application():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Planarity")

    win_font, stats_font = None, None
    try:
        win_font = pygame.font.Font(None, 74)
        stats_font = pygame.font.Font(None, 36)
    except Exception as e:
        print(f"Font loading failed: {e}")
        # Game can still run without fonts, just won't display text

    while True:
        num_vertices = get_num_vertices_from_user()
        action = main_game_session(screen, num_vertices, win_font, stats_font)
        if action == "QUIT":
            break

    pygame.quit()


if __name__ == '__main__':
    main_application()
