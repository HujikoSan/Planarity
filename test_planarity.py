import unittest
from planarity import on_segment, orientation, do_lines_intersect, get_crossing_edges # Updated import

class TestLineIntersection(unittest.TestCase):
    # No changes needed for TestLineIntersection, as do_lines_intersect remains the same.
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
