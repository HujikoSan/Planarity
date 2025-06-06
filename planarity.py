import pygame
import random
import webbrowser
import urllib.parse

# Screen dimensions (constants)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED_VERTEX = (255, 0, 0)
GREEN_EDGE_NON_CROSSING = (0, 150, 0)
RED_EDGE_CROSSING = (200, 0, 0)
WIN_MESSAGE_COLOR = (0, 128, 0)

# Vertex and Edge data structures
# Vertices: list of (x, y) coordinates
# Edges: list of (vertex_index1, vertex_index2) pairs

# --- Global constants and utility functions that don't initialize Pygame ---
VERTEX_RADIUS = 10

DEFAULT_NUM_VERTICES = 6
MIN_VERTICES = 3
MAX_VERTICES = 20

def get_num_vertices_from_user():
    """Prompts the user for the number of vertices and validates input."""
    num_vertices = DEFAULT_NUM_VERTICES
    try:
        raw_input_str = input(f"Enter the number of vertices ({MIN_VERTICES}-{MAX_VERTICES}, default: {DEFAULT_NUM_VERTICES}): ")
        val = int(raw_input_str)
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
    vertices = []
    edges = []
    min_dist_sq = 50**2
    for i in range(n):
        placed = False
        for _ in range(100):
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
            vertices.append(new_vertex_pos)

    if len(vertices) != n:
        print(f"Error: Only {len(vertices)} out of {n} vertices were generated. Graph may be smaller.")
        n = len(vertices)

    if n == 0: return [], []
    if n == 1: return vertices, []
    if n == 2:
        if len(vertices) == 2: edges.append(tuple(sorted((0,1))))
        return vertices, edges

    v0, v1, v2 = 0, 1, 2
    initial_edges = [tuple(sorted((v0,v1))), tuple(sorted((v1,v2))), tuple(sorted((v2,v0)))]
    edges.extend(initial_edges)
    faces = [(v0, v1, v2)]

    for k in range(3, n):
        if not faces:
            print(f"Error: No faces available to insert vertex {k}. Stopping.")
            break
        face_to_split_idx = random.randrange(len(faces))
        a,b,c = faces.pop(face_to_split_idx)
        v_k = k
        edges.extend([tuple(sorted((v_k,a))), tuple(sorted((v_k,b))), tuple(sorted((v_k,c)))])
        faces.extend([(v_k,a,b), (v_k,b,c), (v_k,c,a)])

    final_edges = list(set(edges))

    if n >= 3:
        min_edges_for_connected = n - 1 if n > 0 else 0
        num_edges_target = int(random.uniform(0.8, 1.0) * len(final_edges))
        num_edges_target = max(min_edges_for_connected, num_edges_target)
        num_to_remove = len(final_edges) - num_edges_target

        if num_to_remove > 0:
            potential_edges_to_remove = list(final_edges)
            random.shuffle(potential_edges_to_remove)
            current_edges_for_check = list(final_edges)
            removed_count = 0
            MIN_DEGREE_TO_ALLOW_REMOVAL = 3

            for edge_candidate in potential_edges_to_remove:
                if removed_count >= num_to_remove or len(current_edges_for_check) <= min_edges_for_connected:
                    break
                u, v = edge_candidate
                degree_u = sum(1 for edge in current_edges_for_check if u in edge)
                degree_v = sum(1 for edge in current_edges_for_check if v in edge)
                if degree_u <= MIN_DEGREE_TO_ALLOW_REMOVAL or degree_v <= MIN_DEGREE_TO_ALLOW_REMOVAL:
                    continue

                if edge_candidate not in current_edges_for_check: continue # Already removed by an earlier operation on a shared vertex? Unlikely with current logic.
                current_edges_for_check.remove(edge_candidate)

                if is_connected(current_edges_for_check, n):
                    removed_count += 1
                else:
                    current_edges_for_check.append(edge_candidate)
            final_edges = current_edges_for_check

    return vertices, final_edges

def is_connected(edges_list, num_vertices):
    if num_vertices == 0: return True
    if num_vertices == 1: return True
    if not edges_list: return False

    adj = [[] for _ in range(num_vertices)]
    for u, v in edges_list:
        adj[u].append(v)
        adj[v].append(u)

    start_node = 0
    q = [start_node]
    visited = {start_node}
    count = 0
    head = 0
    while head < len(q):
        u = q[head]; head += 1; count += 1
        for v_neighbor in adj[u]:
            if v_neighbor not in visited:
                visited.add(v_neighbor); q.append(v_neighbor)
    return count == num_vertices

