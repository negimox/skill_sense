'use client';

import React, { useState } from 'react';
import { Search, TrendingUp, AlertTriangle } from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { JobMatchResponse, MatchedSkill, MissingSkill } from '@/lib/api/skills';

interface JobMatchPanelProps {
  profileId: string;
  onMatch: (jobText: string) => Promise<JobMatchResponse>;
}

export const JobMatchPanel: React.FC<JobMatchPanelProps> = ({ profileId, onMatch }) => {
  const [jobText, setJobText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [matchResult, setMatchResult] = useState<JobMatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleMatch = async () => {
    if (!jobText.trim()) {
      setError('Please enter a job description');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await onMatch(jobText);
      setMatchResult(result);
    } catch (err) {
      setError('Failed to match job description. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const getMatchScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-orange-600';
  };

  const getMatchScoreLabel = (score: number) => {
    if (score >= 0.8) return 'Excellent Match!';
    if (score >= 0.6) return 'Good Match';
    if (score >= 0.4) return 'Partial Match';
    return 'Low Match';
  };

  return (
    <div className="space-y-6">
      {/* Input section */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Match Job Description</h2>
        <p className="text-gray-600 mb-4">
          Paste a job description below to see how your skills match up and identify gaps.
        </p>

        <Textarea
          value={jobText}
          onChange={(e) => setJobText(e.target.value)}
          placeholder="Paste the job description here..."
          className="min-h-[200px] mb-4"
        />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 p-3 rounded mb-4">
            {error}
          </div>
        )}

        <Button
          onClick={handleMatch}
          disabled={isLoading || !jobText.trim()}
          className="w-full sm:w-auto"
        >
          <Search className="w-4 h-4 mr-2" />
          {isLoading ? 'Analyzing...' : 'Analyze Match'}
        </Button>
      </div>

      {/* Results section */}
      {matchResult && (
        <div className="space-y-6">
          {/* Match score */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200 p-6">
            <div className="text-center">
              <div
                className={`text-5xl font-bold mb-2 ${getMatchScoreColor(matchResult.match_score)}`}
              >
                {Math.round(matchResult.match_score * 100)}%
              </div>
              <div className="text-xl font-semibold text-gray-800">
                {getMatchScoreLabel(matchResult.match_score)}
              </div>
            </div>
          </div>

          {/* Matched skills */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              Matched Skills ({matchResult.matched_skills.length})
            </h3>

            {matchResult.matched_skills.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {matchResult.matched_skills.map((skill, index) => (
                  <div key={index} className="border border-green-200 bg-green-50 rounded-lg p-3">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-semibold text-gray-900">{skill.name}</span>
                      <span className="text-green-700 text-sm font-medium">
                        {Math.round(skill.score * 100)}%
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                        {skill.category}
                      </span>
                      <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded-full">
                        Confidence: {Math.round(skill.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No matched skills found</p>
            )}
          </div>

          {/* Missing skills */}
          {matchResult.missing_skills.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                Skill Gaps ({matchResult.missing_skills.length})
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                {matchResult.missing_skills.map((skill, index) => (
                  <div key={index} className="border border-orange-200 bg-orange-50 rounded-lg p-3">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-semibold text-gray-900">{skill.name}</span>
                      <span className="text-orange-700 text-sm font-medium">
                        Gap: {Math.round(skill.estimated_gap * 100)}%
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                        {skill.category}
                      </span>
                      {skill.from_job_section && (
                        <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded-full">
                          From: {skill.from_job_section}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {matchResult.recommendations.length > 0 && (
            <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-3">💡 Recommendations</h3>
              <ul className="space-y-2">
                {matchResult.recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span className="text-gray-800">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
