import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const runtimeDir = path.join(__dirname, '..', 'runtime')
const dataFile = path.join(runtimeDir, 'data.json')

function ensureRuntime() {
  if (!fs.existsSync(runtimeDir)) {
    fs.mkdirSync(runtimeDir, { recursive: true })
  }

  if (!fs.existsSync(dataFile)) {
    fs.writeFileSync(
      dataFile,
      JSON.stringify(
        {
          tasks: [],
          works: [],
          assets: [],
          users: [],
        },
        null,
        2
      ),
      'utf8'
    )
  }
}

function readData() {
  ensureRuntime()
  return JSON.parse(fs.readFileSync(dataFile, 'utf8'))
}

function writeData(data) {
  ensureRuntime()
  fs.writeFileSync(dataFile, JSON.stringify(data, null, 2), 'utf8')
}

export function listCollection(name) {
  return readData()[name] || []
}

export function writeCollection(name, items) {
  const data = readData()
  data[name] = items
  writeData(data)
}

export function upsertCollectionItem(name, item, key = 'id') {
  const items = listCollection(name)
  const nextItems = items.filter((entry) => entry[key] !== item[key])
  nextItems.push(item)
  writeCollection(name, nextItems)
  return item
}

export function findCollectionItem(name, predicate) {
  return listCollection(name).find(predicate) || null
}
