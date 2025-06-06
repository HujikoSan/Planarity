import unittest
from planarity import (
    on_segment, orientation, do_lines_intersect, get_crossing_edges,
    is_connected, generate_random_planar_graph # New imports
)

class TestLineIntersection(unittest.TestCase):
    # No changes for TestLineIntersection
    # p1, q1, p2, q2
    # Segment 1: (p1, q1), Segment 2: (p2, q2)

    def test_simple_intersection(self):
        p1, q1 = (0, 0), (10, 10)
        p2, q2 = (0, 10), (10, 0)
        self.assertTrue(do_lines_intersect(p1, q1, p2, q2), "Simple intersection failed")

    def test_no_intersection(self):
        p1, q1 = (0, 0), (1, 1)
        p2, q2 = (5, 5), (6, 6)
        self.assertFalse(do_lines_intersect(p1, q1, p2, q2), "No intersection failed")

    def test_collinear_overlapping(self):
        p1, q1 = (0, 0), (6, 0)
        p2, q2 = (2, 0), (4, 0)
        self.assertTrue(do_lines_intersect(p1, q1, p2, q2), "Collinear overlapping (1) failed")
        self.assertTrue(do_lines_intersect(p2, q2, p1, q1), "Collinear overlapping (2) failed")

    def test_collinear_non_overlapping(self):
        p1, q1 = (0, 0), (2, 0)
        p2, q2 = (3, 0), (5, 0)
        self.assertFalse(do_lines_intersect(p1, q1, p2, q2), "Collinear non-overlapping failed")

    def test_collinear_touching_endpoint(self):
        p1, q1 = (0, 0), (2, 0)
        p2, q2 = (2, 0), (4, 0)
        self.assertTrue(do_lines_intersect(p1, q1, p2, q2), "Collinear touching endpoint failed")

    def test_parallel_no_intersection(self):
        p1, q1 = (0, 0), (10, 0)
        p2, q2 = (0, 5), (10, 5)
        self.assertFalse(do_lines_intersect(p1, q1, p2, q2), "Parallel no intersection failed")

    def test_sharing_endpoint_L_shape(self):
        p1, q1 = (0, 0), (5, 0)
        p2, q2 = (5, 0), (5, 5)
        self.assertTrue(do_lines_intersect(p1, q1, p2, q2), "Sharing endpoint L-shape failed")


    def test_T_junction_like(self):
        p1, q1 = (0, 0), (10, 0)
        p2, q2 = (5, 5), (5, 0)
        self.assertTrue(do_lines_intersect(p1, q1, p2, q2), "T-junction failed")

    def test_segments_cross_at_endpoint_special_case(self):
        p1, q1 = (0,0), (10,0)
        p2, q2 = (5,5), (5,0)
        self.assertTrue(do_lines_intersect(p1, q1, p2, q2), "Cross at endpoint (1) failed")

        p1, q1 = (5,0), (5,5)
        p2, q2 = (0,0),(10,0)
        self.assertTrue(do_lines_intersect(p1, q1, p2, q2), "Cross at endpoint (2) failed")


