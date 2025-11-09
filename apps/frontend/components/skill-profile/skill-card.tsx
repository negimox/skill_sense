'use client';

import React from 'react';
import { Check, X, Edit2, AlertCircle } from 'lucide-react';
import { SkillItem } from '@/lib/api/skills';
import { Button } from '../ui/button';

interface SkillCardProps {
  skill: SkillItem;
  onAccept: (skillName: string) => void;
  onReject: (skillName: string) => void;
  onEdit: (skillName: string) => void;
  onViewEvidence: (skill: SkillItem) => void;
  isMultiSelectMode?: boolean;
  isSelected?: boolean;
  onToggleSelect?: (skillName: string) => void;
}

export const SkillCard: React.FC<SkillCardProps> = ({
  skill,
  onAccept,
  onReject,
  onEdit,
  onViewEvidence,
  isMultiSelectMode = false,
  isSelected = false,
  onToggleSelect,
}) => {
  const getStatusColor = () => {
    switch (skill.manual_status) {
      case 'accepted':
        return 'border-green-500/50 bg-green-900/20';
      case 'rejected':
        return 'border-red-500/50 bg-red-900/20 opacity-60';
      case 'edited':
        return 'border-blue-500/50 bg-blue-900/20';
      default:
        return 'border-gray-700 bg-gray-900/50';
    }
  };

  const getConfidenceColor = () => {
    if (skill.confidence >= 0.8) return 'text-green-400';
    if (skill.confidence >= 0.6) return 'text-yellow-400';
    return 'text-orange-400';
  };

  const getCategoryBadgeColor = () => {
    switch (skill.category) {
      case 'technical':
        return 'bg-blue-500/20 text-blue-300 border border-blue-500/30';
      case 'soft':
        return 'bg-purple-500/20 text-purple-300 border border-purple-500/30';
      case 'domain':
        return 'bg-green-500/20 text-green-300 border border-green-500/30';
      default:
        return 'bg-gray-500/20 text-gray-300 border border-gray-500/30';
    }
  };

  const displayName = skill.edited_name || skill.name;

  return (
    <div
      className={`relative p-4 rounded-lg border-2 transition-colors hover:border-sky-500/50 backdrop-blur-sm ${getStatusColor()} ${
        isSelected ? 'ring-2 ring-sky-500' : ''
      }`}
    >
      {/* Multi-select checkbox */}
      {isMultiSelectMode && skill.manual_status === 'suggested' && (
        <div className="absolute top-2 left-2">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelect?.(skill.name)}
            className="w-5 h-5 rounded border-gray-600 text-sky-600 focus:ring-sky-500 focus:ring-offset-0 cursor-pointer"
          />
        </div>
      )}

      {/* Status indicator */}
      {skill.manual_status !== 'suggested' && (
        <div className="absolute top-2 right-2">
          {skill.manual_status === 'accepted' && <Check className="w-5 h-5 text-green-400" />}
          {skill.manual_status === 'rejected' && <X className="w-5 h-5 text-red-400" />}
          {skill.manual_status === 'edited' && <Edit2 className="w-5 h-5 text-blue-400" />}
        </div>
      )}

      {/* Skill header */}
      <div className="mb-3">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-lg font-semibold text-white">{displayName}</h3>
        </div>

        <div className="flex items-center gap-2 mt-2">
          {/* Category badge */}
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${getCategoryBadgeColor()}`}>
            {skill.category}
          </span>

          {/* Confidence score */}
          <span className={`text-sm font-medium ${getConfidenceColor()}`}>
            {Math.round(skill.confidence * 100)}% confidence
          </span>
        </div>
      </div>

      {/* Evidence count */}
      <div className="mb-3">
        <button
          onClick={() => onViewEvidence(skill)}
          className="text-sm text-sky-400 hover:text-sky-300 underline flex items-center gap-1"
        >
          <AlertCircle className="w-4 h-4" />
          View {skill.evidence.length} evidence{skill.evidence.length !== 1 ? 's' : ''}
        </button>
      </div>

      {/* ESCO ID if available */}
      {skill.mapped_taxonomy_id && (
        <div className="mb-3 text-xs text-gray-400 font-mono bg-gray-800/50 p-1 rounded">
          ESCO ID: {skill.mapped_taxonomy_id}
        </div>
      )}

      {/* Action buttons */}
      {skill.manual_status === 'suggested' && !isMultiSelectMode && (
        <div className="flex gap-2">
          <Button
            onClick={() => onAccept(skill.name)}
            size="sm"
            className="flex-1 bg-green-600 hover:bg-green-700 text-white"
          >
            <Check className="w-4 h-4 mr-1" />
            Accept
          </Button>
          <Button
            onClick={() => onEdit(skill.name)}
            size="sm"
            variant="outline"
            className="flex-1 border-gray-600 text-gray-300 hover:bg-gray-800"
          >
            <Edit2 className="w-4 h-4 mr-1" />
            Edit
          </Button>
          <Button
            onClick={() => onReject(skill.name)}
            size="sm"
            variant="destructive"
            className="flex-1 bg-red-600 hover:bg-red-700"
          >
            <X className="w-4 h-4 mr-1" />
            Reject
          </Button>
        </div>
      )}

      {skill.manual_status === 'suggested' && isMultiSelectMode && (
        <div className="text-sm text-gray-400 font-medium text-center">
          Select to accept or reject
        </div>
      )}

      {skill.manual_status === 'accepted' && (
        <div className="text-sm text-green-400 font-medium">✓ Accepted</div>
      )}

      {skill.manual_status === 'rejected' && (
        <div className="text-sm text-red-400 font-medium">✗ Rejected</div>
      )}

      {skill.manual_status === 'edited' && (
        <div className="text-sm text-blue-400 font-medium">
          ✎ Edited{skill.edited_name && ` (was: ${skill.name})`}
        </div>
      )}
    </div>
  );
};