def draw_graph(screen_surface, graph_verts, graph_edges_list, vert_radius, crossing_edges_param=None):
    if crossing_edges_param is None: crossing_edges_param = set()
    for edge_tuple in graph_edges_list:
        start_pos = graph_verts[edge_tuple[0]]; end_pos = graph_verts[edge_tuple[1]]
        edge_color = RED_EDGE_CROSSING if edge_tuple in crossing_edges_param else GREEN_EDGE_NON_CROSSING
        pygame.draw.line(screen_surface, edge_color, start_pos, end_pos, 2)
    for vertex_pos in graph_verts:
        pygame.draw.circle(screen_surface, RED_VERTEX, vertex_pos, vert_radius)

def on_segment(p,q,r): return (q[0]<=max(p[0],r[0]) and q[0]>=min(p[0],r[0]) and q[1]<=max(p[1],r[1]) and q[1]>=min(p[1],r[1]))
def orientation(p,q,r): val=(q[1]-p[1])*(r[0]-q[0])-(q[0]-p[0])*(r[1]-q[1]); return 0 if val==0 else (1 if val>0 else 2)
def do_lines_intersect(p1,q1,p2,q2):
    o1=orientation(p1,q1,p2); o2=orientation(p1,q1,q2); o3=orientation(p2,q2,p1); o4=orientation(p2,q2,q1)
    if o1!=o2 and o3!=o4: return True
    if o1==0 and on_segment(p1,p2,q1): return True;
    if o2==0 and on_segment(p1,q2,q1): return True
    if o3==0 and on_segment(p2,p1,q2): return True;
    if o4==0 and on_segment(p2,q1,q2): return True
    return False

def get_crossing_edges(graph_verts, graph_edges_list):
    crossing_edges_set = set(); num_edges = len(graph_edges_list)
    for i in range(num_edges):
        for j in range(i + 1, num_edges):
            e1_idx,e2_idx = graph_edges_list[i],graph_edges_list[j]
            # Check if edges share a common vertex more directly
            if e1_idx[0] == e2_idx[0] or e1_idx[0] == e2_idx[1] or \
               e1_idx[1] == e2_idx[0] or e1_idx[1] == e2_idx[1]:
                continue
            p1,q1=graph_verts[e1_idx[0]],graph_verts[e1_idx[1]]
            p2,q2=graph_verts[e2_idx[0]],graph_verts[e2_idx[1]]
            if do_lines_intersect(p1,q1,p2,q2):
                crossing_edges_set.add(e1_idx); crossing_edges_set.add(e2_idx)
    return crossing_edges_set

