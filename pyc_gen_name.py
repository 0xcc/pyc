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

prefix_count = {
}

def new(prefix):
	global prefix_count
	if not prefix in prefix_count:
		prefix_count[prefix] = 0

	prefix_count[prefix] += 1
	n = "%s%d" % (prefix, prefix_count[prefix])
	
	return n

def user_name(s):
	return "user_%s" % s

