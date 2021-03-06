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
import pyc_vis
from pyc_log import log
import ast
import copy

class ASTVisitor(pyc_vis.Visitor):

	def __init__(self):
		pyc_vis.Visitor.__init__(self)
		self.pass_fields = False

	def default_accumulator(self):
		return set([])

	def default_accumulate(self, current, output):
		if output is None:
			return current

		return current | output

	def default(self, node, *args, **kwargs):
		result = self.default_accumulator()

		if isinstance(node, ast.AST):
			result = self.default_accumulate(result, self.default_ast(node, *args, **kwargs))

			for (fld, value) in ast.iter_fields(node):
				#print "%s => %s" % (fld, value.__class__.__name__)
			
				if isinstance(value, list):
					for i in range(0, len(value) ):
						if self.pass_fields:
							kwargs["field"] = fld + ("[%d]" % i)

						result = self.default_accumulate(
							result,
							pyc_vis.visit(self, value[i], *args, **kwargs)
						)
				else:
					if self.pass_fields:
						kwargs["field"] = fld

					result = self.default_accumulate(
						result,
						pyc_vis.visit(self, value, *args, **kwargs)
					)

		else:
			#print "non ast:"
			result = self.default_non_ast(node, *args, **kwargs)

		return result


class ASTSearcher(ASTVisitor):
	
	def default_ast(self, node, *args, **kwargs):
		return set([])

	def default_non_ast(self, node, *args, **kwargs):
		return set([])

class ASTTxformer(pyc_vis.Visitor):
	def __init__(self):
		pyc_vis.Visitor.__init__(self)

	def default_accumulator(self):
		return None

	def default_accumulate(self, current, output):
		return (output, None)

	def default(self, node, *args, **kwargs):
		result = self.default_accumulator()

		#print "%s" % node.__class__.__name__
		new_node = node.__class__()
		for field, old_value in ast.iter_fields(node):
			#print "%s => %s" % (field, old_value.__class__.__name__)
			if isinstance(old_value, list):
				new_values = []
				for value in old_value:
					if isinstance(value, ast.AST):
						value = pyc_vis.visit(self, value, *args, **kwargs)
						(value, result) = self.default_accumulate(result, value)
						if value is None:
							continue
						elif not isinstance(value, ast.AST):
							if value.__class__ not in set([list, tuple]):
								raise Exception("didnt expect returned value of (%s) %r" % (value.__class__.__name__, value) )

							new_values.extend(value)
							continue

					new_values.append(value)
				setattr(new_node, field, new_values)
			elif isinstance(old_value, ast.AST):
				new_child = pyc_vis.visit(self, old_value, *args, **kwargs)
				(new_child, result) = self.default_accumulate(result, new_child)
				if not new_child is None:
					setattr(new_node, field, new_child)

			elif isinstance(old_value, int) \
					or isinstance(old_value, str) \
					or old_value is None:
				setattr(new_node, field, old_value)

			else:
				raise Exception(
					"didnt expect to copy field %r with class %r in node %s" % (
						old_value, 
						old_value.__class__, 
						ast.dump(node)
					) 
				)

		if result is None:
			return new_node
		else:
			return (new_node, result)


def names(node):

	class NameFinder(ASTSearcher):

		def visit_Name(self, node, *args, **kwargs):
			return set([node.id])

	v = NameFinder()
	#v.log = lambda s: log("NameFinder  : %s" % s)
	return pyc_vis.walk(v, node)

