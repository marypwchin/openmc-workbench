"""Find documented OpenMC API calls in Python notebooks and scripts.

Uses static syntax inspection: it never imports OpenMC or executes notebook cells.
Keep the class and method registries limited to documented OpenMC APIs; this
avoids linking a pandas or user-defined method to an unrelated OpenMC method.
"""

import ast
import json

DOCS = 'https://docs.openmc.org/en/stable/'
GENERATED = DOCS + 'pythonapi/generated/'

# Documented class methods. Constructors are listed separately below.
CLASS_METHODS = {
    'openmc.data.DataLibrary': {
        'export_to_xml', 'from_xml', 'get_by_material', 'register_file',
        'remove_by_material',
    },
    'openmc.data.IncidentNeutron': {
        'add_elastic_0K_from_endf', 'add_temperature_from_ace',
        'export_to_hdf5', 'from_ace', 'from_endf', 'from_hdf5',
        'from_njoy', 'get_reaction_components',
    },
    'openmc.data.ThermalScattering': {
        'export_to_hdf5', 'from_ace', 'from_hdf5', 'from_njoy',
    },
    'openmc.Material': {
        'add_components', 'add_element', 'add_nuclide', 'add_s_alpha_beta',
        'clone', 'get_atom_density', 'get_density', 'get_element_atom_densities',
        'get_elements', 'get_mass', 'get_mass_density',
        'get_nuclide_atom_densities', 'get_nuclides', 'get_total_atoms',
        'mean_free_path',
        'mix_materials', 'remove_element', 'remove_nuclide', 'set_density',
    },
    'openmc.Materials': {'append', 'export_to_xml', 'from_xml'},
    'openmc.model.Model': {
        'calculate_volumes', 'export_to_model_xml', 'export_to_xml',
        'from_model_xml', 'from_xml', 'plot', 'run',
    },
    'openmc.Geometry': {
        'export_to_xml', 'get_all_cells', 'get_all_materials',
        'get_all_universes', 'remove_redundant_surfaces',
    },
    'openmc.Region': {'clone', 'from_expression', 'get_surfaces', 'plot'},
    'openmc.StatePoint': {'get_tallies', 'get_tally', 'link_with_summary'},
    'openmc.Tally': {
        'get_pandas_dataframe', 'get_reshaped_data', 'get_slice',
        'get_values', 'find_filter',
    },
    'openmc.Universe': {
        'add_cell', 'add_cells', 'get_all_cells', 'get_all_materials',
    },
    'openmc.RegularMesh': {'from_domain'},
    'openmc.Cell': {'clone', 'get_all_cells', 'get_all_materials'},
    'openmc.data.Tabulated1D': {'integral'},
    'openmc.data.Reaction': {'from_hdf5'},
}

# Construction of these classes is itself a significant OpenMC API call.
# The documentation link points to the class, not to an invented __init__ anchor.
CONSTRUCTORS = {
    'openmc.Material', 'openmc.Materials', 'openmc.Cell', 'openmc.Geometry',
    'openmc.Universe', 'openmc.model.Model', 'openmc.Settings',
    'openmc.Tally', 'openmc.Tallies', 'openmc.CellFilter',
    'openmc.EnergyFilter', 'openmc.MeshFilter', 'openmc.RegularMesh',
    'openmc.StatePoint', 'openmc.IndependentSource',
    'openmc.stats.Point', 'openmc.stats.Isotropic', 'openmc.stats.Discrete',
    'openmc.Plot', 'openmc.Plots', 'openmc.Sphere', 'openmc.XPlane', 'openmc.YPlane',
    'openmc.ZPlane', 'openmc.XCylinder', 'openmc.YCylinder',
    'openmc.ZCylinder', 'openmc.Plane', 'openmc.RectangularParallelepiped',
}

# API aliases: openmc.Model is re-exported from openmc.model.Model.
CLASS_ALIASES = {'openmc.Model': 'openmc.model.Model'}

# Functions documented outside of class pages. A source-doc link is used for
# calculate_cexs, which does not have a separate generated API reference page.
FUNCTION_DOCS = {
    'openmc.plot_xs': GENERATED + 'openmc.plot_xs.html',
    'openmc.plotter.calculate_cexs': DOCS + '_modules/openmc/plotter.html#calculate_cexs',
    'openmc.plotter.calculate_mgxs': DOCS + '_modules/openmc/plotter.html#calculate_mgxs',
    'openmc.run': GENERATED + 'openmc.run.html',
    'openmc.plot_geometry': GENERATED + 'openmc.plot_geometry.html',
}
FUNCTION_ALIASES = {'openmc.plotter.plot_xs': 'openmc.plot_xs'}


