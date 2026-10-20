"""Java host-class facts for D-08, using tree-sitter-java (JavaParser is not reachable here).

Mirrors scripts/InspectCases.java (JavaParser) for the facts M2 used, but for every method
of the host class instead of the gold method only:
  fields          direct field declarators of the host class           (cls.getFields())
  parameters      declared parameters of a method                       (method.getParameters())
  locals          every variable declarator inside a method body        (method.findAll(VariableDeclarator))
  member_accesses scoped method calls and field accesses in a method    (MethodCallExpr with scope, FieldAccessExpr)
Equivalence with the M2 JavaParser ASTs is checked by scripts/check_ast_equivalence.py.
"""
import re
import tree_sitter_java
from tree_sitter import Language, Parser

PARSER = Parser(Language(tree_sitter_java.language()))
TYPE_DECLS = {'class_declaration', 'interface_declaration', 'enum_declaration', 'record_declaration', 'annotation_type_declaration'}
COMMENTS = {'line_comment', 'block_comment'}


def text(node):
    return node.text.decode('utf-8')


def norm(s):
    """Whitespace-free form, used where JavaParser pretty-prints (types, scopes)."""
    return re.sub(r'\s+', '', s)


def line(node):
    return node.start_point[0] + 1


def walk(node):
    yield node
    for child in node.children:
        yield from walk(child)


def _type_name(decl):
    return text(decl.child_by_field_name('name'))


def find_types(root, package):
    """FQN -> declaration node for every (nested) type; nested types use Outer.Inner, as in sample_ids.csv."""
    found = {}

    def visit(node, prefix):
        for child in node.children:
            if child.type in TYPE_DECLS:
                fqn = prefix + _type_name(child)
                found[fqn] = child
                body = child.child_by_field_name('body')
                if body is not None:
                    visit(body, fqn + '.')
            elif child.type in ('class_body', 'interface_body', 'enum_body', 'enum_body_declarations', 'program'):
                visit(child, prefix)
    visit(root, (package + '.') if package else '')
    return found


def _declarators(node):
    """(name, type, line) for each declarator of a field/local declaration node."""
    typ = node.child_by_field_name('type')
    out = []
    for child in node.children_by_field_name('declarator'):
        out.append({'name': text(child.child_by_field_name('name')), 'type': norm(text(typ)), 'line': line(child)})
    return out


def _modifiers(node):
    for child in node.children:
        if child.type == 'modifiers':
            return child
    return None


def _annotations(node):
    mods = _modifiers(node)
    if mods is None:
        return []
    return [text(c.child_by_field_name('name')) for c in mods.children if c.type in ('marker_annotation', 'annotation')]


def _parameters(method):
    params = []
    plist = method.child_by_field_name('parameters')
    for p in plist.children if plist is not None else []:
        if p.type == 'formal_parameter':
            params.append({'name': text(p.child_by_field_name('name')), 'type': norm(text(p.child_by_field_name('type'))), 'line': line(p)})
        elif p.type == 'spread_parameter':  # JavaParser: getTypeAsString() of a varargs parameter omits "..."
            typ = next(c for c in p.children if c.type not in ('modifiers', '...', 'variable_declarator'))
            decl = next(c for c in p.children if c.type == 'variable_declarator')
            params.append({'name': text(decl.child_by_field_name('name')), 'type': norm(text(typ)), 'line': line(p)})
    return params


def _locals(body):
    out = []
    for n in walk(body):
        if n.type in ('local_variable_declaration', 'field_declaration'):  # fields of anonymous/local classes are VariableDeclarators too
            out.extend(_declarators(n))
        elif n.type == 'enhanced_for_statement':
            out.append({'name': text(n.child_by_field_name('name')), 'type': norm(text(n.child_by_field_name('type'))), 'line': line(n.child_by_field_name('name'))})
        elif n.type == 'resource' and n.child_by_field_name('type') is not None:
            out.append({'name': text(n.child_by_field_name('name')), 'type': norm(text(n.child_by_field_name('type'))), 'line': line(n.child_by_field_name('name'))})
    return out


