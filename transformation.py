import ast
import os


class SafeTransformationLibrary(ast.NodeTransformer):
    """
    AST-level safe code transformer.
    Replaces dangerous constructs with safe alternatives where possible.
    """

    def __init__(self):
        self.changes_made = []

    def visit_Call(self, node):
   
        if isinstance(node.func, ast.Name) and node.func.id == 'eval':
            self.changes_made.append({
                'line': node.lineno,
                'original': 'eval()',
                'replacement': 'ast.literal_eval()',
                'reason': 'eval() allows arbitrary code execution; ast.literal_eval() safely parses literals only'
            })
            new_node = ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='ast', ctx=ast.Load()),
                    attr='literal_eval',
                    ctx=ast.Load()
                ),
                args=node.args,
                keywords=node.keywords
            )
            return ast.copy_location(new_node, node)

        
        if isinstance(node.func, ast.Name) and node.func.id == 'exec':
            self.changes_made.append({
                'line': node.lineno,
                'original': 'exec()',
                'replacement': '# REMOVED: exec() flagged as dangerous',
                'reason': 'exec() executes arbitrary code strings — removed for safety'
            })
           
            return ast.copy_location(
                ast.Call(
                    func=ast.Name(id='print', ctx=ast.Load()),
                    args=[ast.Constant(value='[SECURITY] exec() was removed by self-healing compiler')],
                    keywords=[]
                ),
                node
            )


        if (isinstance(node.func, ast.Attribute) and
                node.func.attr == 'system' and
                isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'os'):
            self.changes_made.append({
                'line': node.lineno,
                'original': 'os.system()',
                'replacement': 'subprocess.run(..., shell=False)',
                'reason': 'os.system() is vulnerable to shell injection; subprocess.run with shell=False is safer'
            })
          
            if node.args:
                arg = node.args[0]
                split_call = ast.Call(
                    func=ast.Attribute(value=arg, attr='split', ctx=ast.Load()),
                    args=[], keywords=[]
                )
                new_node = ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id='subprocess', ctx=ast.Load()),
                        attr='run',
                        ctx=ast.Load()
                    ),
                    args=[split_call],
                    keywords=[ast.keyword(arg='shell', value=ast.Constant(value=False))]
                )
                return ast.copy_location(new_node, node)


        if isinstance(node.func, ast.Name) and node.func.id == 'compile':
            self.changes_made.append({
                'line': node.lineno,
                'original': 'compile()',
                'replacement': '# FLAGGED: compile() with dynamic input',
                'reason': 'compile() with user-controlled input enables code injection'
            })

        return self.generic_visit(node)


def transform_code(source: str) -> tuple[str, list]:
    """
    Transform source code string and return (safe_code, list_of_changes).
    Automatically prepends required imports.
    """
    tree = ast.parse(source)
    transformer = SafeTransformationLibrary()
    safe_tree = transformer.visit(tree)
    ast.fix_missing_locations(safe_tree)
    safe_code = ast.unparse(safe_tree)

   
    imports_needed = []
    if 'ast.literal_eval' in safe_code and 'import ast' not in safe_code:
        imports_needed.append('import ast')
    if 'subprocess.run' in safe_code and 'import subprocess' not in safe_code:
        imports_needed.append('import subprocess')

    if imports_needed:
        safe_code = '\n'.join(imports_needed) + '\n' + safe_code

    return safe_code, transformer.changes_made


def run_transformation_engine(input_file):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, input_file)
    output_path = os.path.join(script_dir, "safe_transformed_code.py")

    try:
        with open(input_path, "r") as f:
            source = f.read()

        safe_code, changes = transform_code(source)

        with open(output_path, "w") as f:
            f.write("# --- AUTO-GENERATED SAFE TRANSFORMATION ---\n")
            f.write(safe_code)

        print(f"\n✅ Transformation complete. {len(changes)} change(s) made.")
        for c in changes:
            print(f"  Line {c['line']}: {c['original']} → {c['replacement']}")
        print(f"  Saved to: {output_path}")

    except Exception as e:
        print(f"❌ Transformation Failed: {e}")


if __name__ == "__main__":
    run_transformation_engine("test_code.py")