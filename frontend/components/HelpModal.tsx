'use client';

import { X, Keyboard, Zap, Eye, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function HelpModal({ isOpen, onClose }: HelpModalProps) {
  if (!isOpen) return null;

  const shortcuts = [
    { key: 'R', description: 'Refresh dashboard', icon: <RefreshCw className="w-4 h-4" /> },
    { key: 'T', description: 'Trigger analysis', icon: <Zap className="w-4 h-4" /> },
    { key: 'H', description: 'Show/hide help', icon: <Keyboard className="w-4 h-4" /> },
    { key: 'Esc', description: 'Close modals', icon: <X className="w-4 h-4" /> },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-lg p-6 max-w-md w-full mx-4"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Help & Shortcuts</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
              <Keyboard className="w-5 h-5 mr-2" />
              Keyboard Shortcuts
            </h3>
            <div className="space-y-2">
              {shortcuts.map((shortcut, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div className="flex items-center space-x-2">
                    {shortcut.icon}
                    <span className="text-sm text-gray-700">{shortcut.description}</span>
                  </div>
                  <kbd className="px-2 py-1 bg-gray-200 text-gray-800 text-xs rounded font-mono">
                    {shortcut.key}
                  </kbd>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
              <Eye className="w-5 h-5 mr-2" />
              Dashboard Features
            </h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Real-time metrics with WebSocket updates</li>
              <li>• AI agent status monitoring</li>
              <li>• Interactive decision approval workflow</li>
              <li>• Alert management with severity levels</li>
              <li>• Historical trend visualization</li>
            </ul>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="w-full btn-primary"
          >
            Got it!
          </button>
        </div>
      </motion.div>
    </div>
  );
}