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
		def tokenize(s):
			# guaranteed clean splitting
			s = s.replace('(', ' ( ').replace(')', ' ) ')
			s = s.replace(',', ' , ')
			s = s.replace('=', ' = ').replace('>', ' > ').replace('<', ' < ')
			s = s.replace('-', ' - ')
			s = s.replace('union', ' union ').replace('intersect', ' intersect ')
			return [token for token in s.split() if token]

		def find_matching_paren(tokens, start_index):
			if tokens[start_index] != '(':
				return -1
			depth = 1
			for i in range(start_index + 1, len(tokens)):
				if tokens[i] == '(':
					depth += 1
				elif tokens[i] == ')':
					depth -= 1
					if depth == 0:
						return i
			return -1

		def parse(tokens):
			if not tokens:
				raise ValueError("Cannot parse an empty query component.")
			if tokens[0] == '(' and find_matching_paren(tokens, 0) == len(tokens) - 1:
				return parse(tokens[1:-1])

			# order of operators (lowest to highest)
			# 1. set operations: minus, union, intersect
			# 2. join
			# 3. unary operations: select, project

			# 1. set operators
			depth = 0
			for i in range(len(tokens) - 1, -1, -1):
				token = tokens[i]
				if token == ')':
					depth += 1
				elif token == '(':
					depth -= 1
				elif depth == 0 and token in ['-', 'union', 'intersect']:
					op_type = {'-': 'minus', 'union': 'union', 'intersect': 'intersect'}[token]
					return {
						'type': op_type,
						'left': parse(tokens[:i]),
						'right': parse(tokens[i+1:])
					}

			# 2. join operator
			depth = 0
			for i in range(len(tokens) - 1, -1, -1):
				token = tokens[i]
				if token == ')':
					depth += 1
				elif token == '(':
					depth -= 1
				elif depth == 0 and token == 'join':
					left_node = parse(tokens[:i])
					rhs_tokens = tokens[i+1:]
					if not rhs_tokens:
						raise ValueError("Missing right operand for join.")
					right_operand_tokens = []
					condition_tokens = []
					if rhs_tokens[-1] == ')':
						# Subquery case: find its matching opening parenthesis
						start_paren_idx = find_matching_paren(rhs_tokens, 0) if rhs_tokens[0] == '(' else -1 # A bit of a guess, need to be smarter
						
						local_depth = 1
						start_paren_idx = -1
						for j in range(len(rhs_tokens) - 2, -1, -1):
							if rhs_tokens[j] == ')': local_depth +=1
							elif rhs_tokens[j] == '(':
								local_depth -= 1
								if local_depth == 0:
									start_paren_idx = j
									break
						if start_paren_idx == -1:
							raise ValueError("Invalid join syntax: unmatched parenthesis in right operand.")
						right_operand_tokens = rhs_tokens[start_paren_idx:]
						condition_tokens = rhs_tokens[:start_paren_idx]
					else:
						right_operand_tokens = [rhs_tokens[-1]]
						condition_tokens = rhs_tokens[:-1]
					if not condition_tokens:
						raise ValueError("Join condition is missing.")
					return {
						'type': 'join',
						'left': left_node,
						'right': parse(right_operand_tokens),
						'condition': ' '.join(condition_tokens)
					}

			# 3. unary operators
			op = tokens[0]
			if op in ['project', 'select']:
				paren_start_idx = -1
				for i, token in enumerate(tokens[1:], 1):
					if token == '(':
						paren_start_idx = i
						break
				if paren_start_idx == -1 or find_matching_paren(tokens, paren_start_idx) != len(tokens) - 1:
					raise ValueError(f"Invalid syntax for {op}. Expected '... (source)'.")
				spec_tokens = tokens[1:paren_start_idx]
				source_tokens = tokens[paren_start_idx+1:-1]
				if op == 'project':
					columns = [t for t in spec_tokens if t != ',']
					if not columns: raise ValueError("Project operation must specify columns.")
					return { 'type': 'project', 'columns': columns, 'source': parse(source_tokens) }
				else: # select
					if not spec_tokens: raise ValueError("Select operation must have a condition.")
					return { 'type': 'select', 'condition': ' '.join(spec_tokens), 'source': parse(source_tokens) }

			# base case: single relation
			if len(tokens) == 1:
				name = tokens[0]
				if name in RAQP.relations:
					return {'type': 'relation', 'name': name}

			raise ValueError(f"Unable to parse syntax: {' '.join(tokens)}")

		return parse(tokenize(query_text))

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