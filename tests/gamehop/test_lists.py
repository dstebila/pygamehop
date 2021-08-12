import unittest
from gamehop.lists import *

class TestFilterAST(unittest.TestCase):
    def test_new_empty_list(self):
        def f():
            return new_empty_list()
        self.assertEqual(f(), ())

    def test_append_item(self):
        def f():
            l1 = new_empty_list()
            l2 = append_item(l1, 3)
            return l2
        self.assertEqual(f(), (3,))

    def test_set_item(self):
        def f():
            l1 = new_empty_list()
            l2 = append_item(l1, 3)
            l3 = set_item(l2, 0, 4)
            return l3
        self.assertEqual(f(), (4,))

    def test_set_item(self):
        def f():
            l1 = new_empty_list()
            l2 = append_item(l1, 3)
            return get_item(l2, 0)
        self.assertEqual(f(), 3)


    def test_index_of(self):
        def f():
            l1 = new_empty_list()
            l2 = append_item(l1, 3)
            l3 = append_item(l2, 4)
            l4 = append_item(l3, 5)
            return index_of(l4, 4)
        self.assertEqual(f(), 1)

    def test_concat(self):
        def f():
            l1 = new_empty_list()
            l2 = append_item(l1, 3)
            l3 = append_item(l2, 4)
            l4 = append_item(l3, 5)
            return concat(l3, l4)
        self.assertEqual(f(), (3,4,3,4,5))

    def test_slice(self):
        def f():
            l1 = new_empty_list()
            l2 = append_item(l1, 3)
            l3 = append_item(l2, 4)
            l4 = append_item(l3, 5)
            l5 = append_item(l4, 6)
            return slice(l4, 1, 3)
        self.assertEqual(f(), (4,5))
    def test_slice_step(self):
        def f():
            l1 = tuple(range(0, 5))
            return slice(l1, 3, 1, -1)
        self.assertEqual(f(), (3, 2))
