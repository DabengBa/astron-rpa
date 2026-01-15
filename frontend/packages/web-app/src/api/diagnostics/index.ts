import { utilsManager } from '@/platform'

export type ExportDiagnosticsResult = {
  ok: boolean
  outputPath?: string
  error?: string
}

export async function exportDiagnostics(): Promise<ExportDiagnosticsResult> {
  return await utilsManager.invoke('export-diagnostics')
}
