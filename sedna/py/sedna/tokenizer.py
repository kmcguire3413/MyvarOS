"""
	The module documentation.
"""
#!python3
import json

class Token:
	"""
		Provides a highly polymorphic object that can represent any token type.

		This object is heavily used in tokenization. At a minimum it supports a
		type field and value for that type field along with line numbers and
		line position. If `xvalue` in the constructor is a dictionary then the
		items of the dictionary will become attributes of the object.

		During serialization to XML or JSON this object is serialized using
		its attributes. The attributes can be assigned externaly or through
		the `xvalue` parameter of the constructor.
	"""
	def __init__(self, xtype=None, xvalue=True, line_num='?', line_pos='?'):
		"""
			Create a new instance of this object.
		"""
		self.line_pos = line_pos
		self.line_num = line_num

		self.xtype = xtype
		
		if type(xvalue) is dict:
			setattr(self, xtype, True)
			for k in xvalue:
				setattr(self, k, xvalue[k])
		else:
			setattr(self, xtype, xvalue)

	def new(self, xtype, xvalue):
		"""
			Create a new instance of this object that uses the same
			line number and line position as this instance.
		"""
		return Token(xtype, xvalue, self.line_num, self.line_pos) 

	def __getattr__(self, name):
		"""
			Any attribute not present does not throw an exception but
			instead returns false. This allows lazy testing for attributes
			which makes it easy to write code.
		"""
		return False

	def get_json_form(self):
		"""
			The standard for serialization and movement of tokenized data
			to later stages of processing. This is a promotes agnostic data
			structures between major stages of the system.
		"""
		def json_value(v):
			vt = type(v)

			if vt is str:
				return v 
			elif vt is int:
				return v
			elif vt is float:
				return v
			elif vt is list:
				out = []
				for item in v:
					if type(item) is Token:
						out.append(item.get_json_form())
					else:
						out.append(json_value(item))
				return out
			elif vt is dict:
				out = {}
				for k in v:
					if type(v[k]) is Token:
						out[k] = v[k].get_json_form()
					else:
						out[k] = json_value(v[k])
				return out
			elif vt is tuple:
				return list(v)
			else:
				return None

		out = {}

		for k in self.__dict__.keys():
			if k[0] == '_':
				continue
			if k == self.xtype:
				kn = 'value'
			else:
				kn = k

			v = getattr(self, k)

			out[kn] = json_value(v)

		return out

	def __repr__(self):
		"""
			Provides ability to print object or give a debugging ability but does
			not present a stable output.
		"""
		if self.is_stmt_dec:
			return 'is_stmt_dec typename: %s generics: %s' % (self.typename, self.generic_args)
		elif self.is_invocation:
			return 'is_invocation var: %s args-count: %s' % (self.name_parts, len(self.args))
		elif self.is_stmt_assignment:
			return 'is_stmt_assignment destination-variable: %s' % self.dst
		else:
			return '%s: %s' % (self.xtype, getattr(self, self.xtype))


class Reader:
	"""
		Provides incremental reading of a single dimensional list like object.

		This is used to read single dimensional lists of objects such as but
		not limited to tokens, characters, or bytes. This is used when reading
		the individual characters of the source file and transforming them into
		tokens. It is also used to read those same produced tokens to produce
		higher level tokens.

		This class is heavily used in all of the tokenization passes.
	"""
	def __init__(self, data):
		self.data = data
		self.pos = 0

	def one(self):
		"""
			Read current item and advance the position by one.
		"""
		tmp = self.data[self.pos]
		self.pos += 1
		return tmp

	def peek_one(self):
		"""
			Read current item but do _NOT_ advance position.
		"""
		return self.data[self.pos]

	def peek_next(self):
		"""
			Read next item but do _NOT_ advance position.
		"""
		return self.data[self.pos + 1]

	def has_more(self):
		"""
			Returns `True` if more items can be read.
		"""
		if self.pos < len(self.data):
			return True
		return False

def tokenizer_read_string(data):
	"""
		Reads a string encapsulated by quotes.
	"""
	if data.one() != '"':
		raise Exception('Invalid character for string "%s"' % data.peek_one())
	s = []
	while data.peek_one() != '"':
		s.append(data.one())
	data.one()

	return ''.join(s)

def tokenizer_read_char(data):
	"""
		Reads a character encapsulated by single quotes.
	"""
	if data.one() != '\'':
		raise Exception('Invalid character for string "%s"' % data.peek_one())
	if data.peek_next() != '\'':
		raise Exception('Invalid character for string "%s"' % data.peek_one())
	c = data.one()
	data.one()
	return c
	
