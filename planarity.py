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
    num_vertices = DEFAULT_NUM_VERTICES
    try:
        raw_input_str = input(f"Enter # vertices ({MIN_VERTICES}-{MAX_VERTICES}, def: {DEFAULT_NUM_VERTICES}): ")
        val = int(raw_input_str)
        if MIN_VERTICES <= val <= MAX_VERTICES: num_vertices = val
        else: print(f"Input out of range. Using default: {DEFAULT_NUM_VERTICES}.")
    except ValueError: print(f"Invalid input. Using default: {DEFAULT_NUM_VERTICES}.")
    except EOFError: print(f"No input (EOF). Using default: {DEFAULT_NUM_VERTICES}.")
    return num_vertices

def generate_random_planar_graph(n):
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
                if ((new_vertex_pos[0]-v_pos[0])**2 + (new_vertex_pos[1]-v_pos[1])**2) < min_dist_sq:
                    too_close = True; break
            if not too_close: vertices.append(new_vertex_pos); placed = True; break
        if not placed: vertices.append(new_vertex_pos) # Add anyway if no ideal spot

    if len(vertices) != n: n = len(vertices)

    if n == 0: return [], []
    if n == 1: return vertices, []
    if n == 2:
        if len(vertices) == 2: edges.append(tuple(sorted((0,1))))
        return vertices, edges

    v0,v1,v2 = 0,1,2; initial_edges=[tuple(sorted((v0,v1))),tuple(sorted((v1,v2))),tuple(sorted((v2,v0)))]
    edges.extend(initial_edges); faces = [(v0,v1,v2)]

    for k in range(3,n):
        if not faces: break
        a,b,c = faces.pop(random.randrange(len(faces)))
        edges.extend([tuple(sorted((k,a))),tuple(sorted((k,b))),tuple(sorted((k,c)))])
        faces.extend([(k,a,b),(k,b,c),(k,c,a)])

    final_edges = list(set(edges))
    if n >= 3:
        min_conn = n-1 if n>0 else 0; target_edges = max(min_conn, int(random.uniform(0.8,1.0)*len(final_edges)))
        to_remove = len(final_edges) - target_edges
        if to_remove > 0:
            shuffled_edges = list(final_edges); random.shuffle(shuffled_edges)
            current_graph_edges = list(final_edges); removed_count = 0
            for edge_cand in shuffled_edges:
                if removed_count >= to_remove or len(current_graph_edges) <= min_conn: break
                u,v = edge_cand
                deg_u = sum(1 for e in current_graph_edges if u in e)
                deg_v = sum(1 for e in current_graph_edges if v in e)
                if deg_u<=3 or deg_v<=3: continue
                if edge_cand not in current_graph_edges: continue
                current_graph_edges.remove(edge_cand)
                if is_connected(current_graph_edges,n): removed_count+=1
                else: current_graph_edges.append(edge_cand)
            final_edges = current_graph_edges
    return vertices, final_edges

def is_connected(edges_list,num_vertices):
    if num_vertices<=1: return True;
    if not edges_list: return False
    adj=[[] for _ in range(num_vertices)];
    for u,v in edges_list: adj[u].append(v); adj[v].append(u)
    q=[0]; visited={0}; count=0; head=0
    while head<len(q):
        u=q[head]; head+=1; count+=1
        for v_neighbor in adj[u]:
            if v_neighbor not in visited: visited.add(v_neighbor); q.append(v_neighbor)
    return count == num_vertices

