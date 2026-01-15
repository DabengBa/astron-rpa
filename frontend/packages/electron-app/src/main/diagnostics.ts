import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'

import { app, ipcMain } from 'electron'

import logger from './log'
import { config } from './config'
import { getPortableRootDir, resolveWorkDirs } from './policies/pathPolicy'

async function safeReadText(filePath: string): Promise<string | null> {
  try {
    return await fs.readFile(filePath, 'utf-8')
  } catch {
    return null
  }
}

async function ensureDir(dirPath: string): Promise<void> {
  await fs.mkdir(dirPath, { recursive: true })
}

async function collectLogFiles(logDir: string): Promise<string[]> {
  try {
    const names = await fs.readdir(logDir)
    return names
      .filter(n => n.endsWith('.log'))
      .slice(-10)
      .map(n => path.join(logDir, n))
  } catch {
    return []
  }
}

async function writeDiagnosticsBundle(): Promise<{ ok: boolean, outputPath?: string, error?: string }> {
  try {
    const rootDir = getPortableRootDir()
    const workDirs = resolveWorkDirs()

    const diagnosticsRoot = path.join(workDirs.exportsDir, 'diagnostics')
    await ensureDir(diagnosticsRoot)

    const ts = new Date().toISOString().replace(/[:.]/g, '-')
    const bundleDir = path.join(diagnosticsRoot, `diag-${ts}`)
    await ensureDir(bundleDir)

    const meta = {
      createdAt: new Date().toISOString(),
      appVersion: app.getVersion(),
      platform: process.platform,
      arch: process.arch,
      node: process.versions.node,
      electron: process.versions.electron,
      osRelease: os.release(),
      portableRootDir: rootDir,
      workDirs,
      remoteAddr: config.remote_addr,
    }

    await fs.writeFile(path.join(bundleDir, 'meta.json'), JSON.stringify(meta, null, 2), 'utf-8')

    const conf = await safeReadText(path.join(rootDir, 'conf.yaml'))
    if (conf)
      await fs.writeFile(path.join(bundleDir, 'conf.yaml'), conf, 'utf-8')

    const logDir = path.join(workDirs.workDir, 'logs')
    const logs = await collectLogFiles(logDir)
    if (logs.length) {
      const outLogDir = path.join(bundleDir, 'logs')
      await ensureDir(outLogDir)
      await Promise.all(logs.map(async (f) => {
        const base = path.basename(f)
        await fs.copyFile(f, path.join(outLogDir, base))
      }))
    }

    return { ok: true, outputPath: bundleDir }
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    logger.error('export diagnostics failed', msg)
    return { ok: false, error: msg }
  }
}

export function registerDiagnosticsIpc() {
  ipcMain.handle('export-diagnostics', async () => {
    return await writeDiagnosticsBundle()
  })
}
