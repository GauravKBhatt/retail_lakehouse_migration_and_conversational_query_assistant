import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface LogsPanelProps {
  open: boolean
  onClose: () => void
}

export function LogsPanel({ open, onClose }: LogsPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)

  const { data: logs, isFetching } = useQuery({
    queryKey: ['logs'],
    queryFn: () => axios.get('http://localhost:8000/logs?lines=300').then(r => r.data),
    refetchInterval: 3000,
    enabled: open,
  })

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, autoScroll])

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 30
    setAutoScroll(atBottom)
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-gray-900 rounded-2xl shadow-2xl w-[900px] max-h-[85vh] flex flex-col border border-gray-700">
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h2 className="text-white font-semibold text-sm">Server Logs</h2>
            {isFetching && <span className="text-xs text-gray-500 ml-2">refreshing...</span>}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div
          className="flex-1 overflow-y-auto p-4 font-mono text-xs leading-relaxed text-gray-300"
          onScroll={handleScroll}
        >
          {logs ? logs.split('\n').map((line: string, i: number) => {
            const isError = /ERROR|Exception|Traceback/i.test(line)
            const isWarn = /WARN/i.test(line)
            return (
              <div key={i} className={`whitespace-pre-wrap ${isError ? 'text-red-400' : isWarn ? 'text-yellow-400' : 'text-gray-300'}`}>
                {line}
              </div>
            )
          }) : (
            <div className="text-gray-500">Loading logs...</div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  )
}
