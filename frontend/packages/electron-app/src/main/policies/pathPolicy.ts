import path from 'node:path'

import { app } from 'electron'

export type WorkDirs = {
  workDir: string
  configDir: string
  dataDir: string
  runtimeDir: string
  exportsDir: string
  logsDir: string
}

export function getPortableRootDir(): string {
  const appPath = app.getAppPath()
  return app.isPackaged ? path.resolve(appPath, '..') : appPath
}

export function resolveWorkDirs(): WorkDirs {
  const rootDir = getPortableRootDir()

  const workDir = path.join(rootDir, 'data')
  const configDir = path.join(rootDir, 'config')
  const dataDir = path.join(workDir, 'data')
  const runtimeDir = path.join(workDir, 'runtime')
  const exportsDir = path.join(workDir, 'exports')
  const logsDir = path.join(workDir, 'logs')

  return {
    workDir,
    configDir,
    dataDir,
    runtimeDir,
    exportsDir,
    logsDir,
  }
}

