import { useEffect, useRef, useState } from 'react'
import './App.css'

type OxigenError = { type: string; description: string; line: number; column: number; fragment?: string }
type SymbolInfo = { name: string; kind: string; data_type: string; scope: string; line: number; value: string }
type Execution = { success: boolean; console: string[]; errors: OxigenError[]; symbols: SymbolInfo[]; ast: string }

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:2611'
const initialCode = `fn main() {
    println!("Hola desde OxigenScript");
}
`

function App() {
  const [fileName, setFileName] = useState('nuevo.oxs')
  const [source, setSource] = useState(initialCode)
  const [result, setResult] = useState<Execution>({ success: true, console: [], errors: [], symbols: [], ast: '' })
  const [backendStatus, setBackendStatus] = useState('verificando')
  const [activeReport, setActiveReport] = useState<'errors' | 'symbols' | 'ast'>('errors')
  const [running, setRunning] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetch(`${apiUrl}/api/health`).then((response) => {
      setBackendStatus(response.ok ? 'conectado' : 'sin conexión')
    }).catch(() => setBackendStatus('sin conexión'))
  }, [])

  const openFile = (file?: File) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.oxs')) {
      window.alert('Seleccione un archivo con extensión .oxs')
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      setSource(String(reader.result || ''))
      setFileName(file.name)
    }
    reader.readAsText(file, 'UTF-8')
  }

  const saveFile = () => {
    const blob = new Blob([source], { type: 'text/plain;charset=utf-8' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = fileName.endsWith('.oxs') ? fileName : `${fileName}.oxs`
    link.click()
    URL.revokeObjectURL(link.href)
  }

  const execute = async () => {
    setRunning(true)
    try {
      const response = await fetch(`${apiUrl}/api/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.message || 'No se pudo ejecutar el código')
      setResult(data)
      setBackendStatus('conectado')
    } catch (error) {
      setBackendStatus('sin conexión')
      setResult({ success: false, console: [], symbols: [], ast: '', errors: [{ type: 'Servidor', description: error instanceof Error ? error.message : 'Error de conexión', line: 0, column: 0 }] })
    } finally {
      setRunning(false)
    }
  }

  const newFile = () => {
    setFileName('nuevo.oxs')
    setSource('')
    setResult({ success: true, console: [], errors: [], symbols: [], ast: '' })
  }

  return (
    <main className="workspace">
      <header className="toolbar">
        <div className="brand"><span className="brand-mark">O₂</span><div><strong>OxigenScript</strong><small>Intérprete académico</small></div></div>
        <div className="actions">
          <button onClick={newFile}>Nuevo</button>
          <button onClick={() => fileInput.current?.click()}>Abrir .oxs</button>
          <button onClick={saveFile}>Guardar</button>
          <button className="run" onClick={execute} disabled={running}>{running ? 'Analizando…' : '▶ Analizar / Ejecutar'}</button>
          <input ref={fileInput} type="file" accept=".oxs" hidden onChange={(event) => openFile(event.target.files?.[0])} />
        </div>
        <span className={`status ${backendStatus === 'conectado' ? 'online' : ''}`}>● Backend {backendStatus}</span>
      </header>

      <section className="editor-panel">
        <div className="panel-title"><span>{fileName}</span><span>{source.split('\n').length} líneas</span></div>
        <div className="editor-wrap">
          <pre className="line-numbers" aria-hidden="true">{source.split('\n').map((_, index) => index + 1).join('\n')}</pre>
          <textarea aria-label="Editor OxigenScript" spellCheck={false} value={source} onChange={(event) => setSource(event.target.value)} />
        </div>
      </section>

      <section className="bottom-grid">
        <article className="console-panel">
          <div className="panel-title"><span>Consola</span><button className="text-button" onClick={() => setResult({ ...result, console: [] })}>Limpiar</button></div>
          <pre className="console">{result.console.length ? result.console.join('\n') : 'La salida de println! aparecerá aquí.'}</pre>
        </article>

        <article className="reports-panel">
          <nav className="tabs">
            <button className={activeReport === 'errors' ? 'active' : ''} onClick={() => setActiveReport('errors')}>Errores <b>{result.errors.length}</b></button>
            <button className={activeReport === 'symbols' ? 'active' : ''} onClick={() => setActiveReport('symbols')}>Símbolos <b>{result.symbols.length}</b></button>
            <button className={activeReport === 'ast' ? 'active' : ''} onClick={() => setActiveReport('ast')}>AST</button>
          </nav>
          <div className="report-content">
            {activeReport === 'errors' && (result.errors.length ? <table><thead><tr><th>Tipo</th><th>Descripción</th><th>Posición</th></tr></thead><tbody>{result.errors.map((error, index) => <tr key={index}><td>{error.type}</td><td>{error.description}</td><td>{error.line}:{error.column}</td></tr>)}</tbody></table> : <p className="empty">No se registraron errores.</p>)}
            {activeReport === 'symbols' && (result.symbols.length ? <table><thead><tr><th>Identificador</th><th>Categoría</th><th>Tipo</th><th>Ámbito</th><th>Línea</th></tr></thead><tbody>{result.symbols.map((symbol, index) => <tr key={index}><td>{symbol.name}</td><td>{symbol.kind}</td><td>{symbol.data_type}</td><td>{symbol.scope}</td><td>{symbol.line}</td></tr>)}</tbody></table> : <p className="empty">Ejecute un programa para crear la tabla.</p>)}
            {activeReport === 'ast' && (result.ast ? <><div className="report-links"><a href={`${apiUrl}/api/reports/ast.svg`} target="_blank">Ver gráfico SVG</a><a href={`${apiUrl}/api/reports/ast.dot`} target="_blank">Descargar DOT</a></div><pre className="dot-preview">{result.ast}</pre></> : <p className="empty">El AST aparecerá después del análisis.</p>)}
          </div>
          <footer className="report-footer"><a href={`${apiUrl}/api/reports/errors`} target="_blank">Reporte HTML de errores</a><a href={`${apiUrl}/api/reports/symbols`} target="_blank">Reporte HTML de símbolos</a></footer>
        </article>
      </section>
    </main>
  )
}

export default App
