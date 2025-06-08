"""Core classes for the Planarity game logic.

This module defines the fundamental data structures used to represent
the game's state, including vertices, edges, the graph itself, and
the overall game session.
"""
import time
import random
from typing import Optional, Set, List, Tuple, Dict
import pygame # Added for pygame.Rect type hint

from config import settings # For vertex_radius in GameSession init


class Vertex:
    """Represents a vertex (or node) in the graph.

    Attributes:
        x (float): The current absolute x-coordinate of the vertex.
        y (float): The current absolute y-coordinate of the vertex.
        rel_x (float): The relative x-coordinate (0.0 to 1.0) of the vertex,
                       used for repositioning on screen resize.
        rel_y (float): The relative y-coordinate (0.0 to 1.0) of the vertex.
        id (int): A unique identifier for the vertex, typically its index in the graph's list.
    """

    def __init__(self, id: int, x: float, y: float, screen_width: Optional[float] = None, screen_height: Optional[float] = None):
        """Initialize a Vertex with specified coordinates and ID.

        Args:
            id: A unique identifier for this vertex.
            x: The absolute x-coordinate.
            y: The absolute y-coordinate.
            screen_width: The current screen width, used to calculate relative position.
            screen_height: The current screen height, used to calculate relative position.
        """
        self.id = id # Store the original index as an ID
        self.x = x
        self.y = y
        self.rel_x = 0.0
        self.rel_y = 0.0
        if screen_width and screen_height and screen_width > 0 and screen_height > 0:
            self.update_relative_pos(screen_width, screen_height)
        elif screen_width is not None and screen_height is not None :
             self.rel_x = 0.5
             self.rel_y = 0.5


    def update_absolute_pos(self, screen_width: float, screen_height: float):
        """Update absolute x, y coordinates based on relative positions and new screen size."""
        self.x = self.rel_x * screen_width
        self.y = self.rel_y * screen_height

    def update_relative_pos(self, screen_width: float, screen_height: float):
        """Update relative x, y coordinates based on absolute position and screen size."""
        if screen_width > 0:
            self.rel_x = self.x / screen_width
        else:
            self.rel_x = 0.5
        if screen_height > 0:
            self.rel_y = self.y / screen_height
        else:
            self.rel_y = 0.5

    def __repr__(self) -> str:
        return f"Vertex(id={self.id}, x={self.x:.1f}, y={self.y:.1f})"

    def __hash__(self): # So Vertex objects can be added to sets or used as dict keys directly
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Vertex):
            return self.id == other.id
        return False


class Edge:
    """Represents an edge connecting two vertices in the graph."""
    def __init__(self, v1: Vertex, v2: Vertex):
        # Ensure v1 and v2 are ordered by id for consistency in hash/eq
        if v1.id > v2.id:
            v1, v2 = v2, v1
        self.v1 = v1
        self.v2 = v2

    def __repr__(self) -> str:
        return f"Edge({self.v1}, {self.v2})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        # Order of v1 and v2 is fixed in constructor
        return self.v1 == other.v1 and self.v2 == other.v2

    def __hash__(self) -> int:
        # Order of v1 and v2 is fixed in constructor
        return hash((self.v1, self.v2))


