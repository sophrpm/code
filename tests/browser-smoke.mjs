import { readFile, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

//iniciar Chromium con remote-debugging-port=9222 y ambos servidores antes de ejecutar
const page = await fetch('http://127.0.0.1:9222/json/new?http://127.0.0.1:5173', { method: 'PUT' }).then(r => r.json())
const socket = new WebSocket(page.webSocketDebuggerUrl)
await new Promise(resolve => socket.addEventListener('open', resolve, { once: true }))
let id = 0
const pending = new Map()
socket.addEventListener('message', event => {
  const message = JSON.parse(event.data)
  if (message.id && pending.has(message.id)) {
    pending.get(message.id)(message)
    pending.delete(message.id)
  }
})
async function send(method, params = {}) {
  const key = ++id
  const response = new Promise(resolve => pending.set(key, resolve))
  socket.send(JSON.stringify({ id: key, method, params }))
  const value = await response
  assert.equal(value.error, undefined, JSON.stringify(value))
  return value.result
}
async function evaluate(expression) {
  const response = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
  assert.equal(response.exceptionDetails, undefined, JSON.stringify(response))
  return response.result.value
}
async function waitFor(expression) {
  const result = await evaluate(`new Promise(resolve => { let attempts=0; const timer=setInterval(() => { if (${expression}) {clearInterval(timer);resolve(true)} else if (++attempts>200) {clearInterval(timer);resolve(false)} },50) })`)
  assert.equal(result, true, expression)
}
await send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 1100, deviceScaleFactor: 1, mobile: false })
await waitFor('document.querySelector("textarea") && document.body.innerText.includes("Backend conectado")')
const source = await readFile('examples/demo.oxs', 'utf8')
await evaluate(`(() => { const editor=document.querySelector('textarea'); Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(editor,${JSON.stringify(source)});editor.dispatchEvent(new Event('input',{bubbles:true})); })()`)
await evaluate(`Array.from(document.querySelectorAll('button')).find(b => b.textContent==='Compilar').click()`)
await waitFor('document.querySelector(".assembly").textContent.includes("ox_fn_fibonacci") && !document.querySelector("button.run").disabled')
assert.equal(await evaluate('document.querySelector(".console").textContent.includes("Fibonacci(10)")'), false)
await evaluate('document.querySelector("button.run").click()')
await waitFor('document.querySelector(".console").textContent.includes("Fibonacci(10): 55")')
assert.equal(await evaluate('document.querySelector(".timings").textContent.includes("Código de salida: 0")'), true)
await evaluate(`Array.from(document.querySelectorAll('.tabs button')).find(b => b.textContent.includes('Símbolos')).click()`)
await waitFor('document.querySelector(".report-content").textContent.includes("matriz")')
const screenshot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
await writeFile('docs/capturas/oxigennative-qemu.png', Buffer.from(screenshot.data, 'base64'))
await evaluate(`Array.from(document.querySelectorAll('.tabs button')).find(b => b.textContent==='AST').click()`)
assert.equal(await evaluate('document.querySelector(".dot-preview").textContent.includes("ArrayLiteral")'), true)
await send('Emulation.setDeviceMetricsOverride', { width: 700, height: 1000, deviceScaleFactor: 1, mobile: true })
assert.equal(await evaluate('document.documentElement.scrollWidth <= innerWidth'), true)
console.log('Navegador: compilación, QEMU, consola, tiempos, símbolos, AST y ancho móvil aprobados.')
socket.close()