def main_game_session(screen, common_win_font, common_stats_font, fixed_num_vertices=None):
    if fixed_num_vertices is not None: num_vertices_this_session = fixed_num_vertices
    else: num_vertices_this_session = get_num_vertices_from_user()

    graph_vertices, graph_edges = generate_random_planar_graph(num_vertices_this_session)
    selected_vertex_index = None; mouse_button_down = False
    crossing_edges_set = get_crossing_edges(graph_vertices, graph_edges)
    start_time = pygame.time.get_ticks(); elapsed_time_seconds = 0.0
    game_won = False; is_paused = False; pause_start_ticks = 0

    retry_button_rect, retry_same_button_rect, post_to_x_button_rect = None, None, None
    pause_reset_button_rect, pause_quit_button_rect, resume_button_rect = None, None, None
    pause_button_rect = pygame.Rect(10, 10, 85, 30)

    new_game_text = common_stats_font.render("New Game", True, BLACK) if common_stats_font else None
    retry_same_text = common_stats_font.render("Retry Same Level", True, BLACK) if common_stats_font else None
    post_to_x_text = common_stats_font.render("Post to X", True, BLACK) if common_stats_font else None
    paused_title_text = common_win_font.render("Paused", True, BLACK) if common_win_font else None
    resume_text = common_stats_font.render("Resume", True, BLACK) if common_stats_font else None
    reset_level_text = common_stats_font.render("Reset Level", True, BLACK) if common_stats_font else None
    quit_to_menu_text = common_stats_font.render("Quit to Menu", True, BLACK) if common_stats_font else None

    transparent_pause_button_surface = None
    if common_stats_font:
        game_pause_text_render = common_stats_font.render("Pause", True, BLACK)
        if game_pause_text_render:
            transparent_pause_button_surface = pygame.Surface(pause_button_rect.size, pygame.SRCALPHA)
            transparent_pause_button_surface.fill((220, 220, 220, 180))
            text_r = game_pause_text_render.get_rect(center=(pause_button_rect.width//2, pause_button_rect.height//2))
            transparent_pause_button_surface.blit(game_pause_text_render, text_r)
            pygame.draw.rect(transparent_pause_button_surface, BLACK, transparent_pause_button_surface.get_rect(), 1)

    running_session = True
    while running_session:
        current_ticks = pygame.time.get_ticks()
        if not game_won and not is_paused: elapsed_time_seconds = (current_ticks - start_time) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT", None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    if game_won:
                        if retry_button_rect and retry_button_rect.collidepoint(event.pos): return "RESTART", None
                        elif retry_same_button_rect and retry_same_button_rect.collidepoint(event.pos): return "RESTART_SAME", num_vertices_this_session
                        elif post_to_x_button_rect and post_to_x_button_rect.collidepoint(event.pos):
                            tweet = f"I solved a Planarity puzzle with {num_vertices_this_session}V & {len(graph_edges)}E in {elapsed_time_seconds:.1f}s! #PlanarityGame"
                            webbrowser.open_new_tab(f"https://x.com/intent/post?text={urllib.parse.quote(tweet)}")
                    elif is_paused:
                        if resume_button_rect and resume_button_rect.collidepoint(event.pos):
                            is_paused = False; start_time += current_ticks - pause_start_ticks
                        elif pause_reset_button_rect and pause_reset_button_rect.collidepoint(event.pos): return "RESTART_SAME", num_vertices_this_session
                        elif pause_quit_button_rect and pause_quit_button_rect.collidepoint(event.pos): return "RESTART", None
                    elif not game_won: # Active gameplay
                        mouse_button_down = True; mouse_x, mouse_y = event.pos
                        for i,(vx,vy) in enumerate(graph_vertices):
                            if ((vx-mouse_x)**2+(vy-mouse_y)**2)**0.5 < VERTEX_RADIUS: selected_vertex_index=i; break
                elif event.button == 3: # Right click
                    if not is_paused and not game_won and pause_button_rect.collidepoint(event.pos):
                        is_paused = True; pause_start_ticks = current_ticks
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_button_down = False
                if not game_won and not is_paused and selected_vertex_index is not None:
                    crossing_edges_set = get_crossing_edges(graph_vertices, graph_edges)
                selected_vertex_index = None
            elif event.type == pygame.MOUSEMOTION:
                if not game_won and not is_paused and mouse_button_down and selected_vertex_index is not None:
                    mx,my=event.pos; graph_vertices[selected_vertex_index]=(max(VERTEX_RADIUS,min(mx,SCREEN_WIDTH-VERTEX_RADIUS)),max(VERTEX_RADIUS,min(my,SCREEN_HEIGHT-VERTEX_RADIUS)))
                    crossing_edges_set = get_crossing_edges(graph_vertices, graph_edges)

        screen.fill(WHITE); draw_graph(screen, graph_vertices, graph_edges, VERTEX_RADIUS, crossing_edges_set)

        if not game_won and not is_paused and not crossing_edges_set:
            game_won = True
            # Define win screen button rects ONCE when game is won. Positions will be set in drawing.
            # Widths are based on pre-rendered text, heights are standard.
            btn_std_h = 40; btn_std_s = 10
            w_ng = new_game_text.get_width() + 30 if new_game_text else 200
            w_rs = retry_same_text.get_width() + 30 if retry_same_text else 200
            w_px = post_to_x_text.get_width() + 30 if post_to_x_text else 200

            retry_button_rect = pygame.Rect(0, 0, w_ng, btn_std_h)
            retry_same_button_rect = pygame.Rect(0, 0, w_rs, btn_std_h)
            post_to_x_button_rect = pygame.Rect(0, 0, w_px, btn_std_h)


        if game_won:
            # --- Layout Constants for Win Screen ---
            TITLE_FONT_HEIGHT = common_win_font.get_height() if common_win_font else 60
            STATS_FONT_HEIGHT = common_stats_font.get_height() if common_stats_font else 30
            BUTTON_HEIGHT = 40
            SPACE_AFTER_TITLE = 15
            SPACE_AFTER_STAT_LINE = 5
            SPACE_BEFORE_BUTTONS = 25
            SPACE_BETWEEN_BUTTONS = 10

            # Prepare rendered surfaces for messages
            win_msg_surfaces = []
            if common_win_font: win_msg_surfaces.append(common_win_font.render("You Win!", True, WIN_MESSAGE_COLOR))
            stats_to_display = [
                f"Vertices: {num_vertices_this_session}",
                f"Edges: {len(graph_edges)}",
                f"Time: {elapsed_time_seconds:.1f} seconds"
            ]
            if common_stats_font:
                for stat_text in stats_to_display:
                    win_msg_surfaces.append(common_stats_font.render(stat_text, True, WIN_MESSAGE_COLOR))

            # Prepare button data
            buttons_data = []
            if new_game_text: buttons_data.append({'surface': new_game_text, 'rect': retry_button_rect, 'color': (200,200,200)})
            if retry_same_text: buttons_data.append({'surface': retry_same_text, 'rect': retry_same_button_rect, 'color': (200,200,200)})
            if post_to_x_text: buttons_data.append({'surface': post_to_x_text, 'rect': post_to_x_button_rect, 'color': (180,180,220)})

            # Calculate total height
            total_content_h = 0
            if win_msg_surfaces:
                total_content_h += TITLE_FONT_HEIGHT + SPACE_AFTER_TITLE
                total_content_h += (len(stats_to_display) * STATS_FONT_HEIGHT) + (max(0, len(stats_to_display)-1) * SPACE_AFTER_STAT_LINE)
            if buttons_data:
                total_content_h += SPACE_BEFORE_BUTTONS
                total_content_h += len(buttons_data) * BUTTON_HEIGHT
                total_content_h += max(0, len(buttons_data)-1) * SPACE_BETWEEN_BUTTONS

            current_y_top = SCREEN_HEIGHT // 2 - total_content_h // 2

            # Render messages
            if win_msg_surfaces:
                title_surf = win_msg_surfaces[0]
                title_r = title_surf.get_rect(center=(SCREEN_WIDTH//2, current_y_top + title_surf.get_height()//2))
                screen.blit(title_surf, title_r)
                current_y_top += title_surf.get_height() + SPACE_AFTER_TITLE

                for i in range(1, len(win_msg_surfaces)):
                    stat_surf = win_msg_surfaces[i]
                    stat_r = stat_surf.get_rect(center=(SCREEN_WIDTH//2, current_y_top + stat_surf.get_height()//2))
                    screen.blit(stat_surf, stat_r)
                    current_y_top += stat_surf.get_height() + SPACE_AFTER_STAT_LINE

            current_y_top += SPACE_BEFORE_BUTTONS - SPACE_AFTER_STAT_LINE # Adjust as last stat_line added extra space

            # Render buttons
            for btn in buttons_data:
                btn['rect'].centerx = SCREEN_WIDTH // 2
                btn['rect'].top = current_y_top
                pygame.draw.rect(screen, btn['color'], btn['rect'])
                pygame.draw.rect(screen, BLACK, btn['rect'], 2)
                screen.blit(btn['surface'], btn['surface'].get_rect(center=btn['rect'].center))
                current_y_top += BUTTON_HEIGHT + SPACE_BETWEEN_BUTTONS

        if not game_won and not is_paused and common_stats_font:
            screen.blit(common_stats_font.render(f"Time: {elapsed_time_seconds:.1f}",True,BLACK),(10,50))
            if transparent_pause_button_surface: screen.blit(transparent_pause_button_surface,pause_button_rect.topleft)

        if is_paused:
            ovl=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA); ovl.fill((0,0,0,180)); screen.blit(ovl,(0,0))
            y_start=SCREEN_HEIGHT//2-100 # Adjusted for potentially 3 buttons + title
            btn_w,btn_h,btn_s = 180,50,15
            if paused_title_text: screen.blit(paused_title_text,paused_title_text.get_rect(center=(SCREEN_WIDTH//2,y_start))); y_start+=60

            # Resume Button
            if resume_text:
                resume_button_rect=pygame.Rect(SCREEN_WIDTH//2-btn_w//2,y_start,btn_w,btn_h); pygame.draw.rect(screen,(200,200,200),resume_button_rect); pygame.draw.rect(screen,BLACK,resume_button_rect,2)
                screen.blit(resume_text,resume_text.get_rect(center=resume_button_rect.center)); y_start+=btn_h+btn_s
            # Reset Level Button
            if reset_level_text:
                pause_reset_button_rect=pygame.Rect(SCREEN_WIDTH//2-btn_w//2,y_start,btn_w,btn_h); pygame.draw.rect(screen,(200,200,200),pause_reset_button_rect); pygame.draw.rect(screen,BLACK,pause_reset_button_rect,2)
                screen.blit(reset_level_text,reset_level_text.get_rect(center=pause_reset_button_rect.center)); y_start+=btn_h+btn_s
            # Quit to Menu Button
            if quit_to_menu_text:
                pause_quit_button_rect=pygame.Rect(SCREEN_WIDTH//2-btn_w//2,y_start,btn_w,btn_h); pygame.draw.rect(screen,(200,200,200),pause_quit_button_rect); pygame.draw.rect(screen,BLACK,pause_quit_button_rect,2)
                screen.blit(quit_to_menu_text,quit_to_menu_text.get_rect(center=pause_quit_button_rect.center))
        pygame.display.flip()
    return "QUIT", None

def main_application():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Planarity")
    win_font, stats_font = None, None
    try: win_font = pygame.font.Font(None, 74); stats_font = pygame.font.Font(None, 36)
    except Exception as e: print(f"Font loading failed: {e}")
    fixed_n = None
    while True:
        status, data = main_game_session(screen, win_font, stats_font, fixed_num_vertices=fixed_n)
        if status == "QUIT": break
        elif status == "RESTART": fixed_n = None
        elif status == "RESTART_SAME": fixed_n = data
    pygame.quit()

if __name__ == '__main__':
    main_application()
