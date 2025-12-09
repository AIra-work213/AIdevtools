import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import {
  oneDark,
  oneLight
} from 'react-syntax-highlighter/dist/esm/styles/prism';
import { CopyToClipboard } from './CopyToClipboard';

interface MarkdownRendererProps {
  children: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  children,
  className = ''
}) => {
  // Check if dark mode is active
  const isDarkMode = document.documentElement.classList.contains('dark');

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      className={`prose prose-sm dark:prose-invert max-w-none ${className}`}
      components={{
        // Code blocks with syntax highlighting
        code({ node, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '');
          const language = match ? match[1] : '';
          const inline = !match;

          if (!inline && language) {
            return (
              <div className="relative group">
                <SyntaxHighlighter
                  style={isDarkMode ? oneDark : oneLight as any}
                  language={language}
                  PreTag="div"
                  className="!mt-2 !mb-2 rounded-lg"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
                <CopyToClipboard text={String(children)} />
              </div>
            );
          }

          if (!inline) {
            return (
              <code
                className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono"
                {...props}
              >
                {children}
              </code>
            );
          }

          return (
            <code
              className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono"
              {...props}
            >
              {children}
            </code>
          );
        },

        // Blockquotes
        blockquote({ children }) {
          return (
            <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 my-2 italic text-gray-700 dark:text-gray-300">
              {children}
            </blockquote>
          );
        },

        // Tables
        table({ children }) {
          return (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                {children}
              </table>
            </div>
          );
        },

        // Table headers
        thead({ children }) {
          return (
            <thead className="bg-gray-50 dark:bg-gray-800">
              {children}
            </thead>
          );
        },

        // Table rows
        tr({ children }) {
          return (
            <tr className="divide-y divide-gray-200 dark:divide-gray-700">
              {children}
            </tr>
          );
        },

        // Table cells
        th({ children }) {
          return (
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {children}
            </th>
          );
        },

        td({ children }) {
          return (
            <td className="px-3 py-2 text-sm text-gray-900 dark:text-gray-100">
              {children}
            </td>
          );
        },

        // Links
        a({ href, children }) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 underline"
            >
              {children}
            </a>
          );
        },

        // Lists
        ul({ children }) {
          return (
            <ul className="list-disc list-inside my-2 space-y-1">
              {children}
            </ul>
          );
        },

        ol({ children }) {
          return (
            <ol className="list-decimal list-inside my-2 space-y-1">
              {children}
            </ol>
          );
        },

        // List items
        li({ children }) {
          return (
            <li className="text-gray-700 dark:text-gray-300">
              {children}
            </li>
          );
        },

        // Headings
        h1({ children }) {
          return (
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-4 mb-2">
              {children}
            </h1>
          );
        },

        h2({ children }) {
          return (
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mt-3 mb-2">
              {children}
            </h2>
          );
        },

        h3({ children }) {
          return (
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-2 mb-1">
              {children}
            </h3>
          );
        },

        // Horizontal rule
        hr() {
          return <hr className="my-4 border-gray-200 dark:border-gray-700" />;
        },

        // Paragraphs
        p({ children }) {
          return (
            <p className="my-2 text-gray-700 dark:text-gray-300">
              {children}
            </p>
          );
        },

        // Strong/Bold
        strong({ children }) {
          return (
            <strong className="font-semibold text-gray-900 dark:text-gray-100">
              {children}
            </strong>
          );
        },

        // Emphasis/Italic
        em({ children }) {
          return (
            <em className="italic text-gray-700 dark:text-gray-300">
              {children}
            </em>
          );
        },
      }}
    >
      {children}
    </ReactMarkdown>
  );
};