def tokenizer_read_number(data):
	"""
		Reads a decimal, hexidecimal, or binary number.

		The hexidecimal is prefixed by `0x` and binary by `0b`.
	"""
	xallow = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

	whole = []
	frac = []

	f = data.one()
	if f == '0':
		t = data.one()
		if t == 'x':
			xallow = xallow + ['a', 'b', 'c', 'd', 'e', 'f', 'A', 'B', 'C', 'D', 'E', 'F']
		elif t == 'b':
			xallow = ['0', '1']
		elif t.isdecimal():
			# allow float
			xallow.append('.')
			whole.append(f)
		else:
			raise Exception('Invalid character in number. Expected "x" for hex or "b" for binary or decimal for decimal.')
	else:
		whole.append(f)

	cur = whole
	while data.peek_one() in xallow:
		if data.peek_one() == '.':
			cur = frac
		cur.append(data.one())

	# hold as true float no matter actual type
	whole = ''.join(whole)
	if len(frac) > 0:
		frac = ''.join(frac)
	else:
		frac = '0'

	return (int(whole), int(frac))

def tokenizer_read_name(data):
	"""
		Read a name or also known as an identifier. 

		This is mostly variable names or object member references. The `.` character
		is used to support reading not only single object member references but
		also nested member references.
	"""
	tmp = []

	while data.peek_one() == '_' or data.peek_one() == '.' or data.peek_one().isalnum():
		tmp.append(data.one())

	return ''.join(tmp)


def tokenizer_read_block_comment(data):
	"""
		Read a comment started with `/*` and terminated with
		`*/`.
	"""
	while data.one() != '*' and data.peek_one() != '/':
		pass

def tokenizer_read_line_comment(data):
	"""
		Read a single line comment started by `//`.
	"""
	while data.peek_one() != '\n' or data.peek_one() != '\r':
		pass
	data.one()

def tokenizer_one(data):
	"""
		Returns first level tokenization.
	"""
	data = list(data)
	data = Reader(data)

	inside_var_ref = False
	inside_string = False
	inside_number = False

	number_type = None

	scmap = {
		'*': 'is_mul',
		'+': 'is_add',
		'/': 'is_div',
		'.': 'is_dot',
		'=': 'is_equal',
		'{': 'is_curly_open',
		'}': 'is_curly_close',
		'<': 'is_less',
		'>': 'is_greater',
		'[': 'is_sq_open',
		']': 'is_sq_close',
		'(': 'is_para_open',
		')': 'is_para_close',
		'%': 'is_mod',
		'|': 'is_bit_or',
		'&': 'is_bit_and',
		'^': 'is_bit_xor',
		';': 'is_semi_colon',
		':': 'is_colon',
		',': 'is_comma',
		'@': 'is_atsym',
	}

	tokens = []

	line_num = 1
	line_pos = 0

	while data.has_more():
		c = data.peek_one()
		if c == ' ':
			data.one()
		elif c == '\t':
			data.one()
		elif c == '"':
			tokens.append(Token('is_string', tokenizer_read_string(data), line_num, line_pos))
		elif c == '\'':
			tokens.append(Token('is_char', tokenizer_read_char(data), line_num, line_pos))
		elif c.isdecimal():
			tokens.append(Token('is_number', tokenizer_read_number(data), line_num, line_pos))
		elif c.isalpha():
			tokens.append(Token('is_name', tokenizer_read_name(data), line_num, line_pos))
		elif c == '/':
			if data.peek_next() == '*':
				tokenizer_read_block_comment(data)
			elif data.peek_next() == '/':
				tokenizer_read_line_comment(data)
			else:
				data.one()
				tokens.append(Token(scmap[c], True, line_num, line_pos))
		elif c in scmap:
			data.one()
			tokens.append(Token(scmap[c], True, line_num, line_pos))
		elif c == '\n' or c == '\r':
			data.one()
			line_num += 1
			line_pos = 0
		else:
			raise Exception('Unrecognized character "%s" at line %s position %s' % (c, line_num, line_pos))
		line_pos += 1

	return tokens

def tokenizer_read_scope_name(tokens):
	parts = []

	while True:
		if tokens.peek_one().is_name:
			parts.append(tokens.one().is_name)
		elif tokens.peek_one().is_dot:
			pass
		else:
			break

	return '.'.join(parts)

def error_token(token, msg):
	raise Exception('Line %s Pos %s: %s' % (token.line_num, token.line_pos, msg))

