import React, { useState } from 'react';
import { CheckIcon, DocumentDuplicateIcon } from '@heroicons/react/24/outline';

interface CopyToClipboardProps {
  text: string;
  className?: string;
}

export const CopyToClipboard: React.FC<CopyToClipboardProps> = ({
  text,
  className = ''
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={`absolute top-2 right-2 p-2 bg-gray-700 dark:bg-gray-600 text-white rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-gray-600 dark:hover:bg-gray-500 ${className}`}
      title={copied ? 'Copied!' : 'Copy code'}
    >
      {copied ? (
        <CheckIcon className="h-4 w-4 text-green-400" />
      ) : (
        <DocumentDuplicateIcon className="h-4 w-4" />
      )}
    </button>
  );
};