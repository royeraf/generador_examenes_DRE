import * as XLSX from 'xlsx'
import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'

export interface ExportColumn {
  header: string
  key: string
}

export function exportToExcel(
  columns: ExportColumn[],
  rows: Record<string, any>[],
  filename: string,
  sheetName = 'Datos',
) {
  const aoa: (string | number)[][] = [
    columns.map(c => c.header),
    ...rows.map(r => columns.map(c => r[c.key] ?? '')),
  ]
  const ws = XLSX.utils.aoa_to_sheet(aoa)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, sheetName)
  XLSX.writeFile(wb, filename)
}

export function exportToPdf(options: {
  title: string
  subtitle?: string
  columns: ExportColumn[]
  rows: Record<string, any>[]
  filename: string
  accent?: [number, number, number]
}) {
  const { title, subtitle, columns, rows, filename, accent = [20, 184, 166] } = options
  const doc = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' })

  doc.setFontSize(15)
  doc.setTextColor(30, 41, 59)
  doc.text(title, 40, 42)
  if (subtitle) {
    doc.setFontSize(9)
    doc.setTextColor(120, 130, 145)
    doc.text(subtitle, 40, 58)
  }

  autoTable(doc, {
    startY: subtitle ? 72 : 58,
    head: [columns.map(c => c.header)],
    body: rows.map(r => columns.map(c => String(r[c.key] ?? ''))),
    styles: { fontSize: 8, cellPadding: 4, overflow: 'linebreak' },
    headStyles: { fillColor: accent, textColor: 255, fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [245, 247, 250] },
    margin: { left: 40, right: 40 },
  })

  doc.save(filename)
}
