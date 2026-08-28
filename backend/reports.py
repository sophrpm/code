import html
import subprocess

from .ast.node import Node


def ast_to_dot(instructions):
    lines = ["digraph AST {", '  graph [bgcolor="#101827", rankdir=TB];', '  node [shape=box, style="rounded,filled", fillcolor="#17233a", color="#52d3c2", fontcolor="white"];']
    counter = [0]

    def add_node(label):
        node_id = "n" + str(counter[0])
        counter[0] += 1
        safe_label = str(label).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        lines.append(f'  {node_id} [label="{safe_label}"];')
        return node_id

    def visit(value, label=None):
        if isinstance(value, Node):
            node_id = add_node(value.__class__.__name__)
            for name, child in value.__dict__.items():
                if name in ("line", "column") or child is None:
                    continue
                if isinstance(child, (Node, list, dict)):
                    child_id = visit(child, name)
                    lines.append(f'  {node_id} -> {child_id} [label="{name}"];')
                elif isinstance(child, (str, int, float, bool)):
                    child_id = add_node(f"{name}: {child}")
                    lines.append(f"  {node_id} -> {child_id};")
            return node_id

        if isinstance(value, list):
            node_id = add_node(label or "Lista")
            for child in value:
                child_id = visit(child)
                lines.append(f"  {node_id} -> {child_id};")
            return node_id

        if isinstance(value, dict):
            node_id = add_node(label or "Datos")
            for name, child in value.items():
                if child is None:
                    continue
                child_id = visit(child, name) if isinstance(child, (Node, list, dict)) else add_node(f"{name}: {child}")
                lines.append(f'  {node_id} -> {child_id} [label="{name}"];')
            return node_id

        return add_node(value)

    visit(instructions, "Program")
    lines.append("}")
    return "\n".join(lines)


def dot_to_svg(dot_source):
    try:
        process = subprocess.run(["dot", "-Tsvg"], input=dot_source, text=True, capture_output=True, check=False)
    except OSError:
        return None
    if process.returncode != 0:
        return None
    return process.stdout


def errors_to_html(errors):
    rows = []
    for index, error in enumerate(errors, 1):
        rows.append([index, error.get("type"), error.get("description"), error.get("line"), error.get("column"), error.get("fragment") or ""])
    return table_html("Reporte de errores", ["No.", "Tipo", "Descripción", "Línea", "Columna", "Fragmento"], rows)


def symbols_to_html(symbols):
    rows = []
    for index, symbol in enumerate(symbols, 1):
        rows.append([index, symbol.get("name"), symbol.get("kind"), symbol.get("data_type"), symbol.get("scope"), symbol.get("line"), symbol.get("value", "")])
    return table_html("Tabla de símbolos", ["No.", "Identificador", "Categoría", "Tipo", "Ámbito", "Línea", "Valor"], rows)


def table_html(title, headers, rows):
    head = "".join("<th>" + html.escape(str(value)) + "</th>" for value in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join("<td>" + html.escape(str(value)) + "</td>" for value in row) + "</tr>"
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>body{{font-family:Arial,sans-serif;background:#0c1424;color:#e7edf7;padding:2rem}}table{{width:100%;border-collapse:collapse;background:#14213a}}th,td{{border:1px solid #334461;padding:.65rem;text-align:left}}th{{background:#167d79}}tr:nth-child(even){{background:#192945}}</style></head>
<body><h1>{html.escape(title)}</h1><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></body></html>'''
