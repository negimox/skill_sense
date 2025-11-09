'use client';

import React from 'react';
import { X, ExternalLink } from 'lucide-react';
import { SkillItem, EvidenceItem } from '@/lib/api/skills';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';

interface EvidenceModalProps {
  skill: SkillItem | null;
  isOpen: boolean;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({ skill, isOpen, onClose }) => {
  if (!skill) return null;

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-orange-600';
  };

  const getSourceBadgeColor = (source: string) => {
    switch (source.toLowerCase()) {
      case 'resume':
        return 'bg-blue-100 text-blue-800';
      case 'linkedin':
        return 'bg-indigo-100 text-indigo-800';
      case 'github':
        return 'bg-gray-800 text-white';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">
            Evidence for "{skill.edited_name || skill.name}"
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Summary */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600">Confidence Score:</span>
                <div className={`text-2xl font-bold ${getScoreColor(skill.confidence)}`}>
                  {Math.round(skill.confidence * 100)}%
                </div>
              </div>
              <div>
                <span className="text-sm text-gray-600">Total Evidence:</span>
                <div className="text-2xl font-bold text-gray-900">{skill.evidence.length}</div>
              </div>
            </div>
          </div>

          {/* Evidence list */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-gray-900">Evidence Trails</h3>
            {skill.evidence.map((evidence, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                {/* Evidence header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2 py-1 rounded-full font-medium ${getSourceBadgeColor(
                        evidence.source
                      )}`}
                    >
                      {evidence.source}
                    </span>
                    <span className={`text-sm font-medium ${getScoreColor(evidence.score)}`}>
                      Relevance: {Math.round(evidence.score * 100)}%
                    </span>
                  </div>
                  {evidence.href && (
                    <a
                      href={evidence.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      <ExternalLink className="w-4 h-4" />
                      <span className="text-sm">View source</span>
                    </a>
                  )}
                </div>

                {/* Snippet */}
                <div className="bg-gray-50 p-3 rounded border-l-4 border-blue-500">
                  <p className="text-sm text-gray-800 leading-relaxed">"{evidence.snippet}"</p>
                </div>

                {/* Metadata */}
                <div className="flex gap-4 mt-2 text-xs text-gray-500">
                  {evidence.page_number && <span>Page {evidence.page_number}</span>}
                  {evidence.line_number && <span>Line {evidence.line_number}</span>}
                  {evidence.offset && <span>Position: {evidence.offset}</span>}
                </div>
              </div>
            ))}
          </div>

          {skill.evidence.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No evidence available for this skill
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