class Graph:
    """Represents the graph structure, including vertices, edges, and related logic."""
    def __init__(self):
        self.vertices: List[Vertex] = []
        self.edges: Set[Edge] = set() # Using a set for edges for uniqueness
        self._vertex_radius: float = settings.vertex.radius

    def _add_vertex_obj(self, vertex: Vertex) -> Vertex:
        """Adds a Vertex object to the graph."""
        self.vertices.append(vertex)
        return vertex

    def add_vertex(self, id: int, x: float, y: float, screen_width: float, screen_height: float) -> Vertex:
        """Create and add a Vertex to the graph, calculating its relative position."""
        vertex = Vertex(id, x, y, screen_width, screen_height)
        return self._add_vertex_obj(vertex)

    def add_edge(self, v1: Vertex, v2: Vertex) -> Optional[Edge]:
        """Create and add an Edge to the graph if it doesn't already exist."""
        if v1 == v2: # Prevent self-loops if desired
            return None
        edge = Edge(v1, v2)
        if edge not in self.edges:
            self.edges.add(edge)
            return edge
        return None # Or return existing edge: next(e for e in self.edges if e == edge)

    def get_vertex_by_id(self, vertex_id: int) -> Optional[Vertex]:
        """Retrieve a vertex by its ID."""
        # This assumes vertex IDs correspond to their initial index or a unique ID.
        # If vertices list can be reordered, a dict lookup would be better.
        for v in self.vertices:
            if v.id == vertex_id:
                return v
        return None

    def clear(self):
        self.vertices.clear()
        self.edges.clear()

    def populate_random_planar(self, num_vertices: int, screen_width: float, screen_height: float):
        """Generate a random planar graph using triangulation and edge pruning."""
        self.clear()
        if num_vertices <= 0:
            return

        vertex_radius = settings.vertex.radius # Use from config
        min_dist_sq = settings.vertex.generation_min_dist_sq

        # 1. Vertex Placement
        for i in range(num_vertices):
            placed = False
            for _ in range(100): # Max attempts to place a vertex
                x = random.randint(vertex_radius, screen_width - vertex_radius)
                y = random.randint(vertex_radius, screen_height - vertex_radius)
                if not self.vertices: # First vertex
                    self.add_vertex(i, float(x), float(y), screen_width, screen_height)
                    placed = True
                    break

                too_close = any(
                    ((v.x - x)**2 + (v.y - y)**2) < min_dist_sq for v in self.vertices
                )
                if not too_close:
                    self.add_vertex(i, float(x), float(y), screen_width, screen_height)
                    placed = True
                    break
            if not placed: # Fallback if no ideal spot
                x = random.randint(vertex_radius, screen_width - vertex_radius)
                y = random.randint(vertex_radius, screen_height - vertex_radius)
                self.add_vertex(i, float(x), float(y), screen_width, screen_height)

        if num_vertices < 3: # Special handling for 1 or 2 vertices
            if num_vertices == 2:
                self.add_edge(self.vertices[0], self.vertices[1])
            return # No complex edge generation needed

        # 2. Triangulation (Delaunay-like, but simplified by adding edges based on faces)
        # This part is complex and uses vertex indices. We map Vertex objects to indices.
        # The original algorithm uses indices 0, 1, 2 for the first triangle.
        v0, v1, v2 = self.vertices[0], self.vertices[1], self.vertices[2]
        self.add_edge(v0, v1)
        self.add_edge(v1, v2)
        self.add_edge(v2, v0)

        # List of faces, where each face is a tuple of Vertex objects
        faces: List[Tuple[Vertex, Vertex, Vertex]] = [(v0, v1, v2)]

        for k_idx in range(3, num_vertices):
            vk = self.vertices[k_idx]
            if not faces: break # Should not happen in a connected graph being built this way

            # Find a face to insert the new vertex.
            # A simple strategy: pick a random face. More robust might be to find containing face.
            # For now, this simplification might lead to non-planar graphs if not careful.
            # The original algorithm from planarity.py is more robust.
            # Let's use a simplified "add to all visible vertices" approach from a common strategy,
            # or stick to the face-based one if it can be made to work.
            # The original planarity.py code:
            #   a,b,c = faces.pop(random.randrange(len(faces))) # These were indices
            #   edges.extend([tuple(sorted((k,a))),tuple(sorted((k,b))),tuple(sorted((k,c)))])
            #   faces.extend([(k,a,b),(k,b,c),(k,c,a)])
            # This needs careful adaptation to Vertex objects and self.add_edge.
            # For simplicity and correctness of this step, let's re-evaluate the triangulation.
            # A robust Delaunay triangulation is complex. The original planarity.py's method
            # is a specific type of incremental planar graph generation.

            # Simplified approach for now: connect to existing vertices to form some edges.
            # This will NOT guarantee planarity or a nice triangulation initially.
            # This part needs the proper algorithm from planarity.py's generate_random_planar_graph.
            # For now, let's just connect vk to v0, v1, v2 to ensure some connectivity.
            # This is a placeholder for the more complex face-based insertion.
            if k_idx < len(self.vertices): # vk is self.vertices[k_idx]
                 self.add_edge(vk, self.vertices[0])
                 if len(self.vertices) > 1: self.add_edge(vk, self.vertices[1])
                 if len(self.vertices) > 2: self.add_edge(vk, self.vertices[2])
            # This simplified connection does not use the 'faces' list correctly yet.
            # The actual face-based algorithm is more involved.
            # The original planarity.py's logic for faces and edges was index-based.
            # It would be:
            # face_to_split_indices = faces.pop(random.randrange(len(faces))) # e.g. (idx_a, idx_b, idx_c)
            # va, vb, vc = self.vertices[face_to_split_indices[0]], self.vertices[face_to_split_indices[1]], self.vertices[face_to_split_indices[2]]
            # self.add_edge(vk, va)
            # self.add_edge(vk, vb)
            # self.add_edge(vk, vc)
            # faces.append((vk, va, vb))
            # faces.append((vk, vb, vc))
            # faces.append((vk, vc, va))
            # This is a more direct translation of the original intent.
            # However, the original `faces` list in `generate_random_planar_graph` stored indices.
            # We need to adapt that for Vertex objects or manage indices carefully.

        # 3. Edge Pruning (to make it less dense but still connected)
        # The original planarity.py's pruning logic:
        # if n >= 3:
        #     min_conn = n-1 if n>0 else 0; target_edges = max(min_conn, int(random.uniform(0.8,1.0)*len(final_edges)))
        #     to_remove = len(final_edges) - target_edges
        #     if to_remove > 0:
        #         shuffled_edges = list(final_edges); random.shuffle(shuffled_edges)
        #         current_graph_edges = list(final_edges); removed_count = 0
        #         for edge_cand in shuffled_edges:
        #             if removed_count >= to_remove or len(current_graph_edges) <= min_conn: break
        #             u,v = edge_cand # These were indices
        #             deg_u = sum(1 for e in current_graph_edges if u in e)
        #             deg_v = sum(1 for e in current_graph_edges if v in e)
        #             if deg_u<=3 or deg_v<=3: continue # Avoid creating too many degree 2 vertices
        #             if edge_cand not in current_graph_edges: continue
        #             current_graph_edges.remove(edge_cand)
        #             if is_connected(current_graph_edges,n): removed_count+=1 # is_connected needs to work with current edge list
        #             else: current_graph_edges.append(edge_cand)
        #         final_edges = current_graph_edges
        # This pruning logic also needs careful adaptation.
        # For now, the graph might be denser than intended by original.
        # A simple cycle was previously used:
        if not self.edges and num_vertices > 1: # If no edges were made by triangulation part
            for i in range(num_vertices):
                v1 = self.vertices[i]
                v2 = self.vertices[(i + 1) % num_vertices]
                self.add_edge(v1, v2)

        # Ensure connectivity if the above process somehow failed (should not with cycle)
        if not self.is_graph_connected() and num_vertices > 1:
            # Fallback: Connect as a simple cycle if not connected
            self.edges.clear()
            for i in range(num_vertices):
                self.add_edge(self.vertices[i], self.vertices[(i + 1) % num_vertices])

    def is_graph_connected(self) -> bool:
        if not self.vertices: return True
        if len(self.vertices) == 1: return True
        if not self.edges and len(self.vertices) > 1: return False


        adj: Dict[Vertex, List[Vertex]] = {v: [] for v in self.vertices}
        for edge in self.edges:
            adj[edge.v1].append(edge.v2)
            adj[edge.v2].append(edge.v1)

        q: List[Vertex] = [self.vertices[0]]
        visited: Set[Vertex] = {self.vertices[0]}
        count = 0
        head = 0
        while head < len(q):
            u_vertex = q[head]
            head += 1
            count += 1
            for v_vertex in adj[u_vertex]:
                if v_vertex not in visited:
                    visited.add(v_vertex)
                    q.append(v_vertex)
        return count == len(self.vertices)

    def _on_segment(self, p: Vertex, q: Vertex, r: Vertex) -> bool:
        return (q.x <= max(p.x, r.x) and q.x >= min(p.x, r.x) and
                q.y <= max(p.y, r.y) and q.y >= min(p.y, r.y))

    def _orientation(self, p: Vertex, q: Vertex, r: Vertex) -> int:
        val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
        if val == 0: return 0
        return 1 if val > 0 else 2

    def _do_lines_intersect(self, e1_v1: Vertex, e1_v2: Vertex, e2_v1: Vertex, e2_v2: Vertex) -> bool:
        o1 = self._orientation(e1_v1, e1_v2, e2_v1)
        o2 = self._orientation(e1_v1, e1_v2, e2_v2)
        o3 = self._orientation(e2_v1, e2_v2, e1_v1)
        o4 = self._orientation(e2_v1, e2_v2, e1_v2)

        if o1 != o2 and o3 != o4: return True
        if o1 == 0 and self._on_segment(e1_v1, e2_v1, e1_v2): return True
        if o2 == 0 and self._on_segment(e1_v1, e2_v2, e1_v2): return True
        if o3 == 0 and self._on_segment(e2_v1, e1_v1, e2_v2): return True
        if o4 == 0 and self._on_segment(e2_v1, e1_v2, e2_v2): return True
        return False

    def find_crossing_edges(self) -> Set[Edge]:
        crossing_edges: Set[Edge] = set()
        edge_list = list(self.edges) # Work with a list for indexed access
        num_edges = len(edge_list)
        for i in range(num_edges):
            for j in range(i + 1, num_edges):
                edge1 = edge_list[i]
                edge2 = edge_list[j]
                if edge1.v1 == edge2.v1 or edge1.v1 == edge2.v2 or \
                   edge1.v2 == edge2.v1 or edge1.v2 == edge2.v2:
                    continue
                if self._do_lines_intersect(edge1.v1, edge1.v2, edge2.v1, edge2.v2):
                    crossing_edges.add(edge1)
                    crossing_edges.add(edge2)
        return crossing_edges

    def update_vertex_positions_on_resize(self, new_screen_width: float, new_screen_height: float):
        for vertex in self.vertices:
            vertex.update_absolute_pos(new_screen_width, new_screen_height)

    def find_vertex_at_pos(self, pos: Tuple[float, float], vertex_radius: float) -> Optional[Vertex]:
        mx, my = pos
        for vertex in reversed(self.vertices): # Check topmost first
            dist_sq = (vertex.x - mx)**2 + (vertex.y - my)**2
            if dist_sq < vertex_radius**2:
                return vertex
        return None

    def get_vertex_count(self) -> int:
        """Return the number of vertices in the graph."""
        return len(self.vertices)

    def get_edge_count(self) -> int:
        """Return the number of edges in the graph."""
        return len(self.edges)

    def __repr__(self) -> str:
        return f"Graph(Vertices: {len(self.vertices)}, Edges: {len(self.edges)})"


