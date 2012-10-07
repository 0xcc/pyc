import pyc_vis
import ast
import copy

class ASTVisitor(pyc_vis.Visitor):

	def __init__(self):
		pyc_vis.Visitor.__init__(self)
	
	def default(self, node, *args):
		"""Called if no explicit visitor function exists for a node."""

		if isinstance(node, ast.AST):
			self.default_ast(node, *args)
			for (field, value) in ast.iter_fields(node):
				#print "%s => %s" % (field, value.__class__.__name__)
				if isinstance(value, list):
					for i in range(0, len(value) ):
						pyc_vis.visit(self, value[i], field + ("[%d]" % i) )
				else:
					pyc_vis.visit(self, value, field)

		else:
			#print "non ast:"
			self.default_non_ast(node, *args)

class ASTTxformer(pyc_vis.Visitor):
	def __init__(self):
		pyc_vis.Visitor.__init__(self)

	def default(self, node):
		new_node = node.__class__()
		for field, old_value in ast.iter_fields(node):
			old_value = getattr(node, field, None)
			if isinstance(old_value, list):
				new_values = []
				for value in old_value:
					if isinstance(value, ast.AST):
						value = pyc_vis.visit(self, value)
						if value is None:
							continue
						elif not isinstance(value, ast.AST):
							new_values.extend(value)
							continue
					new_values.append(value)
				setattr(new_node, field, new_values)
			elif isinstance(old_value, ast.AST):
				new_child = pyc_vis.visit(self, old_value)
				if not new_child is None:
					setattr(new_node, field, new_child)

			elif isinstance(old_value, int):
				setattr(new_node, field, old_value)

			else:
				raise Exception("didnt expect to copy field with class %r: %r" % (old_value.__class__, old_value) )

		return new_node