def _accesses(body):
    out = []
    for n in walk(body):
        if n.type == 'method_invocation' and n.child_by_field_name('object') is not None:
            out.append({'kind': 'call', 'scope': norm(text(n.child_by_field_name('object'))), 'member': text(n.child_by_field_name('name')), 'line': line(n)})
        elif n.type == 'field_access':
            out.append({'kind': 'field', 'scope': norm(text(n.child_by_field_name('object'))), 'member': text(n.child_by_field_name('field')), 'line': line(n)})
    return out


def _statements(body):
    return [c for c in body.named_children if c.type not in COMMENTS] if body is not None else None


def _is_field_ref(expr, fields):
    if expr.type == 'identifier':
        return text(expr) in fields
    if expr.type == 'field_access':
        return text(expr.child_by_field_name('object')) == 'this' and text(expr.child_by_field_name('field')) in fields
    return False


def accessor_kind(method, fields, params):
    """D-08 H3 rule: single `return <field>;` (getter) or `<field> = <param>;` (setter)."""
    stmts = _statements(method.child_by_field_name('body'))
    if not stmts or len(stmts) != 1:
        return None
    s = stmts[0]
    if s.type == 'return_statement':
        exprs = [c for c in s.named_children if c.type not in COMMENTS]
        if len(exprs) == 1 and _is_field_ref(exprs[0], fields):
            return 'getter'
    if s.type == 'expression_statement':
        e = s.named_children[0]
        if e.type == 'assignment_expression' and text(e.child_by_field_name('operator')) == '=':
            right = e.child_by_field_name('right')
            if _is_field_ref(e.child_by_field_name('left'), fields) and right.type == 'identifier' and text(right) in params:
                return 'setter'
    return None


def inspect(source_bytes, host_fqn):
    root = PARSER.parse(source_bytes).root_node
    if root.has_error:
        raise ValueError('tree-sitter reports a syntax error in host source')
    pkg = next((c for c in root.children if c.type == 'package_declaration'), None)
    package = norm(text(pkg)).removeprefix('package').removesuffix(';') if pkg is not None else ''
    imports = [norm(text(c)).removeprefix('import').removesuffix(';') for c in root.children if c.type == 'import_declaration']
    imports = [('static ' + i[len('static'):]) if i.startswith('static') else i for i in imports]
    types = find_types(root, package)
    if host_fqn not in types:
        raise ValueError('Host selection failed: ' + host_fqn)
    cls = types[host_fqn]
    body = cls.child_by_field_name('body')
    fields = [d for c in body.named_children if c.type == 'field_declaration' for d in _declarators(c)]
    field_names = {f['name'] for f in fields}
    methods = []
    for c in body.named_children:
        if c.type not in ('method_declaration', 'constructor_declaration'):
            continue
        params = _parameters(c)
        mbody = c.child_by_field_name('body')
        stmts = _statements(mbody)
        methods.append({
            'name': text(c.child_by_field_name('name')),
            'kind': 'constructor' if c.type == 'constructor_declaration' else 'method',
            'line': line(c), 'end_line': c.end_point[0] + 1,
            'annotations': _annotations(c),
            'modifiers': norm(text(_modifiers(c))) if _modifiers(c) is not None else '',
            'parameters': params,
            'locals': _locals(mbody) if mbody is not None else [],
            'member_accesses': _accesses(mbody) if mbody is not None else [],
            'has_body': mbody is not None,
            'statement_count': len(stmts) if stmts is not None else None,
            'accessor': accessor_kind(c, field_names, {p['name'] for p in params}) if mbody is not None else None,
            'source': text(c),
        })
    nested = sorted(f for f in types if f.startswith(host_fqn + '.'))
    return {'host': host_fqn, 'package': package, 'imports': imports, 'fields': fields,
            'methods': methods, 'types_in_file': sorted(types), 'nested_types': nested}