class TestGetCrossingEdges(unittest.TestCase): # Renamed class
    def test_no_crossings_square(self):
        vertices = [(0,0), (10,0), (10,10), (0,10)]
        edges = [(0,1), (1,2), (2,3), (3,0)]
        expected_crossings = set()
        self.assertEqual(get_crossing_edges(vertices, edges), expected_crossings, "No crossings square failed")

    def test_one_crossing_X_shape(self):
        vertices = [(0,0), (10,10), (0,10), (10,0)]
        e1 = (0,1)
        e2 = (2,3)
        edges = [e1, e2]
        expected_crossings = {e1, e2}
        self.assertEqual(get_crossing_edges(vertices, edges), expected_crossings, "One crossing X-shape failed")

    def test_square_with_crossing_diagonals(self):
        # Vertex order for indexing: v0=(0,0), v1=(10,0), v2=(0,10), v3=(10,10)
        vertices = [(0,0), (10,0), (0,10), (10,10)]

        # Edges based on this vertex order.
        # Previous version of this test used:
        # edge_s1 = (0,1) # (0,0) to (10,0)
        # edge_s2 = (1,3) # (10,0) to (10,10)
        # edge_s3 = (3,2) # (10,10) to (0,10)
        # edge_s4 = (2,0) # (0,10) to (0,0)
        # diag1 = (0,3)   # (0,0) to (10,10)
        # diag2 = (1,2)   # (10,0) to (0,10)
        # This definition is consistent.
        edge_s1 = (0,1); edge_s2 = (1,3); edge_s3 = (3,2); edge_s4 = (2,0)
        diag1 = (0,3); diag2 = (1,2)
        edges = [edge_s1, edge_s2, edge_s3, edge_s4, diag1, diag2]

        expected_crossings = {diag1, diag2}
        self.assertEqual(get_crossing_edges(vertices, edges), expected_crossings, "Square with crossing diagonals failed")

    def test_multiple_crossings_star(self):
        vertices = [(50,0), (100,35), (80,90), (20,90), (0,35)] # v0,v1,v2,v3,v4
        e02 = (0,2); e03 = (0,3); e13 = (1,3); e14 = (1,4); e24 = (2,4)
        edges = [e02, e03, e13, e14, e24]
        # Verified crossings: (e02,e13), (e03,e14), (e13,e24)
        # All 5 edges are involved.
        expected_crossings = {e02, e13, e03, e14, e24}
        self.assertEqual(get_crossing_edges(vertices, edges), expected_crossings, "Multiple crossings star failed")

    def test_edges_sharing_vertex_no_crossing(self):
        vertices = [(0,0), (10,0), (5,5)]
        edges = [(0,1), (1,2)]
        expected_crossings = set()
        self.assertEqual(get_crossing_edges(vertices, edges), expected_crossings, "Edges sharing vertex (triangle) failed")

        vertices = [(0,0), (10,0), (10,10), (0,10)]
        edges = [(0,1), (1,2), (2,3), (3,0)]
        self.assertEqual(get_crossing_edges(vertices, edges), expected_crossings, "Edges sharing vertex (square) failed")

    def test_no_edges(self):
        vertices = [(0,0), (1,1)]
        edges = []
        expected_crossings = set()
        self.assertEqual(get_crossing_edges(vertices, edges), expected_crossings, "No edges failed")

    def test_single_edge(self):
        vertices = [(0,0), (1,1)]
        edges = [(0,1)]
        expected_crossings = set()
        self.assertEqual(get_crossing_edges(vertices, edges), expected_crossings, "Single edge failed")

    def test_collinear_edges_sharing_vertex_no_crossing(self):
        vertices = [(0,0), (5,0), (10,0)]
        edges = [(0,1), (1,2)]
        expected_crossings = set()
        self.assertEqual(get_crossing_edges(vertices, edges), expected_crossings, "Collinear edges sharing vertex failed")

    def test_collinear_edges_not_sharing_vertex_overlapping_crossing(self):
        vertices = [(0,0), (10,0), (2,0), (8,0)]
        e1 = (0,1)
        e2 = (2,3)
        edges = [e1, e2]
        expected_crossings = {e1, e2}
        self.assertEqual(get_crossing_edges(vertices, edges), expected_crossings, "Collinear overlapping non-adjacent failed")

    def test_collinear_edges_not_sharing_vertex_separate_no_crossing(self):
        vertices = [(0,0), (1,0), (2,0), (3,0)]
        edges = [(0,1), (2,3)]
        expected_crossings = set()
        self.assertEqual(get_crossing_edges(vertices, edges), expected_crossings, "Collinear separate non-adjacent failed")


if __name__ == '__main__':
    unittest.main()


class TestIsConnected(unittest.TestCase):
    def test_empty_graph(self):
        self.assertTrue(is_connected([], 0), "Empty graph (0 vertices) should be connected.")

    def test_single_vertex_graph(self):
        self.assertTrue(is_connected([], 1), "Single vertex graph should be connected.")

    def test_two_vertices_no_edge(self):
        self.assertFalse(is_connected([], 2), "Two vertices, no edge, should be disconnected.")

    def test_two_vertices_with_edge(self):
        self.assertTrue(is_connected([tuple(sorted((0,1)))], 2), "Two vertices with an edge should be connected.")

    def test_cycle_graph_connected(self):
        n = 4
        edges = [tuple(sorted((i, (i + 1) % n))) for i in range(n)]
        self.assertTrue(is_connected(edges, n), "Cycle graph C4 should be connected.")
        n = 5
        edges = [tuple(sorted((i, (i + 1) % n))) for i in range(n)]
        self.assertTrue(is_connected(edges, n), "Cycle graph C5 should be connected.")

    def test_disconnected_two_triangles(self):
        edges = [
            tuple(sorted((0,1))), tuple(sorted((1,2))), tuple(sorted((2,0))), # Triangle 1
            tuple(sorted((3,4))), tuple(sorted((4,5))), tuple(sorted((5,3)))  # Triangle 2
        ]
        self.assertFalse(is_connected(edges, 6), "Two separate triangles should be disconnected.")

    def test_graph_with_isolated_vertex(self):
        edges = [tuple(sorted((0,1))), tuple(sorted((1,2))), tuple(sorted((2,0)))] # Triangle
        # Vertex 3 is isolated
        self.assertFalse(is_connected(edges, 4), "Graph with an isolated vertex should be disconnected.")

    def test_larger_connected_graph(self):
        # Simple line graph (path graph) P5
        edges = [tuple(sorted((0,1))), tuple(sorted((1,2))), tuple(sorted((2,3))), tuple(sorted((3,4)))]
        self.assertTrue(is_connected(edges, 5), "Path graph P5 should be connected.")


