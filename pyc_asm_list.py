
from pyc_asm_nodes import *

class sym_table(dict):

	def __init__(self):
		self.stack = 0

	def type_size(self, type):
		if type == "long":
			return 4
		else:
			raise Exception("unknown type %s" % type)

	def push(self, type):
		size = self.type_size(type)
		self.stack += size

	def pop(self, type):
		size = type_size(type)
		self.stack -= size

		
		
def from_ss_list(ss_list):
	asm_list = []
	st = sym_table()

	print "convert simple statements to list of asm nodes"

	for ss in ss_list:
		asm_list.append(py_ss_to_asm(ss, st))


def py_ss_to_asm(ss, sym_tbl):
	if isinstance(ss, compiler.ast.Assign):
		return assign_to_asm(ss, sym_tbl)
	elif isinstance(ss, compiler.ast.Printnl):
		return printnl_to_asm(ss, sym_tbl)
	
	raise Exception("didnt expect ast node of type %s" % ss.__class__.__name__)

	
def assign_to_asm(assign, sym_tbl):
	print repr(assign)
	
	nodelen = len(assign.nodes)
	if nodelen != 1:
		raise Exception("expected Assign with a single assignment")

	sym = assign.nodes[0].name
	addr = None

	try:
		addr = sym_tbl[sym]
	except KeyError:
		pass
	
	if addr == None:
		addr = sym_tbl.stack	
		sym_tbl.push("long")
		
	result = set_mem(addr, assign.expr, sym_tbl)
	sym_tbl[sym] = addr
	

def set_mem(addr, expr, sym_tbl):
	if isinstance(expr, compiler.ast.Const):
		#movl $N, -(4+ADDR)(%ebp)
		return [Movl(Immed(Int(expr.value)), Indirect(Register("ebp"), addr) )]
	elif isinstance(expr, compiler.ast.Name):
		src_addr = sym_tbl[expr.name]
		if src_addr == addr:
			raise Exception("src and dest are equal: %d" % addr)

		return [
			Movl(Indirect(Register("ebp"), src_addr), Register("eax") ),
			Movl(Register("eax"), Indirect(Register("ebp"), addr) )
		]
	else:
		raise Exception("unexpected expr: %s" % expr.__class__.__name__)


def printnl_to_asm(printnl, sym_tbl):
	nodelen = len(printnl.nodes)

	print repr(printnl)
	
	if nodelen == 1:
		raise Exception("asdfasdf")	
	else:
		raise Exception("expected printnl with 1 node")
	