def tokenizer_two(tokens):
	tokens = Reader(tokens)
	out = []

	while tokens.has_more():
		tok = tokens.one()

		if tok.is_name == 'imports':
			if tokens.peek_one().is_name:
				ntok = tok.new('is_stmt_import', tokens.one().is_name)
				out.append(ntok)
			else:
				error_token(tokens[x], 'Expected import name but got %s' % tokens.peek_one())
		elif tok.is_name == 'scope':
			if tokens.peek_one().is_name:
				out.append(tok.new('is_stmt_scope', tokenizer_read_scope_name(tokens)))
			else:
				error_token(tokens[x], 'Expected scope name but got %s' % tokens.peek_one())				
		elif tok.is_atsym:
			if tokens.peek_one().is_name:
				out.append(tok.new('is_attribute', tokens.one().is_name))
		elif tok.is_name == 'type':
			nme = tokens.one()
			if tokens.one().is_curly_open and nme.is_name:
				out.append(tok.new('is_stmt_type', nme.is_name))
			else:
				error_token(tok, 'Expected type name and curly brace.')
		elif tok.is_name == 'fn':
			nme = tokens.one()
			if not nme.is_name:
				error_token(tok, 'Expected function name but got %s' % nme)
			if not tokens.one().is_para_open:
				error_token(tok, 'Expected parathesis after function name.')
			args = []
			while tokens.has_more and not tokens.peek_one().is_para_close:
				if tokens.peek_one().is_comma:
					args.append([])
				if len(args) < 0:
					args.append([])
				args[-1].append(token.one())
			if not tokens.one().is_para_close:
				error_token(nme, 'Expected closing parathesis after function name.')
			out.append(tok.new('is_stmt_fn', {
				'name':     nme.is_name,
				'args':     args,
			}))
		else:
			out.append(tok)

	tokens = Reader(out)
	out = []

	while tokens.has_more():
		tok = tokens.one()

		if tok.is_stmt_fn:
			# This takes all tokens and accumulates them into the function body. Then
			# those tokens are parsed into an AST.
			if not tokens.one().is_curly_open:
				error_token(tok, 'Expected curly brace after function implementation start.')
			body = []

			d = 1
			while not (tokens.peek_one().is_curly_close and d == 1):
				ctok = tokens.one()
				if ctok.is_curly_open:
					d += 1
				elif ctok.is_curly_close:
					d -= 1
				body.append(ctok)
			tokens.one()
			tok.body = body
			tok.body = tokenize_body(tok.body)
			out.append(tok)
		else:
			out.append(tok)

	return out

def tokenizer_three(tokens):
	tokens = Reader(tokens)

	out = []

	while tokens.has_more():
		tok = tokens.one()

		if tok.is_stmt_type is not False:
			body = []
			while not tokens.peek_one().is_curly_close:
				body.append(tokens.one())
			tokens.one()
			tok.body = body
			out.append(tok)
		else:
			out.append(tok)

	return out

def tokenize_expression(exp):
	tokens = Reader(exp)

	out = []

	while tokens.has_more():
		tok = tokens.one()

		if tok.is_name and tokens.has_more() and tokens.peek_one().is_para_open:
			'''
				Invocation of sub-routine/method/function.
			'''
			ntok = tok.new('is_invocation', True)
			ntok.name_parts = tok.is_name.split('.')

			for p in ntok.name_parts:
				if len(p) < 1:
					error_token(tok, 'The identifier must not have successive dots or empty entries before or after dots such as "%s"' % tok.is_name)

			tokens.one()

			args = []

			d = 1
			while not (tokens.peek_one().is_para_close and d == 1):
				ctok = tokens.one()

				if len(args) < 1:
					args.append([])

				if ctok.is_para_open:
					d += 1
				if ctok.is_para_close:
					d -= 1

				if ctok.is_comma and d == 1:
					args.append([])
				else:
					args[-1].append(ctok)

			tokens.one()

			for x in range(0, len(args)):
				args[x] = tokenize_expression(args[x])

			ntok.args = args
			out.append(ntok)
		elif tok.is_greater:
			if tokens.peek_one().is_equal:
				out.append(tok.new('is_eq_or_greater'))
			else:
				out.append(tok)
		elif tok.is_less:
			if tokens.peek_one().is_equal:
				out.append(tok.new('is_eq_or_less'))
			else:
				out.append(tok)
		elif tok.is_para_open:
			subexp = []
			d = 1
			while not (tokens.peek_one().is_para_close and d == 1):
				tmp = tokens.one()
				if tmp.is_para_open:
					d += 1
				elif tmp.is_para_close:
					d -= 1
				subexp.append(tmp)
			tokens.one()

			subexp = tokenize_expression(subexp)

			ntok = tok.new('is_subexpression', {
				'body': subexp
			})
			out.append(ntok)
		else:
			out.append(tok)
	return out