class TestGenerateRandomPlanarGraph(unittest.TestCase):
    def _run_graph_generation_test(self, n_vertices):
        print(f"Testing graph generation for n_vertices = {n_vertices}") # Added print for long tests
        vertices, edges = generate_random_planar_graph(n_vertices)

        self.assertEqual(len(vertices), n_vertices, f"Expected {n_vertices} vertices, got {len(vertices)}")

        m = len(edges)
        # print(f"  n={n_vertices}, m={m}") # Debug print

        if n_vertices == 0:
            self.assertEqual(m, 0, f"n=0, expected 0 edges, got {m}")
        elif n_vertices == 1:
            self.assertEqual(m, 0, f"n=1, expected 0 edges, got {m}")
        elif n_vertices == 2:
            self.assertEqual(m, 1, f"n=2, expected 1 edge, got {m}")
            if m == 1: # check content if edge count is correct
                 self.assertIn(tuple(sorted((0,1))), edges, "Edge (0,1) missing for n=2")
        elif n_vertices >= 3:
            max_possible_edges_triangulation = 3 * n_vertices - 6
            # Target is 0.8 to 1.0 of these edges.
            min_target_edges = int(0.8 * max_possible_edges_triangulation)
            min_for_connectivity = n_vertices - 1

            lower_bound = max(min_for_connectivity, min_target_edges)
            # Upper bound is the number of edges in a full triangulation
            upper_bound = max_possible_edges_triangulation

            self.assertTrue(lower_bound <= m <= upper_bound,
                            f"For n={n_vertices}, edges {m} not in range [{lower_bound}, {upper_bound}]")

            # Check connectivity for n > 0 or if n=0 and m=0
            if n_vertices > 0 : # (n=0 case covered by specific edge check)
                 self.assertTrue(is_connected(edges, len(vertices)),
                                f"Graph with n={n_vertices} and m={m} edges not connected.")

        # Check for canonical edge format (u < v) and uniqueness (implicitly by set in generation)
        for u, v in edges:
            self.assertTrue(u < v, f"Edge {(u,v)} not in canonical form (u < v).")
        self.assertEqual(len(edges), len(set(edges)), "Duplicate edges found.")


    def test_generate_n0(self):
        self._run_graph_generation_test(0)

    def test_generate_n1(self):
        self._run_graph_generation_test(1)

    def test_generate_n2(self):
        self._run_graph_generation_test(2)

    def test_generate_n3(self):
        self._run_graph_generation_test(3) # Triangulation: 3 edges. Target: max(2, int(0.8*3)=2) to 3. Range [2,3]
                                           # Corrected: Triangulation for n=3 is 3 edges. Target: max(2, int(0.8*3)=2) to 3. Range [2,3].
                                           # After fix in planarity.py (num_edges_target = max(min_edges_for_connected, num_edges_target))
                                           # max_edges_for_triangulation = 3*3-6 = 3.
                                           # min_target_edges = int(0.8 * 3) = 2.
                                           # min_for_connectivity = 3-1 = 2.
                                           # lower_bound = max(2,2) = 2. upper_bound = 3. Range [2,3].

    def test_generate_n4(self):
        self._run_graph_generation_test(4) # Triangulation: 6 edges. Target: max(3, int(0.8*6)=4) to 6. Range [4,6]

    def test_generate_n5(self):
        self._run_graph_generation_test(5) # Triangulation: 9 edges. Target: max(4, int(0.8*9)=7) to 9. Range [7,9]

    def test_generate_n10(self):
        self._run_graph_generation_test(10) # Triangulation: 24 edges. Target: max(9, int(0.8*24)=19) to 24. Range [19,24]

    def test_generate_n20(self):
        self._run_graph_generation_test(20) # Triangulation: 54 edges. Target: max(19, int(0.8*54)=43) to 54. Range [43,54]
