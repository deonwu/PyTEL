import pprint
import re
import sys
import unittest
from pytel.ast import c_ast


class Test_c_ast(unittest.TestCase):
    def test_BinaryOp(self):
        b1 = c_ast.BinaryOp(
            op='+', 
            left=c_ast.Constant(type='int', value='6'),
            right=c_ast.ID(name='joe'))

        self.failUnless(isinstance(b1.left, c_ast.Constant))
        self.assertEqual(b1.left.type, 'int')
        self.assertEqual(b1.left.value, '6')
        
        self.failUnless(isinstance(b1.right, c_ast.ID))
        self.assertEqual(b1.right.name, 'joe')


class TestNodeVisitor(unittest.TestCase):
    class ConstantVisitor(c_ast.NodeVisitor):
        def __init__(self):
            self.values = []
        
        def visit_Constant(self, node):
            self.values.append(node.value)
    
    def test_scalar_children(self):
        b1 = c_ast.BinaryOp(
            op='+', 
            left=c_ast.Constant(type='int', value='6'),
            right=c_ast.ID(name='joe'))
    
        cv = self.ConstantVisitor()
        cv.visit(b1)
        
        self.assertEqual(cv.values, ['6'])
        
        b2 = c_ast.BinaryOp(
            op='*',
            left=c_ast.Constant(type='int', value='111'),
            right=b1)
        
        b3 = c_ast.BinaryOp(
            op='^',
            left=b2,
            right=b1)
        
        cv = self.ConstantVisitor()
        cv.visit(b3)
        
        self.assertEqual(cv.values, ['111', '6', '6'])

    def tests_list_children(self):
        c1 = c_ast.Constant(type='float', value='5.6')
        c2 = c_ast.Constant(type='char', value='t')
        
        b1 = c_ast.BinaryOp(
            op='+',
            left=c1,
            right=c2)
        
        b2 = c_ast.BinaryOp(
            op='-',
            left=b1,
            right=c2)

        comp = c_ast.Compound(
            decls=[b1, b2],
            stmts=[c1, c2])
        
        cv = self.ConstantVisitor()
        cv.visit(comp)
        
        self.assertEqual(cv.values, 
            ['5.6', 't', '5.6', 't', 't', '5.6', 't'])


if __name__ == '__main__':
    unittest.main()