def tokenize_body(body):
	"""
		Handles creating higher level tokenization.

		if, for, dec, assignment, as (casting)
	"""
	tokens = Reader(body)

	out = []

	while tokens.has_more():
		tok = tokens.one()

		if tok.is_name == 'if':
			'''
				The if statement.
			'''
			tmp = tokens.one()
			if not tmp.is_para_open:
				error_token(tok, 'Expected open parathesis, after if keyword, but found %s' % tmp)

			exp = []

			while not tokens.peek_one().is_para_close:
				exp.append(tokens.one())
			tokens.one()

			tmp = tokens.one()
			if not tmp.is_curly_open:
				error_token(tok, 'Expected open curly braces after if keyword expression but found %s' % tmp)

			cond_true = []
			cond_false = []

			d = 1
			while not (tokens.peek_one().is_curly_close and d == 1):
				tmp = tokens.one()
				
				if tmp.is_curly_open:
					d += 1
				elif tmp.is_curly_close:
					d -= 1

				cond_true.append(tmp)
			tokens.one()

			if tokens.has_more() and tokens.peek_one().is_name == 'else':
				tokens.one()
				if not tokens.peek_one().is_curly_open:
					error_token(tok, 'Expected open curly brace after else keyword.')
				tokens.one()

				d = 1
				while not (tokens.peek_one().is_curly_close and d == 1):
					ctok = tokens.one()
					if ctok.is_curly_open:
						d += 1
					if ctok.is_curly_close:
						d -= 1
					cond_false.append(ctok)

				tokens.one()

			ntok = tok.new('is_stmt_if', {
				'cond_true': tokenize_body(cond_true),
				'cond_false': tokenize_body(cond_false),
				'cond': exp,
			})

			out.append(ntok)
		elif tok.is_name and tokens.has_more() and tokens.peek_one().is_para_open:
			exp = [tok]
			while not tokens.peek_one().is_semi_colon:
				exp.append(tokens.one())
			tokens.one()
			exp = tokenize_expression(exp)

			ntok = tok.new('is_stmt_assignment', {
				'body': exp,
				# No destination, but execute the code. I figure
				# the optimizer can come in and remove any dead
				# or useless code later. See note below.
				'dst': None,
			})

			'''
				Note 1:
					It is possible to have a statement like this:
						method0() + 3 + 4 + method1()
					While, the output is essentially useless the possibility
					of side-effects is enormous. It is impossible to know
					what the methods actually do unless optimization type
					analyze is employed in order to determine there is no
					effect created.

					So, the assignment operation is created since it can easily
					represent this type of /dev/null output operation.
			'''
			out.append(ntok)
		elif tok.is_name and tokens.peek_one().is_equal:
			'''
				The assignment statement.
			'''
			assign_to = tok.is_name

			expression = []

			tokens.one()

			while not tokens.peek_one().is_semi_colon:
				expression.append(tokens.one())
			tokens.one()

			ntok = tok.new('is_stmt_assignment', True)
			ntok.body = tokenize_expression(expression)
			ntok.dst = assign_to
			out.append(ntok)
		elif tok.is_name == 'dec':
			'''
				The variable declaration statement.
			'''
			if not tokens.peek_one().is_name:
				error_token(tok, 'Expected variable name after dec keyword.')
			varname = tokens.one().is_name

			if tokens.peek_one().is_semi_colon:
				out.one()
				out.append(tok.new('is_stmt_dec', {
					'name': varname,
					'type': None,
				}))
			elif tokens.peek_one().is_colon:
				tokens.one()
				args = []
				
				while not tokens.peek_one().is_semi_colon:
					args.append(tokens.one())
				tokens.one()

				ntok = tok.new('is_stmt_dec', True)

				z = 0
				x = 0
				while x < len(args):
					arg = args[x]
					if arg.is_name == 'move':
						ntok.is_move = True 
						args = args[0:x] + args[x+1:]
						z = z + 1
					elif arg.is_name == 'copy':
						ntok.is_copy = True 
						args = args[0:x] + args[x+1:]
						z = z + 1
					elif arg.is_name == 'reference':
						ntok.is_ref = True
						args = args[0:x] + args[x+1:]
						z = z + 1
					else:
						x += 1

				if z > 1:
					error_token(tok, 'The variable can only have one of move, copy, or ref.')

				def read_generic_types(tokens):
					args = []
					d = 1

					if not tokens.peek_one().is_name:
						error_token(tokens.peek_one(), 'Expected variable type name after any attributes.')

					vname = tokens.one()

					if tokens.has_more():
						if not tokens.peek_one().is_less:
							error_token(vname, 'Only expected generic arguments after typename.')
						tokens.one()
					else:
						return {
							'typename':    		vname.is_name,
							'generic_args':		[],
						}

					# Get value of `is_name`, aka the actual name.
					vname = vname.is_name

					while not (tokens.peek_one().is_greater and d == 1):
						if len(args) == 0:
							args.append([])
						
						if tokens.peek_one().is_less:
							d += 1
						elif tokens.peek_one().is_greater:
							d -= 1

						if d == 1 and tokens.peek_one().is_comma:
							args.append([])
							tokens.one()
						else:
							args[-1].append(tokens.one())

					# Further resolve the sub-types if needed.
					for x in range(0, len(args)):
						_r = Reader(args[x])
						args[x] = read_generic_types(_r)

					return {
						'typename': 		vname,
						'generic_args':		args,
					}

				_r = Reader(args)

				info = read_generic_types(_r)
				ntok.name = varname
				ntok.typename = info['typename']
				ntok.generic_args = info['generic_args']
				out.append(ntok)
			else:
				error_token(tok, 'Expected semi-colon or colon after variable name when using dec keyword.')
		elif tok.is_name == 'for':
			tok = tokens.one()
			if not tok.is_para_open:
				error_token(tok, 'Expected opening parathesis after for keyword.')

			args = [[]]

			while not tokens.peek_one().is_para_close:
				ctok = tokens.one()
				if ctok.is_semi_colon:
					args.append([])
				else:
					args[-1].append(ctok)

			if not tokens.one().is_curly_open:
				error_token(tok, 'Expected opening curly brace after for keyword arguments.')

			body = []

			d = 1
			while not (tokens.peek_one().is_curly_close and d == 1):
				ctok = tokens.one()
				if ctok.is_curly_open:
					d += 1
				if ctok.is_curly_close:
					d -= 1
				body.append(ctok)

			tokens.one()

			ntok = tok.new('is_stmt_for', {
				'args': args,
				'body': tokenize_body(body),
			})

			out.append(ntok)
		else:
			out.append(tok)

	if len(out) > 0:
		line_num = out[0].line_num
		line_pos = out[0].line_pos
	else:
		line_num = '?'
		line_pos = '?'

	return out

