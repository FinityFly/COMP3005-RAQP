import re

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
		result_rows, columns = RAQP._parse_and_execute_query(query_text)
		table = {"columns": columns, "rows": result_rows}
		rel_name = RAQP._extract_relation_name(query_text)
		explanation = RAQP._format_output_text(rel_name, columns, result_rows)
		return RAQPResult(explanation, table)
	
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
		result = f'{rel_name} = {{{header}\n' + '\n'.join(lines) + '\n}}'
		return result

	@staticmethod
	def _split_input(input_text):
		parts = input_text.split('Query:')
		rel_text = parts[0].strip()
		query_text = parts[1].strip() if len(parts) > 1 else ''

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
	def _parse_and_execute_query(query_text):
		handlers = {
			'select': lambda m: RAQP._handle_select(m),
			'project': lambda m: RAQP._handle_project(m),
			'join': lambda m: RAQP._handle_join(m),
			'union': lambda m: RAQP._handle_set_op(m, 'union'),
			'intersect': lambda m: RAQP._handle_set_op(m, 'intersect'),
			'diff': lambda m: RAQP._handle_set_op(m, 'diff'),
		}
		for op, handler in handlers.items():
			if query_text.startswith(op):
				patterns = {
					'select': r'select\s+(.+?)\s*\((\w+)\)',
					'project': r'project\s+(.+?)\s*\((\w+)\)',
					'join': r'join\s*\((\w+),\s*(\w+),\s*(.+)\)',
					'union': r'union\s*\((\w+),\s*(\w+)\)',
					'intersect': r'intersect\s*\((\w+),\s*(\w+)\)',
					'diff': r'diff\s*\((\w+),\s*(\w+)\)',
				}
				m = re.match(patterns[op], query_text)
				if not m:
					return [], []
				return handler(m)
		return [], []

	@staticmethod
	def _handle_select(m):
		condition, rel_name = m.group(1), m.group(2)
		relation = RAQP.relations.get(rel_name)
		if not relation:
			return [], []
		filtered_rows = RAQP._select(relation, condition)
		return filtered_rows, relation.columns

	@staticmethod
	def _handle_project(m):
		col, rel_name = m.group(1), m.group(2)
		relation = RAQP.relations.get(rel_name)
		if not relation:
			return [], []
		projected_rows = RAQP._project(relation, col)
		return projected_rows, [col]

	@staticmethod
	def _handle_join(m):
		left_name, right_name, cond = m.group(1), m.group(2), m.group(3)
		left = RAQP.relations.get(left_name)
		right = RAQP.relations.get(right_name)
		if not left or not right:
			return [], []
		joined_rows, joined_cols = RAQP._join(left, right, cond)
		return joined_rows, joined_cols

	@staticmethod
	def _handle_set_op(m, op):
		left_name, right_name = m.group(1), m.group(2)
		left = RAQP.relations.get(left_name)
		right = RAQP.relations.get(right_name)
		if not left or not right:
			return [], []
		if op == 'union':
			result_rows = RAQP._union(left, right)
		elif op == 'intersect':
			result_rows = RAQP._intersect(left, right)
		elif op == 'diff':
			result_rows = RAQP._difference(left, right)
		else:
			result_rows = []
		return result_rows, left.columns

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
	def _project(relation, col_name):
		col_name = col_name.strip()
		col_idx = relation.columns.index(col_name)
		projected = [[row[col_idx]] for row in relation.rows]
		return projected

	@staticmethod
	def _join(left, right, cond):
		# Only supports equi-join on one column, like EID = EID
		left_col, right_col = [c.strip() for c in cond.split('=')]
		left_idx = left.columns.index(left_col)
		right_idx = right.columns.index(right_col)
		joined_cols = left.columns + right.columns
		joined_rows = []
		for lrow in left.rows:
			for rrow in right.rows:
				if lrow[left_idx] == rrow[right_idx]:
					joined_rows.append(lrow + rrow)
		return joined_rows, joined_cols

	@staticmethod
	def _union(left, right):
		# Only supports relations with same columns
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
