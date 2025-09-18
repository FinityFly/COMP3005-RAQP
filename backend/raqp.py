import re
import json
"""
Multi relation not implemented
"""

class Relation:
	def __init__(self, name, columns, rows):
		self.name = name
		self.columns = columns
		self.rows = rows

class RAQPResult:
	def __init__(self, text, table):
		self.text = text
		self.table = table

class RAQP:
	relations = {}

	@staticmethod
	def process(input_text):
		rel_text, query_text = RAQP._split_input(input_text)
		RAQP.relations = RAQP._parse_relations(rel_text)

		parsed_query = RAQP._parse_query(query_text)
		print("="*20)
		print("Parsed Query Tree:")
		print(json.dumps(parsed_query, indent=2))
		print("="*20)

		result_rows, columns, rel_name = RAQP._execute(parsed_query)
		table = {"columns": columns, "rows": result_rows}
		if not result_rows:
			explanation = "No result."
		else:
			explanation = RAQP._format_output_text(rel_name, columns, result_rows)
		return RAQPResult(explanation, table)

	@staticmethod
	def _print_relation(rel):
		print(f"Relation: {rel.name}")
		# print(",\t".join(rel.columns))
		# for row in rel.rows:
		# 	print(",\t".join(row))
		# print()
		print(rel.columns)
		print(rel.rows)

	@staticmethod
	def _extract_relation_name(query_text):
		# Try to extract the correct relation name based on the operation
		# Handles select, project, join, union, intersect, diff
		if query_text.startswith('select') or query_text.startswith('project'):
			m = re.match(r'.*\((\w+)\)', query_text)
			if m:
				return m.group(1)
		elif query_text.startswith('join'):
			m = re.match(r'join\s*\((\w+),\s*(\w+),', query_text)
			if m:
				# Use left relation for join result name
				return m.group(1)
		elif query_text.startswith('union') or query_text.startswith('intersect') or query_text.startswith('diff'):
			m = re.match(r'.*\((\w+),\s*(\w+)\)', query_text)
			if m:
				# Use left relation for set operation result name
				return m.group(1)
		return "Result"

	@staticmethod
	def _format_output_text(rel_name, columns, rows):
		if not columns:
			return "No result."
		header = ', '.join(columns)
		lines = []
		for row in rows:
			formatted = []
			for val in row:
				if isinstance(val, str) and not val.isdigit():
					formatted.append(f'"{val}"')
				else:
					formatted.append(str(val))
			lines.append('  ' + ', '.join(formatted))
		result = f'{rel_name} = {{{header}\n' + '\n'.join(lines) + '\n}'
		return result

	@staticmethod
	def _split_input(input_text):
		parts = input_text.split('Query:')
		rel_text = parts[0].strip()
		query_text = parts[1].strip() if len(parts) > 1 else None
		if not query_text:
			raise ValueError("No query found in input.")

		return rel_text, query_text

	@staticmethod
	def _parse_relations(rel_text):
		relations = {}
		rel_pattern = re.compile(r'(\w+)\s*\(([^)]+)\)\s*=\s*{([^}]*)}', re.MULTILINE)
		for match in rel_pattern.finditer(rel_text):
			name = match.group(1)
			columns = [c.strip() for c in match.group(2).split(',')]
			rows_raw = match.group(3).strip().split('\n')
			rows = []
			for row in rows_raw:
				if row.strip():
					rows.append([v.strip() for v in row.split(',')])
			relations[name] = Relation(name, columns, rows)
		return relations

	@staticmethod
	def _parse_query(query_text):
		# Tokenize and parse respecting brackets and operator precedence
		# Supported ops: select, project, join, union, intersect, minus (-)
		# Returns a tree: {type, ...}
		def tokenize(s):
			# Add spaces around brackets and operators for easier splitting
			s = s.replace('(', ' ( ').replace(')', ' ) ')
			s = s.replace(',', ' , ')
			s = s.replace('=', ' = ')
			s = s.replace('>', ' > ').replace('<', ' < ')
			s = s.replace('-', ' - ')
			s = s.replace('union', ' union ').replace('intersect', ' intersect ')
			return s.split()

		# Helper to find matching closing bracket
		def find_matching(tokens, start):
			depth = 0
			for i in range(start, len(tokens)):
				if tokens[i] == '(': depth += 1
				elif tokens[i] == ')':
					depth -= 1
					if depth == 0:
						return i
			return -1

		# Recursive descent parser
		def parse(tokens):
			# Handle brackets
			if tokens and tokens[0] == '(':  # ( ... )
				end = find_matching(tokens, 0)
				if end == -1:
					raise Exception('Unmatched parenthesis')
				inner = parse(tokens[1:end])
				rest = tokens[end+1:]
				if rest:
					# Check for binary op after bracket
					if rest[0] in ['union', 'intersect', '-']:
						op = rest[0]
						right = parse(rest[1:])
						if op == 'union':
							return {'type': 'union', 'left': inner, 'right': right}
						elif op == 'intersect':
							return {'type': 'intersect', 'left': inner, 'right': right}
						elif op == '-':
							return {'type': 'minus', 'left': inner, 'right': right}
					else:
						return inner
				else:
					return inner
			# Binary ops: union, intersect, minus
			for op in ['union', 'intersect', '-']:
				if op in tokens:
					idx = tokens.index(op)
					left = parse(tokens[:idx])
					right = parse(tokens[idx+1:])
					if op == 'union':
						return {'type': 'union', 'left': left, 'right': right}
					elif op == 'intersect':
						return {'type': 'intersect', 'left': left, 'right': right}
					elif op == '-':
						return {'type': 'minus', 'left': left, 'right': right}
			# Unary ops: select, project
			if tokens and tokens[0] == 'select':
				# select cond (source)
				# Find first '('
				try:
					paren_idx = tokens.index('(')
					cond = ' '.join(tokens[1:paren_idx])
					end = find_matching(tokens, paren_idx)
					source = parse(tokens[paren_idx+1:end])
					return {'type': 'select', 'condition': cond, 'source': source}
				except Exception:
					raise Exception('Invalid select syntax')
			if tokens and tokens[0] == 'project':
				# project col1, col2 (source)
				try:
					paren_idx = tokens.index('(')
					cols = []
					for i in range(1, paren_idx):
						if tokens[i] != ',':
							cols.append(tokens[i])
					end = find_matching(tokens, paren_idx)
					source = parse(tokens[paren_idx+1:end])
					return {'type': 'project', 'columns': cols, 'source': source}
				except Exception:
					raise Exception('Invalid project syntax')
			# Join: rel1 join cond rel2
			if 'join' in tokens:
				idx = tokens.index('join')
				left = parse(tokens[:idx])
				# Find the condition and right relation
				# Condition ends at the start of the right relation (which is a token that matches a relation name or starts a bracket)
				cond_tokens = []
				i = idx+1
				# Find the '=' in the condition
				eq_idx = None
				for j in range(i, len(tokens)):
					if tokens[j] == '=':
						eq_idx = j
						break
				if eq_idx is not None:
					# Take left and right of '=' for condition
					left_cond = ' '.join(tokens[i:eq_idx]).strip()
					# Now, right of '=' may include the right relation name
					# Find the next token that is not part of the condition (i.e., not identifier, not dot, not '='), which is the start of the right relation
					k = eq_idx+1
					right_cond_tokens = []
					while k < len(tokens) and tokens[k] not in ['(', 'union', 'intersect', '-'] and not tokens[k].startswith('select') and not tokens[k].startswith('project') and not tokens[k] == 'join':
						right_cond_tokens.append(tokens[k])
						k += 1
					# The last token in right_cond_tokens is the right relation name
					if right_cond_tokens:
						right_relation_name = right_cond_tokens[-1]
						right_cond = ' '.join(right_cond_tokens[:-1]).strip()
						cond = f"{left_cond} = {right_cond}"
						right = parse([right_relation_name])
						# If there are more tokens after right relation, parse them as well (for nested joins etc)
						if k < len(tokens):
							# Compose right as a nested parse
							right = parse(tokens[k:])
						return {'type': 'join', 'left': left, 'right': right, 'condition': cond}
					else:
						# Fallback: treat everything after '=' as condition
						cond = f"{left_cond} = {' '.join(tokens[eq_idx+1:]).strip()}"
						right = None
						return {'type': 'join', 'left': left, 'right': right, 'condition': cond}
				else:
					# Fallback: treat everything after join as condition
					cond = ' '.join(tokens[i:]).strip()
					right = None
					return {'type': 'join', 'left': left, 'right': right, 'condition': cond}
			# relation if none of the above
			if tokens:
				name = ' '.join([t for t in tokens if t != ','])
				if name in RAQP.relations:
					return {'type': 'relation', 'name': name}
				else:
					raise Exception(f"Unknown relation/operator name: {name}")
			raise Exception('Could not parse query')

		tokens = tokenize(query_text)
		return parse(tokens)

	@staticmethod
	def _set_op_iterate(node):
		left_rows, left_cols, left_name = RAQP._execute(node['left'])
		right_rows, right_cols, right_name = RAQP._execute(node['right'])
		print(left_cols, left_rows)
		print(right_cols, right_rows)
		left_rel = Relation(left_name, left_cols, left_rows)
		right_rel = Relation(right_name, right_cols, right_rows)
		return left_rel, right_rel, left_name, left_cols

	@staticmethod
	def _execute(node):
		if node['type'] == 'relation':
			rel = RAQP.relations.get(node['name'])
			if not rel:
				return [], [], node['name']
			return rel.rows, rel.columns, node['name']
		elif node['type'] == 'select':
			rows, cols, rel_name = RAQP._execute(node['source'])
			temp_rel = Relation(rel_name, cols, rows)
			print("="*20)
			print()
			print("Selecting from Relation:", temp_rel.name, " | condition:", node['condition'])
			print("Relation:")
			RAQP._print_relation(temp_rel)
			print()
			filtered = RAQP._select(temp_rel, node['condition'])
			return filtered, cols, rel_name
		elif node['type'] == 'project':
			rows, cols, rel_name = RAQP._execute(node['source'])
			temp_rel = Relation(rel_name, cols, rows)
			print("="*20)
			print()
			print("Projecting from Relation:", temp_rel.name, " | columns:", node['columns'])
			print("Relation:")
			RAQP._print_relation(temp_rel)
			print()
			projected = RAQP._project(temp_rel, node['columns'])
			if isinstance(node['columns'], str):
				col_list = [c.strip() for c in node['columns'].split(',')]
			else:
				col_list = node['columns']
			return projected, col_list, rel_name
		elif node['type'] == 'join':
			left_rel, right_rel, left_name, left_cols = RAQP._set_op_iterate(node)
			print("="*20)
			print()
			print("Joining:", left_rel.name, "and", right_rel.name, " | condition:", node['condition'])
			print("Left Relation:")
			RAQP._print_relation(left_rel)
			print("Right Relation:")
			RAQP._print_relation(right_rel)
			print()
			joined_rows, joined_cols = RAQP._join(left_rel, right_rel, node['condition'])
			return joined_rows, joined_cols, left_name # left relation name for join result
		elif node['type'] == 'union':
			left_rel, right_rel, left_name, left_cols = RAQP._set_op_iterate(node)
			print("="*20)
			print()
			print("Unioning:", left_rel.name, "and", right_rel.name)
			print("Left Relation:")
			RAQP._print_relation(left_rel)
			print("Right Relation:")
			RAQP._print_relation(right_rel)
			print()
			result_rows = RAQP._union(left_rel, right_rel)
			return result_rows, left_cols, left_name # left relation name for union result
		elif node['type'] == 'intersect':
			left_rel, right_rel, left_name, left_cols = RAQP._set_op_iterate(node)
			print("="*20)
			print()
			print("Intersecting:", left_rel.name, "and", right_rel.name)
			print("Left Relation:")
			RAQP._print_relation(left_rel)
			print("Right Relation:")
			RAQP._print_relation(right_rel)
			print()
			result_rows = RAQP._intersect(left_rel, right_rel)
			return result_rows, left_cols, left_name
		elif node['type'] == 'minus':
			left_rel, right_rel, left_name, left_cols = RAQP._set_op_iterate(node)
			result_rows = RAQP._difference(left_rel, right_rel)
			print("="*20)
			print()
			print("Differencing:", left_rel.name, "and", right_rel.name)
			print("Left Relation:")
			RAQP._print_relation(left_rel)
			print("Right Relation:")
			RAQP._print_relation(right_rel)
			print()
			return result_rows, left_cols, left_name
		else:
			raise Exception(f"Unknown node type: {node['type']}")

	@staticmethod
	def _select(relation, condition):
		# Only supports simple conditions like Age > 30
		# If you want more, you'll have to add it!
		col_name, op, value = re.split(r'\s*(>|<|=)\s*', condition)
		col_name = col_name.strip()
		op = condition[len(col_name):].strip()[0]
		value = condition.split(op)[1].strip()
		col_idx = relation.columns.index(col_name)
		filtered = []
		for row in relation.rows:
			try:
				cell = row[col_idx]
				cell_val = int(cell) if cell.isdigit() else cell
				value_cmp = int(value) if value.isdigit() else value
				if op == '>':
					if cell_val > value_cmp:
						filtered.append(row)
				elif op == '<':
					if cell_val < value_cmp:
						filtered.append(row)
				elif op == '=':
					if cell_val == value_cmp:
						filtered.append(row)
			except Exception:
				continue
		return filtered

	@staticmethod
	def _project(relation, cols):
		col_indices = [relation.columns.index(col.strip()) for col in cols]
		projected = [[row[idx] for idx in col_indices] for row in relation.rows]
		return projected

	@staticmethod
	def _join(left, right, cond):
		# condition is required for now, natural join implement later
		left_col, right_col = [c.strip() for c in cond.split('=')]
		left_idx = left.columns.index(left_col.split('.')[-1])
		right_idx = right.columns.index(right_col.split('.')[-1])
		joined_cols = left.columns + right.columns
		joined_rows = [lrow + rrow for lrow in left.rows for rrow in right.rows if lrow[left_idx] == rrow[right_idx]]
		# always remove the key column from the right relation
		joined_cols.pop(len(left.columns) + right_idx)
		for i in range(len(joined_rows)):
			joined_rows[i].pop(len(left.columns) + right_idx)
		return joined_rows, joined_cols

	@staticmethod
	def _union(left, right):
		# only supports relations with same columns
		all_rows = left.rows.copy()
		for row in right.rows:
			if row not in all_rows:
				all_rows.append(row)
		return all_rows

	@staticmethod
	def _intersect(left, right):
		# Only supports relations with same columns
		return [row for row in left.rows if row in right.rows]

	@staticmethod
	def _difference(left, right):
		# Only supports relations with same columns
		return [row for row in left.rows if row not in right.rows]

if __name__ == "__main__":
	sample_input = """
Employees (EID, Name, Age) = {
    E1, John, 32
    E2, Alice, 28
    E3, Bob, 29
}

Query: invalid_operation (Employees)
"""
	expected = """
No result.
"""
	result = RAQP.process(sample_input)
	print("=" * 20)
	print("FINAL OUTPUT:")
	print(result.text.strip())
	print("EXPECTED OUTPUT:")
	print(expected.strip())