def dotted(node):
    """Return a.b.c for simple names and attributes, or None otherwise."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        head = dotted(node.value)
        if head:
            return f'{head}.{node.attr}'
    return None


def python_sources(path):
    if path.suffix == '.ipynb':
        notebook = json.loads(path.read_text(encoding='utf-8'))
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') != 'code':
                continue
            content = cell.get('source', '')
            yield ''.join(content) if isinstance(content, list) else content
    elif path.suffix == '.py':
        yield path.read_text(encoding='utf-8')


def parse_python(source):
    """Ignore IPython magic/shell lines without running any notebook code."""
    lines = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(('%%', '%', '!', '?')):
            lines.append(' ' * (len(line) - len(stripped)) + 'pass')
        else:
            lines.append(line)
    try:
        return ast.parse('\n'.join(lines))
    except SyntaxError:
        # Do not interpret invalid Python by guessing about its content.
        return None


class APICalls(ast.NodeVisitor):
    def __init__(self):
        self.aliases = {'openmc': 'openmc'}
        self.types = {}
        self.item_types = {}  # dict name -> key -> OpenMC type, e.g. mats_dic[name]
        self.methods = set()

    def resolve(self, node):
        """Resolve direct names, attributes, and previously typed dict entries."""
        if isinstance(node, ast.Subscript):
            container = dotted(node.value)
            entries = self.item_types.get(container, {})
            key = node.slice.value if isinstance(node.slice, ast.Constant) else None
            if key is not None and key in entries:
                return entries[key]
            # A dynamic key may select any element. Infer only when every
            # known entry has the same class (including wildcard entries).
            classes = set(entries.values())
            return next(iter(classes)) if len(classes) == 1 else None
        if isinstance(node, ast.Attribute):
            parent = self.resolve(node.value)
            return f'{parent}.{node.attr}' if parent else None
        if isinstance(node, ast.Name):
            return self.types.get(node.id, self.aliases.get(node.id, node.id))
        return None

    def inferred_class(self, expression):
        """Infer types from constructors, factory calls, and known variables."""
        if isinstance(expression, (ast.Name, ast.Subscript)):
            name = self.resolve(expression)
            if name in CLASS_METHODS or name in CONSTRUCTORS:
                return name
        if not isinstance(expression, ast.Call):
            return None
        name = self.resolve(expression.func)
        canonical = CLASS_ALIASES.get(name, name)
        if canonical in CLASS_METHODS or canonical in CONSTRUCTORS:
            return canonical
        if canonical and '.' in canonical:
            owner, _, method = canonical.rpartition('.')
            if owner in CLASS_METHODS and method.startswith('from_'):
                return owner
        return None

    def assign_type(self, target, cls):
        if isinstance(target, ast.Name):
            if cls:
                self.types[target.id] = cls
            else:
                self.types.pop(target.id, None)
        elif isinstance(target, ast.Subscript) and cls:
            container = dotted(target.value)
            if container:
                key = (target.slice.value if isinstance(target.slice, ast.Constant)
                       else '*')
                self.item_types.setdefault(container, {})[key] = cls

    def visit_Import(self, node):
        for item in node.names:
            if item.name == 'openmc' or item.name.startswith('openmc.'):
                self.aliases[item.asname or 'openmc'] = (
                    item.name if item.asname else 'openmc'
                )

    def visit_ImportFrom(self, node):
        if node.module and (node.module == 'openmc' or node.module.startswith('openmc.')):
            for item in node.names:
                self.aliases[item.asname or item.name] = f'{node.module}.{item.name}'

    def visit_Assign(self, node):
        self.visit(node.value)
        cls = self.inferred_class(node.value)
        for target in node.targets:
            self.assign_type(target, cls)
            # Also follow dictionaries initialized directly with OpenMC objects.
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Dict):
                entries = self.item_types.setdefault(target.id, {})
                for key_node, value_node in zip(node.value.keys, node.value.values):
                    item_class = self.inferred_class(value_node)
                    if item_class:
                        key = (key_node.value if isinstance(key_node, ast.Constant)
                               else '*')
                        entries[key] = item_class

    def visit_AnnAssign(self, node):
        if node.value:
            self.visit(node.value)
            self.assign_type(node.target, self.inferred_class(node.value))

    def visit_With(self, node):
        for item in node.items:
            self.visit(item.context_expr)
            cls = self.inferred_class(item.context_expr)
            if cls and isinstance(item.optional_vars, ast.Name):
                self.types[item.optional_vars.id] = cls
        for statement in node.body:
            self.visit(statement)

    def visit_For(self, node):
        # A loop over mats_dic.items() yields OpenMC Materials as its second
        # tuple member when all known dictionary entries have that type.
        if (isinstance(node.iter, ast.Call)
                and isinstance(node.iter.func, ast.Attribute)
                and node.iter.func.attr == 'items'
                and isinstance(node.target, ast.Tuple)
                and len(node.target.elts) == 2
                and isinstance(node.target.elts[1], ast.Name)):
            entries = self.item_types.get(dotted(node.iter.func.value), {})
            classes = set(entries.values())
            if len(classes) == 1:
                self.types[node.target.elts[1].id] = next(iter(classes))
        self.generic_visit(node)

    def visit_Call(self, node):
        name = self.resolve(node.func)
        if name:
            name = FUNCTION_ALIASES.get(name, name)
            canonical = CLASS_ALIASES.get(name, name)
            if canonical in CONSTRUCTORS:
                self.methods.add(canonical)
            elif name in FUNCTION_DOCS:
                self.methods.add(name)
            elif '.' in canonical:
                owner, _, method = canonical.rpartition('.')
                owner = CLASS_ALIASES.get(owner, owner)
                if method in CLASS_METHODS.get(owner, ()):
                    self.methods.add(f'{owner}.{method}')
        self.generic_visit(node)


def openmc_methods(path):
    """Return links to recognized OpenMC methods and constructors."""
    visitor = APICalls()
    for source in python_sources(path):
        tree = parse_python(source)
        if tree is not None:
            visitor.visit(tree)

    links = []
    for full_name in sorted(visitor.methods):
        if full_name in FUNCTION_DOCS:
            url = FUNCTION_DOCS[full_name]
            label = full_name.removeprefix('openmc.') + '()'
        elif full_name in CONSTRUCTORS:
            url = GENERATED + full_name + '.html'
            label = full_name.rsplit('.', 1)[-1] + '()'
        else:
            owner, _, method = full_name.rpartition('.')
            url = GENERATED + owner + '.html#' + full_name
            label = owner.removeprefix('openmc.').split('.')[-1] + '.' + method + '()'
        links.append(f'[`{label}`]({url})')
    return ', '.join(links) if links else '—'
