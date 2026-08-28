from flask import Flask, Response, jsonify, request
from flask_cors import CORS

from .service import ExecutionService


app = Flask(__name__)
CORS(app)
service = ExecutionService()


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/execute")
def execute():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("source"), str):
        return jsonify({"success": False, "message": "Se requiere el campo source como texto"}), 400
    return jsonify(service.execute(data["source"]))


@app.post("/api/files")
def load_file():
    source_file = request.files.get("file")
    if source_file is None or not source_file.filename:
        return jsonify({"success": False, "message": "No se recibio un archivo"}), 400
    if not source_file.filename.lower().endswith(".oxs"):
        return jsonify({"success": False, "message": "El archivo debe tener extension .oxs"}), 400
    try:
        source = source_file.read().decode("utf-8")
    except UnicodeDecodeError:
        return jsonify({"success": False, "message": "El archivo debe usar codificacion UTF-8"}), 400
    return jsonify({"success": True, "name": source_file.filename, "source": source})


@app.get("/api/reports/errors")
def errors_report():
    return Response(service.last_errors_html, mimetype="text/html")


@app.get("/api/reports/symbols")
def symbols_report():
    return Response(service.last_symbols_html, mimetype="text/html")


@app.get("/api/reports/ast.dot")
def ast_dot_report():
    return Response(service.last_dot, mimetype="text/vnd.graphviz")


@app.get("/api/reports/ast.svg")
def ast_svg_report():
    if service.last_svg is None:
        return jsonify({"success": False, "message": "Graphviz no esta instalado. Consulte README.md"}), 503
    return Response(service.last_svg, mimetype="image/svg+xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2611, debug=True)
