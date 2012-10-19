from pyc_astvisitor import ASTTxformer
from pyc_astvisitor import ASTVisitor
import pyc_vis
from pyc_log import *
import pyc_gen_name
from pyc_validator import assert_valid

import ast
import copy

class Localizer(ASTTxformer):
	
	def __init__(self):
		ASTTxformer.__init__(self)
		self.log = log
		self.scope = "main"

	def scope_fmt(self, s):
		return "%s_%s" % (self.scope, s)

	def visit_Module(self, node):
		locs = locals(node)
		self.log(self.depth_fmt("locals: %r" % locs) )

		mappy = {}
		for loco in locs:
			mappy[loco] = self.scope_fmt(loco)

		return ast.Module(
			body = [pyc_vis.visit(self, n, mappy) for n in node.body]
		)

	def visit_Name(self, node, mappy):
		return ast.Name(
			id = mappy[node.id],
			ctx = node.ctx
		)

	def visit_FunctionDef(self, node, mappy):
		fn_name = mappy[node.name]

		(new_args, new_body) = self.localize_lambda(node, mappy, fn_name)
		return ast.FunctionDef(
			name = fn_name,
			args = ast.arguments(
				args = new_args,
				vararg = None,
				kwarg = None
			),
			body = new_body
		)

	def visit_Lambda(self, node, mappy):
		name = pyc_gen_name.new(self.scope_fmt("l"))
		(new_args, new_body) = self.localize_lambda(node, mappy, name)
		return ast.Lambda(
			args = new_args,
			body = new_body[0]
		)

	def localize_lambda(self, node, mappy, lam_name):
		assert_valid(node)

		locs = locals(node)
		self.log(self.depth_fmt("locals: %r" % locs) )

		lam_mappy = copy.copy(mappy) #dont need deep copy, its a shallow dict
		self.scope = lam_name
		for loco in locs:
			lam_mappy[loco] = self.scope_fmt(loco)

		body = [node.body] if isinstance(node, ast.Lambda) else node.body
		return (
			pyc_vis.visit(self, node.args, lam_mappy),
			[pyc_vis.visit(self, n, lam_mappy) for n in body]
		)

		
class LocalFinder(pyc_vis.Visitor):
	
	def __init__(self, root):
		pyc_vis.Visitor.__init__(self)
		self.root = root

	def default(self, node):
		return set([])

	def iterate_and_visit(self, ls):
		locals = set([])
		for n in ls:
			locals = locals | pyc_vis.visit(self, n)

		return locals
		
	def visit_Module(self, node):
		if node != self.root:
			raise Exception("shouldnt get here!")

		return self.iterate_and_visit(node.body)

	def visit_Assign(self, node):
		return self.iterate_and_visit(node.targets)

	def visit_Name(self, node):
		return set([node.id])

	def visit_Subscript(self, node):
		return pyc_vis.visit(self, node.value)

	def visit_FunctionDef(self, node):
		if self.root != node:
			return set([node.name])
		else:
			return (
				self.iterate_and_visit(node.args.args)
					| self.iterate_and_visit(node.body)
			)

	def visit_Lambda(self, node):
		if self.root != node:
			return set([])
		else:
			return (
				self.iterate_and_visit(node.args.args)
					| pyc_vis.visit(self, node.body)
			)

def locals(node):
	lf = LocalFinder(node)
	#lf.log = lambda s: log("LocalFinder: %s" % s)
	return pyc_vis.walk(lf, node)

def txform(as_tree):
	v = Localizer()
	#v.log = lambda s: log("Localizer  : %s" % s)
	return pyc_vis.walk(v, as_tree)