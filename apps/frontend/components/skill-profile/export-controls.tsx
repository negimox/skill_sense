'use client';

import React, { useState } from 'react';
import { Download, FileJson, FileText, Database } from 'lucide-react';
import { Button } from '../ui/button';
import { downloadExportedProfile } from '@/lib/api/skills';

interface ExportControlsProps {
  profileId: string;
}

export const ExportControls: React.FC<ExportControlsProps> = ({ profileId }) => {
  const [isExporting, setIsExporting] = useState(false);
  const [maskPii, setMaskPii] = useState(true);

  const handleExport = async (format: 'json' | 'csv' | 'sap') => {
    setIsExporting(true);
    try {
      await downloadExportedProfile(profileId, format, maskPii);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export profile. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="bg-gray-900/70 backdrop-blur-sm rounded-lg border border-gray-800/50 p-6">
      <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <Download className="w-5 h-5 text-sky-400" />
        Export Profile
      </h3>

      <p className="text-gray-400 mb-4">Download your skill profile in various formats</p>

      {/* Privacy toggle */}
      <div className="mb-4 flex items-center gap-2">
        <input
          type="checkbox"
          id="mask-pii"
          checked={maskPii}
          onChange={(e) => setMaskPii(e.target.checked)}
          className="w-4 h-4 text-sky-500 bg-gray-800 border-gray-600 rounded focus:ring-sky-500"
        />
        <label htmlFor="mask-pii" className="text-sm text-gray-300">
          Mask personal information (email, phone)
        </label>
      </div>

      {/* Export buttons */}
      <div className="grid grid-cols-1 gap-3">
        <Button
          onClick={() => handleExport('json')}
          disabled={isExporting}
          variant="outline"
          className="flex items-center justify-center gap-2 bg-gray-800/50 border-gray-700 text-gray-300 hover:bg-gray-700/50"
        >
          <FileJson className="w-4 h-4" />
          Export JSON
        </Button>

        <Button
          onClick={() => handleExport('csv')}
          disabled={isExporting}
          variant="outline"
          className="flex items-center justify-center gap-2 bg-gray-800/50 border-gray-700 text-gray-300 hover:bg-gray-700/50"
        >
          <FileText className="w-4 h-4" />
          Export CSV
        </Button>

        <Button
          onClick={() => handleExport('sap')}
          disabled={isExporting}
          variant="outline"
          className="flex items-center justify-center gap-2 bg-gray-800/50 border-gray-700 text-gray-300 hover:bg-gray-700/50"
        >
          <Database className="w-4 h-4" />
          Export SAP
        </Button>
      </div>

      {isExporting && (
        <div className="mt-4 text-sm text-gray-400 text-center">Preparing download...</div>
      )}

      {/* Format descriptions */}
      <div className="mt-4 space-y-2 text-xs text-gray-500">
        <div>
          <strong className="text-gray-400">JSON:</strong> Full data export with all evidence and
          metadata
        </div>
        <div>
          <strong className="text-gray-400">CSV:</strong> Spreadsheet format with skill summary
        </div>
        <div>
          <strong className="text-gray-400">SAP:</strong> SAP-compatible format with ESCO taxonomy
          IDs
        </div>
      </div>
    </div>
  );
};