def dump_tokens_json_form(tokens):
	out = []

	for tok in tokens:
		j = tok.get_json_form()
		out.append(j)

	return out


def dump_tokens(tokens, depth=1, do_xml=False):
	if depth == 1:
		print('<module>', end='')
	padsym = '   '
	pad = padsym * depth
	for tok in tokens:
		if do_xml:
			print(tok.get_xml_open(), end='')
		else:
			print('%s %s' % (pad, tok))
		if tok.args:
			for x in range(0, len(tok.args)):
				arg = tok.args[x]
				if do_xml:
					print('<arg>', end='')
					dump_tokens(arg, depth + 2, do_xml)
					print('</arg>', end='')
				else:
					print('%sarg[%s]' % (padsym * (depth + 1), x))
					dump_tokens(arg, depth + 2, do_xml)
		if tok.body:
			if do_xml:
				print('<body>', end='')
			dump_tokens(tok.body, depth + 1, do_xml)
			if do_xml:
				print('</body>', end='')
		if tok.cond_true:
			if do_xml:
				print('<cond_true>')
			dump_tokens(tok.cond_true, depth + 1, do_xml)
			if do_xml:
				print('</cond_true>')
		if tok.cond_false:
			if do_xml:
				print('<cond_false>')
			dump_tokens(tok.cond_false, depth + 1, do_xml)
			if do_xml:
				print('</cond_false>')
		if do_xml:
			print(tok.get_xml_close(), end='')
	if depth == 1:
		print('</module>', end='')

"""
	Do full tokenization.
"""
def tokenizer(data):
	mods = [
		tokenizer_one,
		tokenizer_two,
		tokenizer_three,
	]

	tokens = data
	for mod in mods:
		tokens = mod(tokens)

	#dump_tokens(tokens, do_xml=True)
	return dump_tokens_json_form(tokens)