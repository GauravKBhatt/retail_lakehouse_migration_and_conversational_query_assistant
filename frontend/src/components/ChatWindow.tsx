import { useAtom } from 'jotai'
import { isTypingAtom } from '../atoms'
import type { Message } from '../hooks/useChat'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'

interface ChatWindowProps {
  messages: Message[]
}

export function ChatWindow({ messages }: ChatWindowProps) {
  const [isTyping] = useAtom(isTypingAtom)

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {messages.length === 0 && !isTyping && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-teal-50 flex items-center justify-center">
              <svg className="w-8 h-8 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-gray-700 mb-1">Ask your retail data</h2>
            <p className="text-sm text-gray-400">Ask questions about sales, products, stores, and more using natural language.</p>
          </div>
        </div>
      )}
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} items-end gap-2`}
        >
          {msg.role === 'assistant' && (
            <div className="w-7 h-7 rounded-full bg-teal-600 flex items-center justify-center shrink-0">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          )}
          <div
            className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
              msg.role === 'user'
                ? 'bg-teal-600 text-white rounded-br-sm'
                : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm'
            }`}
          >
            {msg.role === 'assistant' ? (
              <Markdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-xl font-bold text-gray-900 mt-3 mb-2">{children}</h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-lg font-bold text-gray-900 mt-3 mb-2">{children}</h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-base font-semibold text-gray-900 mt-2 mb-1">{children}</h3>
                  ),
                  p: ({ children }) => (
                    <p className="text-sm text-gray-800 leading-relaxed mb-2 last:mb-0">{children}</p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-inside text-sm text-gray-800 space-y-1 mb-2">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-inside text-sm text-gray-800 space-y-1 mb-2">{children}</ol>
                  ),
                  li: ({ children }) => (
                    <li className="text-sm text-gray-800">{children}</li>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold text-gray-900">{children}</strong>
                  ),
                  em: ({ children }) => (
                    <em className="italic text-gray-700">{children}</em>
                  ),
                  code: ({ className, children }) => {
                    const isInline = !className
                    if (isInline) {
                      return (
                        <code className="bg-gray-100 text-teal-700 px-1.5 py-0.5 rounded text-xs font-mono">
                          {children}
                        </code>
                      )
                    }
                    return (
                      <code className={`${className ?? ''} block`}>{children}</code>
                    )
                  },
                  pre: ({ children }) => (
                    <pre className="bg-gray-900 text-[#FFA62B] p-3 rounded-lg mt-2 mb-2 overflow-x-auto text-sm leading-relaxed font-mono">
                      {children}
                    </pre>
                  ),
                  table: ({ children }) => (
                    <div className="overflow-x-auto mt-3 mb-3">
                      <table className="min-w-full border border-gray-200 rounded-lg overflow-hidden">
                        {children}
                      </table>
                    </div>
                  ),
                  thead: ({ children }) => (
                    <thead className="bg-gray-50">{children}</thead>
                  ),
                  tbody: ({ children }) => (
                    <tbody className="bg-white divide-y divide-gray-200">{children}</tbody>
                  ),
                  th: ({ children }) => (
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">{children}</td>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-teal-400 pl-3 italic text-gray-600 my-2">
                      {children}
                    </blockquote>
                  ),
                  a: ({ href, children }) => (
                    <a href={href} className="text-teal-600 underline hover:text-teal-800" target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  ),
                  hr: () => (
                    <hr className="border-gray-200 my-3" />
                  ),
                }}
              >
                {msg.content}
              </Markdown>
            ) : (
              msg.content
            )}
          </div>
        </div>
      ))}
      {isTyping && (
        <div className="flex justify-start items-end gap-2">
          <div className="w-7 h-7 rounded-full bg-teal-600 flex items-center justify-center shrink-0">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce [animation-delay:0.15s]" />
              <div className="w-2 h-2 bg-teal-600 rounded-full animate-bounce [animation-delay:0.3s]" />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
