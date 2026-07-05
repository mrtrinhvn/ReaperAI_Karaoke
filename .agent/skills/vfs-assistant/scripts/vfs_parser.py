#!/usr/bin/env python3
import sys
import os
import subprocess

# --- AUTO-BOOTSTRAP DEPENDENCIES ---
def ensure_dependencies():
    try:
        import tree_sitter
        import tree_sitter_python
        import tree_sitter_javascript
        import tree_sitter_typescript
    except ImportError:
        print("VFS: Missing dependencies. Auto-bootstrapping tree-sitter packages...", file=sys.stderr)
        try:
            packages = ["tree-sitter", "tree-sitter-python", "tree-sitter-javascript", "tree-sitter-typescript"]
            subprocess.run(
                [sys.executable, "-m", "pip", "install"] + packages,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("VFS: Dependencies installed successfully. Restarting parser...", file=sys.stderr)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"VFS: Failed to auto-bootstrap dependencies: {e}", file=sys.stderr)
            sys.exit(1)

ensure_dependencies()

from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript

class VfsParserServer:
    def __init__(self):
        self.LANGUAGES = {
            "python": Language(tree_sitter_python.language()),
            "javascript": Language(tree_sitter_javascript.language()),
            "typescript": Language(tree_sitter_typescript.language_typescript()),
            "tsx": Language(tree_sitter_typescript.language_tsx())
        }
        
        self.parsers = {}
        for name, lang in self.LANGUAGES.items():
            parser = Parser(lang)
            self.parsers[name] = parser

        self.queries = {
            "python": """
                (class_definition name: (identifier) @class_name) @class
                (function_definition name: (identifier) @func_name) @function
            """,
            "javascript": """
                (class_declaration name: (identifier) @class_name) @class
                (function_declaration name: (identifier) @func_name) @function
                (method_definition name: (property_identifier) @func_name) @method
                (arrow_function) @function
            """,
            "typescript": """
                (class_declaration name: (type_identifier) @class_name) @class
                (function_declaration name: (identifier) @func_name) @function
                (method_definition name: (property_identifier) @func_name) @method
                (interface_declaration name: (type_identifier) @interface_name) @interface
                (type_alias_declaration name: (type_identifier) @type_name) @type
            """,
            "tsx": """
                (class_declaration name: (type_identifier) @class_name) @class
                (function_declaration name: (identifier) @func_name) @function
                (method_definition name: (property_identifier) @func_name) @method
                (interface_declaration name: (type_identifier) @interface_name) @interface
                (type_alias_declaration name: (type_identifier) @type_name) @type
            """
        }
        
        self.compiled_queries = {}
        for name, query_str in self.queries.items():
            try:
                self.compiled_queries[name] = Query(self.LANGUAGES[name], query_str)
            except Exception as e:
                print(f"Warning: Failed to compile query for {name}: {e}", file=sys.stderr)

    def extract_signatures(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"Error: File not found {file_path}"
            
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".py"]:
            lang = "python"
        elif ext in [".js", ".jsx"]:
            lang = "javascript"
        elif ext in [".ts"]:
            lang = "typescript"
        elif ext in [".tsx"]:
            lang = "tsx"
        else:
            return f"Error: Unsupported file extension {ext}"

        parser = self.parsers.get(lang)
        query = self.compiled_queries.get(lang)
        if not parser or not query:
             return f"Error: Parser/Query not found for language {lang}"

        with open(file_path, "rb") as f:
            source_code = f.read()
            
        tree = parser.parse(source_code)
        
        try:
            cursor = QueryCursor(query)
            capture_dict = cursor.captures(tree.root_node)
            
            extracted_symbols = []
            
            for capture_name, nodes in capture_dict.items():
                if capture_name in ['class', 'function', 'interface', 'type', 'method']:
                    for node in nodes:
                        start_line = node.start_point[0] + 1
                        end_line = node.end_point[0] + 1
                        code_bytes = source_code[node.start_byte:node.end_byte]
                        lines = code_bytes.decode('utf-8').splitlines()
                        signature = lines[0].strip() if lines else ""
                        
                        extracted_symbols.append({
                            "type": capture_name.upper(),
                            "start": start_line,
                            "end": end_line,
                            "signature": signature
                        })
                        
            extracted_symbols.sort(key=lambda x: x['start'])
            
            output = [f"--- VFS AST OUTLINE FOR {os.path.basename(file_path)} ---"]
            for sym in extracted_symbols:
                tag = f"[{sym['type']}]"
                if sym['type'] in ["CLASS", "INTERFACE"]:
                    output.append(f"Line {sym['start']}-{sym['end']} {tag}: {sym['signature']}")
                else:    
                    output.append(f"Line {sym['start']}-{sym['end']} {tag}: {sym['signature']}")
            output.append("--- END OUTLINE ---")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"Error parsing structure: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vfs_parser.py <file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    server = VfsParserServer()
    print(server.extract_signatures(file_path))