def capture_game_view(screen_w_param, screen_h_param, bg_color,
                        verts_param, edges_param,
                        cross_set_param, vert_radius_param,
                        vertex_clr_param, crossing_edge_clr_param, non_crossing_edge_clr_param,
                        num_v_stat, num_e_stat, elapsed_t_stat, # New parameters for stats
                        filename="planarity_screenshot.png"):
    """
    Creates an image of the current graph view (vertices, edges, and stats)
    and saves it to a file.
    """
    capture_surface = pygame.Surface((screen_w_param, screen_h_param))
    capture_surface.fill(bg_color)

    # Draw edges
    for edge_tuple in edges_param:
        if not (0 <= edge_tuple[0] < len(verts_param) and 0 <= edge_tuple[1] < len(verts_param)):
            # print(f"Warning: Edge {edge_tuple} has out-of-bounds vertex indices for screenshot. Skipping.") # Optional debug
            continue
        start_pos = verts_param[edge_tuple[0]]
        end_pos = verts_param[edge_tuple[1]]

        edge_color = crossing_edge_clr_param if edge_tuple in cross_set_param else non_crossing_edge_clr_param
        pygame.draw.line(capture_surface, edge_color, start_pos, end_pos, 2)

    # Draw vertices
    for vertex_pos in verts_param:
        pygame.draw.circle(capture_surface, vertex_clr_param, vertex_pos, vert_radius_param)

    # Draw stats text
    stats_capture_font = None
    try:
        stats_capture_font = pygame.font.Font(None, 24) # Small font for stats
    except Exception as e:
        print(f"Failed to load font for screenshot stats: {e}")

    if stats_capture_font:
        texts_to_render = [
            f"Vertices: {num_v_stat}",
            f"Edges: {num_e_stat}",
            f"Time: {elapsed_t_stat:.1f}s"
        ]
        line_height = stats_capture_font.get_height() + 2 # +2 for a little padding
        current_y_text = 5 # Start 5 pixels from the top
        for text_str in texts_to_render:
            text_surface = stats_capture_font.render(text_str, True, BLACK) # Black text for stats
            capture_surface.blit(text_surface, (5, current_y_text)) # 5 pixels from the left
            current_y_text += line_height

    try:
        pygame.image.save(capture_surface, filename)
        print(f"Screenshot saved to {filename}")
        return filename
    except Exception as e:
        print(f"Error saving screenshot: {e}")
        return None

def draw_graph(screen_s, g_verts, g_edges, v_rad, cross_s=None):
    if cross_s is None: cross_s=set()
    for e_tpl in g_edges:
        sp,ep=g_verts[e_tpl[0]],g_verts[e_tpl[1]]
        e_clr = RED_EDGE_CROSSING if e_tpl in cross_s else GREEN_EDGE_NON_CROSSING
        pygame.draw.line(screen_s,e_clr,sp,ep,2)
    for vp in g_verts: pygame.draw.circle(screen_s,RED_VERTEX,vp,v_rad)

def on_segment(p,q,r): return (q[0]<=max(p[0],r[0]) and q[0]>=min(p[0],r[0]) and q[1]<=max(p[1],r[1]) and q[1]>=min(p[1],r[1]))
def orientation(p,q,r): val=(q[1]-p[1])*(r[0]-q[0])-(q[0]-p[0])*(r[1]-q[1]); return 0 if val==0 else (1 if val>0 else 2)
def do_lines_intersect(p1,q1,p2,q2):
    o1 = orientation(p1,q1,p2)
    o2 = orientation(p1,q1,q2)
    o3 = orientation(p2,q2,p1)
    o4 = orientation(p2,q2,q1)

    if o1!=o2 and o3!=o4:
        return True

    # Special Cases for collinear points.
    # on_segment(p,q,r) checks if point q lies on segment pr.
    if o1==0 and on_segment(p1,p2,q1): # p1, q1, p2 are collinear and p2 lies on segment p1q1
        return True
    if o2==0 and on_segment(p1,q2,q1): # p1, q1, q2 are collinear and q2 lies on segment p1q1
        return True
    if o3==0 and on_segment(p2,p1,q2): # p2, q2, p1 are collinear and p1 lies on segment p2q2
        return True
    if o4==0 and on_segment(p2,q1,q2): # p2, q2, q1 are collinear and q1 lies on segment p2q2
        return True

    return False

def get_crossing_edges(g_verts, g_edges):
    cross_set=set(); n_edges=len(g_edges)
    for i in range(n_edges):
        for j in range(i+1,n_edges):
            e1,e2=g_edges[i],g_edges[j]
            if e1[0]==e2[0] or e1[0]==e2[1] or e1[1]==e2[0] or e1[1]==e2[1]: continue
            p1,q1=g_verts[e1[0]],g_verts[e1[1]]; p2,q2=g_verts[e2[0]],g_verts[e2[1]]
            if do_lines_intersect(p1,q1,p2,q2): cross_set.add(e1); cross_set.add(e2)
    return cross_set