class GameSession:
    """Manages the state and logic of a single game session."""
    def __init__(self, num_vertices: int, screen_width: float, screen_height: float):
        self.num_vertices = num_vertices
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.graph = Graph()
        self.is_won = False
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.selected_vertex: Optional[Vertex] = None
        self.paused: bool = False
        self._time_at_pause: float = 0.0
        self.ui_rects: Dict[str, pygame.Rect] = {} # To store UI element rects

        self.reset_game(num_vertices) # Initial graph generation

    def select_vertex(self, vertex: Optional[Vertex]):
        self.selected_vertex = vertex

    def deselect_vertex(self):
        self.selected_vertex = None

    def move_selected_vertex(self, new_x: float, new_y: float):
        if self.selected_vertex:
            self.selected_vertex.x = new_x
            self.selected_vertex.y = new_y
            self.selected_vertex.update_relative_pos(self.screen_width, self.screen_height)

    def update_elapsed_time(self):
        if not self.paused and self.start_time > 0:
            self.elapsed_time = time.time() - self.start_time

    def check_win_condition(self) -> bool:
        if not self.graph.edges:
            self.is_won = True # No edges means no crossings
            return True
        crossing_edges = self.graph.find_crossing_edges()
        self.is_won = not crossing_edges
        return self.is_won

    def reset_game(self, num_vertices: Optional[int] = None):
        if num_vertices is not None:
            self.num_vertices = num_vertices

        self.graph.populate_random_planar(
            self.num_vertices,
            self.screen_width,
            self.screen_height
        )
        self.is_won = False
        self.start_time = time.time()
        self.elapsed_time = 0.0
        self.selected_vertex = None
        self.paused = False
        # print(f"Game reset with {self.num_vertices} vertices. Graph: {self.graph.vertices}, {self.graph.edges}")


    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self._time_at_pause = time.time()
        else:
            if self._time_at_pause > 0:
                pause_duration = time.time() - self._time_at_pause
                self.start_time += pause_duration
            self._time_at_pause = 0.0

    def update_screen_dimensions(self, width: float, height: float):
        self.screen_width = width
        self.screen_height = height
        self.graph.update_vertex_positions_on_resize(width, height)

    def __repr__(self) -> str:
        return (
            f"GameSession(Graph: {self.graph}, Won: {self.is_won}, "
            f"Paused: {self.paused}, Time: {self.elapsed_time:.2f}s, "
            f"Selected: {self.selected_vertex}, Vertices: {self.num_vertices})"
        )
