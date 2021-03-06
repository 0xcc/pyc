# Copyright 2013 anthony cantor
# This file is part of pyc.
# 
# pyc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# pyc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with pyc.  If not, see <http://www.gnu.org/licenses/>.
from pyc_astvisitor import ASTTxformer
import pyc_vis
from pyc_log import *
from pyc_ir_nodes import *
import pyc_gen_name
from pyc_localize import locals
from pyc_constants import BadAss

import ast
import copy

def vis_fn(visitor, node, name, scope):
	locs = locals(node)
	fnscope = locs | scope 

	return ast.FunctionDef(
		name = name,
		args = pyc_vis.visit(visitor, node.args, fnscope),
		body = [
			pyc_vis.visit(visitor, n, fnscope) for n in node.body
		]
	)

def vis_cd(visitor, node, name, scope):
	if not isinstance(name, str):
		raise Exception("name must be a string")

	tmpname = pyc_gen_name.new("0class")
	bt = BodyTxformer(node, visitor, tmpname, scope) 
	bt.tracer = visitor.tracer
	bt.log = lambda s: log("BodyTxformer : %s" % s)

	return Seq(
		body = (
			[make_assign(
				var_set(tmpname), 
				ClassRef(
					bases=ast.List(
						elts = [
							pyc_vis.visit(visitor, b) for b in node.bases
						],
						ctx = ast.Load()
					)
				)
			)] + \
			pyc_vis.visit(bt, node).body + \
			[make_assign(
				var_set(name), 
				var_ref(tmpname)
			)]
		)
	)

class Declassifier(ASTTxformer):
	
	def __init__(self):
		ASTTxformer.__init__(self)

	def visit_Module(self, node):
		locs = locals(node)
		self.log(self.depth_fmt("locals: %r" % locs) )

		return ast.Module(
			body = [pyc_vis.visit(self, n, locs) for n in node.body]
		)

	def visit_FunctionDef(self, node, scope):
		return vis_fn(self, node, node.name, scope)

	def visit_ClassDef(self, node, scope):
		if not isinstance(node.name, str):
			raise BadAss("assumed ClassDef.name was always a string")

		return vis_cd(self, node, node.name, scope)

class BodyTxformer(ASTTxformer):
	
	def __init__(self, root, parent, refname, scope):
		ASTTxformer.__init__(self)
		self.root = root
		self.parent = parent
		self.scope = scope
		self.attrs = set([])
		self.refname = refname

	def visit_ClassDef(self, cd):
		if cd == self.root:
			
			return Seq(
				body = [
					pyc_vis.visit(self, n) for n in cd.body
				]
			)
		else:
			tmpname = pyc_gen_name.new(self.refname + "_classattr")
			return Seq(
				body = [
					vis_cd(self.parent, cd, tmpname, self.scope),
					self.sattr(cd.name, var_ref(tmpname))
				]
			)

	def sattr(self, name, val):
		self.attrs.add(name)

		return make_assign(
			ast.Attribute(
				value = var_ref(self.refname),
				attr = name,
				ctx = ast.Store()	
			),
			val
		)

	def visit_Lambda(self, node):
		return pyc_vis.visit(self.parent, node, self.scope)

	def visit_FunctionDef(self, node):
		tmpname = pyc_gen_name.new(self.refname + "_defattr")
		return Seq(
			body = [
				vis_fn(self.parent, node, tmpname, self.scope),
				self.sattr(node.name, var_ref(tmpname))
			]			
		)

	def visit_Assign(self, node):
		if len(node.targets) != 1:
			raise BadAss("expected singleton assign list")

		if isinstance(node.targets[0], ast.Name):
			return self.sattr(
				node.targets[0].id,
				pyc_vis.visit(self, node.value)
			)

		return make_assign(
			pyc_vis.visit(self, node.targets[0]),
			pyc_vis.visit(self, node.value)
		)

	def attr_access(self, name):
		return ast.Attribute(
			value = var_ref(self.refname),
			attr = name,
			ctx = ast.Load()
		)

	def visit_Name(self, node):
		if node.id in self.attrs:
			if node.id in self.scope:
				return ast.IfExp(
					test = HasAttr(
						obj=var_ref(self.refname),
						attr=ast.Str(node.id)
					),
					body = self.attr_access(node.id),
					orelse = copy_name(node)
				)
			else:
				return self.attr_access(node.id)

		return copy_name(node)

		
def txform(as_tree, **kwargs):
	v = Declassifier()
	v.log = lambda s: log("Declassifier : %s" % s)
	if 'tracer' in kwargs:
		v.tracer = kwargs['tracer']

	return pyc_vis.walk(v, as_tree)