def main_game_session(screen, win_fnt, stats_fnt, fixed_n_v=None):
    n_v_sess = fixed_n_v if fixed_n_v is not None else get_num_vertices_from_user()
    g_v, g_e = generate_random_planar_graph(n_v_sess)
    sel_v_idx, m_down = None,False; cross_set = get_crossing_edges(g_v,g_e)
    s_time, elap_s = pygame.time.get_ticks(),0.0; g_won,paused,p_s_ticks = False,False,0
    scr_msg_until, scr_msg_surf = 0,None

    r_btn_r,rs_btn_r,px_btn_r,cap_btn_r,pr_btn_r,pq_btn_r,res_btn_r = [None]*7
    pause_btn_r = pygame.Rect(10,10,85,30)

    # Pre-render text surfaces
    ng_txt = stats_fnt.render("New Game", True, BLACK) if stats_fnt else None
    rs_txt = stats_fnt.render("Retry Same Level", True, BLACK) if stats_fnt else None
    px_txt = stats_fnt.render("Post to X", True, BLACK) if stats_fnt else None
    cap_txt = stats_fnt.render("Capture View", True, BLACK) if stats_fnt else None

    paused_title = win_fnt.render("Paused", True, BLACK) if win_fnt else None

    pause_button_labels = ["Resume", "Reset Level", "Quit to Menu"]
    pause_button_surfaces = [stats_fnt.render(text, True, BLACK) if stats_fnt else None for text in pause_button_labels]

    resume_txt = pause_button_surfaces[0]
    reset_txt = pause_button_surfaces[1] # Corresponds to "Reset Level"
    quit_txt = pause_button_surfaces[2]  # Corresponds to "Quit to Menu"

    trans_p_btn_surf = None
    if stats_fnt:
        p_txt_rnd = stats_fnt.render("Pause",True,BLACK)
        if p_txt_rnd:
            trans_p_btn_surf=pygame.Surface(pause_btn_r.size,pygame.SRCALPHA);trans_p_btn_surf.fill((220,220,220,180))
            trans_p_btn_surf.blit(p_txt_rnd,p_txt_rnd.get_rect(center=(pause_btn_r.width//2,pause_btn_r.height//2)))
            pygame.draw.rect(trans_p_btn_surf,BLACK,trans_p_btn_surf.get_rect(),1)

    run_sess = True
    while run_sess:
        c_ticks=pygame.time.get_ticks()
        if not g_won and not paused: elap_s=(c_ticks-s_time)/1000.0
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: return "QUIT",None
            if ev.type==pygame.MOUSEBUTTONDOWN:
                if ev.button==1: # LEFT CLICK - Vertex interaction
                    if not paused: # Allow vertex selection if not paused (regardless of win state)
                        m_down=True; mx,my=ev.pos
                        for i,(vx,vy) in enumerate(g_v):
                            if ((vx-mx)**2+(vy-my)**2)**0.5 < VERTEX_RADIUS: sel_v_idx=i;break
                elif ev.button==3: # RIGHT CLICK - UI Buttons
                    if not paused and not g_won and pause_btn_r.collidepoint(ev.pos): is_paused=True;p_s_ticks=c_ticks
                    elif paused:
                        if res_btn_r and res_btn_r.collidepoint(ev.pos): is_paused=False;s_time+=c_ticks-p_s_ticks
                        elif pr_btn_r and pr_btn_r.collidepoint(ev.pos): return "RESTART_SAME",n_v_sess
                        elif pq_btn_r and pq_btn_r.collidepoint(ev.pos): return "RESTART",None
                    elif g_won:
                        if r_btn_r and r_btn_r.collidepoint(ev.pos): return "RESTART",None
                        elif rs_btn_r and rs_btn_r.collidepoint(ev.pos): return "RESTART_SAME",n_v_sess
                        elif cap_btn_r and cap_btn_r.collidepoint(ev.pos):
                            sf = capture_game_view(
                                SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, g_v, g_e, cross_set,
                                VERTEX_RADIUS, RED_VERTEX, RED_EDGE_CROSSING, GREEN_EDGE_NON_CROSSING,
                                n_v_sess, len(g_e), elap_s # Pass stats here
                            )
                            if sf and stats_fnt: scr_msg_surf=stats_fnt.render(f"Saved: {sf}",True,BLACK); scr_msg_until=c_ticks+3000
                        elif px_btn_r and px_btn_r.collidepoint(ev.pos):
                            sf_for_x = capture_game_view(
                                SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, g_v, g_e, cross_set,
                                VERTEX_RADIUS, RED_VERTEX, RED_EDGE_CROSSING, GREEN_EDGE_NON_CROSSING,
                                n_v_sess, len(g_e), elap_s # Pass stats here
                            )
                            if sf_for_x and stats_fnt:
                                scr_msg_surf = stats_fnt.render(f"Captured! Posting to X...", True, BLACK)
                                scr_msg_until = c_ticks + 2000 # Shorter message for X post
                            tw=f"Solved Planarity: {n_v_sess}V, {len(g_e)}E, {elap_s:.1f}s! #PlanarityGame"; webbrowser.open_new_tab(f"https://x.com/intent/post?text={urllib.parse.quote(tw)}")
            elif ev.type==pygame.MOUSEBUTTONUP and ev.button==1:
                m_down=False
                if not paused and sel_v_idx is not None: # Update crossings if a vertex was moved, if not paused
                    cross_set=get_crossing_edges(g_v,g_e)
                sel_v_idx=None
            elif ev.type==pygame.MOUSEMOTION:
                if not paused and m_down and sel_v_idx is not None: # Allow dragging if not paused (win state doesn't prevent)
                    mx,my=ev.pos;g_v[sel_v_idx]=(max(VERTEX_RADIUS,min(mx,SCREEN_WIDTH-VERTEX_RADIUS)),max(VERTEX_RADIUS,min(my,SCREEN_HEIGHT-VERTEX_RADIUS)))
                    cross_set=get_crossing_edges(g_v,g_e) # Live update of crossings

        screen.fill(WHITE); draw_graph(screen,g_v,g_e,VERTEX_RADIUS,cross_set)
        # Set game_won flag only once if conditions are met
        if not g_won and not paused and not cross_set:
            g_won=True
            if g_won and not r_btn_r: # Define win screen button rects once
                bw,bh,bs=220,40,10 # Button width, height, spacing
                widths = [w.get_width()+30 if w else 200 for w in [ng_txt,rs_txt,px_txt,cap_txt]]
                max_bw = max(widths) if widths else bw
                r_btn_r,rs_btn_r,px_btn_r,cap_btn_r = (pygame.Rect(0,0,max_bw,bh) for _ in range(4))

        if g_won:
            h_title=win_fnt.get_height() if win_fnt else 60; h_stat=stats_fnt.get_height() if stats_fnt else 30
            h_btn=40; s_title,s_stat,s_btn_block,s_btn = 10,3,20,8
            msgs_s=[win_fnt.render("You Win!",True,WIN_MESSAGE_COLOR) if win_fnt else None]
            stats_data=[f"Vertices: {n_v_sess}",f"Edges: {len(g_e)}",f"Time: {elap_s:.1f}s"]
            if stats_fnt: msgs_s.extend([stats_fnt.render(s,True,WIN_MESSAGE_COLOR) for s in stats_data])
            msgs_s = [s for s in msgs_s if s] # Filter out None if fonts failed

            btns_d = []
            if ng_txt: btns_d.append({'s':ng_txt,'r':r_btn_r,'c':(200,200,200)})
            if rs_txt: btns_d.append({'s':rs_txt,'r':rs_btn_r,'c':(200,200,200)})
            if cap_txt: btns_d.append({'s':cap_txt,'r':cap_btn_r,'c':(200,200,180)}) # Yellowish for capture
            if px_txt: btns_d.append({'s':px_txt,'r':px_btn_r,'c':(180,180,220)}) # Bluish for X

            total_h = (h_title + s_title if msgs_s and msgs_s[0] else 0) + \
                      (sum(s.get_height() for s in msgs_s[1:]) + max(0,len(msgs_s)-2)*s_stat if len(msgs_s)>1 else 0) + \
                      (s_btn_block if btns_d else 0) + \
                      (len(btns_d)*h_btn + max(0,len(btns_d)-1)*s_btn if btns_d else 0)
            curr_y = SCREEN_HEIGHT//2 - total_h//2

            if msgs_s:
                r=msgs_s[0].get_rect(center=(SCREEN_WIDTH//2,curr_y+msgs_s[0].get_height()//2));screen.blit(msgs_s[0],r);curr_y+=msgs_s[0].get_height()+s_title
                for i in range(1,len(msgs_s)):
                    s=msgs_s[i];r=s.get_rect(center=(SCREEN_WIDTH//2,curr_y+s.get_height()//2));screen.blit(s,r);curr_y+=s.get_height()+s_stat
            curr_y += s_btn_block - (s_stat if len(msgs_s)>1 else 0) # Adjust if no stats, or remove last stat spacing

            for b in btns_d:
                b['r'].centerx=SCREEN_WIDTH//2;b['r'].top=curr_y;pygame.draw.rect(screen,b['c'],b['r']);pygame.draw.rect(screen,BLACK,b['r'],2)
                screen.blit(b['s'],b['s'].get_rect(center=b['r'].center));curr_y+=h_btn+s_btn

        if not g_won and not paused and stats_fnt:
            screen.blit(stats_fnt.render(f"Time: {elap_s:.1f}",True,BLACK),(10,50))
            if trans_p_btn_surf: screen.blit(trans_p_btn_surf,pause_btn_r.topleft)

        if scr_msg_until > 0 and stats_fnt:
            if c_ticks < scr_msg_until:
                if scr_msg_surf:pygame.draw.rect(screen,(230,230,230),scr_msg_surf.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT-30)).inflate(10,5));screen.blit(scr_msg_surf,scr_msg_surf.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT-30)))
            else: scr_msg_until=0; scr_msg_surf=None

        if paused:
            ovl=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA);ovl.fill((0,0,0,180));screen.blit(ovl,(0,0))
            y_s=SCREEN_HEIGHT//2-100;bw,bh,s=180,50,15
            if paused_title:screen.blit(paused_title,paused_title.get_rect(center=(SCREEN_WIDTH//2,y_s)));y_s+=60
            btns_p_d = [{'s':resume_txt,'r':resume_button_rect},{'s':reset_level_text,'r':pr_btn_r},{'s':quit_to_menu_text,'r':pq_btn_r}]
            for i,b_d in enumerate(btns_p_d):
                if b_d['s']: # Check if text surface exists
                    # Dynamically assign rect to the button's dict or use pre-initialized ones if their scope allows
                    # For pause menu, rects are defined here for simplicity as they are only used here.
                    current_btn_rect = pygame.Rect(SCREEN_WIDTH//2-bw//2,y_s + i*(bh+s),bw,bh)
                    if i==0: resume_button_rect = current_btn_rect # Assign for click detection
                    elif i==1: pause_reset_button_rect = current_btn_rect
                    elif i==2: pause_quit_button_rect = current_btn_rect

                    pygame.draw.rect(screen,(200,200,200),current_btn_rect);pygame.draw.rect(screen,BLACK,current_btn_rect,2)
                    screen.blit(b_d['s'],b_d['s'].get_rect(center=current_btn_rect.center))
        pygame.display.flip()
    return "QUIT", None

def main_application():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Planarity")
    win_fnt, stats_fnt = None, None
    try: win_fnt = pygame.font.Font(None, 74); stats_fnt = pygame.font.Font(None, 36)
    except Exception as e: print(f"Font loading failed: {e}")
    fixed_n = None
    while True:
        status, data = main_game_session(screen, win_fnt, stats_fnt, fixed_n_v=fixed_n) # Corrected keyword
        if status == "QUIT": break
        elif status == "RESTART": fixed_n = None
        elif status == "RESTART_SAME": fixed_n = data
    pygame.quit()

if __name__ == '__main__':
    main_application()
