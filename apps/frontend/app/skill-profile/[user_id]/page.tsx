'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Filter, Loader2, ArrowRight, Sparkles } from 'lucide-react';
import {
  getSkillProfile,
  getSkillProfileByResumeId,
  updateSkillAction,
  matchJob,
  SkillProfile,
  SkillItem,
  JobMatchResponse,
} from '@/lib/api/skills';
import { SkillCard } from '@/components/skill-profile/skill-card';
import { EvidenceModal } from '@/components/skill-profile/evidence-modal';
import { ExportControls } from '@/components/skill-profile/export-controls';
import { Button } from '@/components/ui/button';
import BackgroundContainer from '@/components/common/background-container';

export default function SkillProfilePage() {
  const params = useParams();
  const router = useRouter();
  const resumeId = params.user_id as string;

  const [profile, setProfile] = useState<SkillProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<SkillItem | null>(null);
  const [isEvidenceModalOpen, setIsEvidenceModalOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [editingSkill, setEditingSkill] = useState<string | null>(null);
  const [editedName, setEditedName] = useState('');
  const [selectedSkills, setSelectedSkills] = useState<Set<string>>(new Set());
  const [isMultiSelectMode, setIsMultiSelectMode] = useState(false);

  // Load profile on mount
  useEffect(() => {
    loadProfile();
  }, [resumeId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try to get profile by resume ID
      const data = await getSkillProfileByResumeId(resumeId);
      setProfile(data);
    } catch (err: any) {
      console.error('Failed to load profile:', err);
      setError(err.message || 'Failed to load skill profile');
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (skillName: string) => {
    if (!profile) return;

    try {
      await updateSkillAction({
        profile_id: profile.profile_id,
        skill_name: skillName,
        action: 'accept',
      });

      // Update the skill in the local state instead of reloading
      setProfile((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          skills: prev.skills.map((s) =>
            s.name === skillName ? { ...s, manual_status: 'accepted' } : s
          ),
        };
      });
    } catch (err) {
      console.error('Failed to accept skill:', err);
      alert('Failed to accept skill');
    }
  };

  const handleReject = async (skillName: string) => {
    if (!profile) return;

    try {
      await updateSkillAction({
        profile_id: profile.profile_id,
        skill_name: skillName,
        action: 'reject',
      });

      // Update the skill in the local state instead of reloading
      setProfile((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          skills: prev.skills.map((s) =>
            s.name === skillName ? { ...s, manual_status: 'rejected' } : s
          ),
        };
      });
    } catch (err) {
      console.error('Failed to reject skill:', err);
      alert('Failed to reject skill');
    }
  };

  const handleEditStart = (skillName: string) => {
    setEditingSkill(skillName);
    const skill = profile?.skills.find((s) => s.name === skillName);
    setEditedName(skill?.name || '');
  };

  const handleEditSave = async () => {
    if (!profile || !editingSkill) return;

    try {
      await updateSkillAction({
        profile_id: profile.profile_id,
        skill_name: editingSkill,
        action: 'edit',
        edited_name: editedName,
      });

      // Update the skill in the local state instead of reloading
      setProfile((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          skills: prev.skills.map((s) =>
            s.name === editingSkill ? { ...s, manual_status: 'edited', edited_name: editedName } : s
          ),
        };
      });
      setEditingSkill(null);
    } catch (err) {
      console.error('Failed to edit skill:', err);
      alert('Failed to edit skill');
    }
  };

  const handleToggleSelect = (skillName: string) => {
    setSelectedSkills((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(skillName)) {
        newSet.delete(skillName);
      } else {
        newSet.add(skillName);
      }
      return newSet;
    });
  };

  const handleBulkAccept = async () => {
    if (!profile || selectedSkills.size === 0) return;

    try {
      // Process all selected skills
      await Promise.all(
        Array.from(selectedSkills).map((skillName) =>
          updateSkillAction({
            profile_id: profile.profile_id,
            skill_name: skillName,
            action: 'accept',
          })
        )
      );

      // Update the skills in the local state
      setProfile((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          skills: prev.skills.map((s) =>
            selectedSkills.has(s.name) ? { ...s, manual_status: 'accepted' } : s
          ),
        };
      });

      setSelectedSkills(new Set());
      setIsMultiSelectMode(false);
    } catch (err) {
      console.error('Failed to accept skills:', err);
      alert('Failed to accept some skills');
    }
  };

  const handleBulkReject = async () => {
    if (!profile || selectedSkills.size === 0) return;

    try {
      // Process all selected skills
      await Promise.all(
        Array.from(selectedSkills).map((skillName) =>
          updateSkillAction({
            profile_id: profile.profile_id,
            skill_name: skillName,
            action: 'reject',
          })
        )
      );

      // Update the skills in the local state
      setProfile((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          skills: prev.skills.map((s) =>
            selectedSkills.has(s.name) ? { ...s, manual_status: 'rejected' } : s
          ),
        };
      });

      setSelectedSkills(new Set());
      setIsMultiSelectMode(false);
    } catch (err) {
      console.error('Failed to reject skills:', err);
      alert('Failed to reject some skills');
    }
  };

  const handleViewEvidence = (skill: SkillItem) => {
    setSelectedSkill(skill);
    setIsEvidenceModalOpen(true);
  };

  const handleMatchJob = async (jobText: string): Promise<JobMatchResponse> => {
    if (!profile) {
      throw new Error('No profile loaded');
    }

    return await matchJob({
      profile_id: profile.profile_id,
      job_text: jobText,
      top_k: 10,
    });
  };

  const filteredSkills = profile?.skills.filter((skill) => {
    if (filterStatus === 'all') return true;
    return skill.manual_status === filterStatus;
  });

  if (loading) {
    return (
      <BackgroundContainer innerClassName="justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-sky-400 mx-auto mb-4" />
          <p className="text-gray-300 text-lg">Loading your skill profile...</p>
        </div>
      </BackgroundContainer>
    );
  }

  if (error || !profile) {
    return (
      <BackgroundContainer innerClassName="justify-center">
        <div className="bg-gray-900/70 backdrop-blur-sm rounded-lg border border-red-500/30 p-8 max-w-md">
          <h1 className="text-2xl font-bold text-red-400 mb-4">Error</h1>
          <p className="text-gray-300 mb-6">
            {error || 'Profile not found. Please upload a resume first.'}
          </p>
          <Button
            onClick={() => router.push('/resume')}
            className="w-full bg-gradient-to-r from-sky-500 to-blue-500 hover:from-sky-600 hover:to-blue-600"
          >
            Upload Resume
          </Button>
        </div>
      </BackgroundContainer>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-600 via-orange-400 to-purple-700 p-2">
      <div className="w-full min-h-[calc(100vh-1rem)] bg-zinc-950 rounded-2xl p-8 overflow-y-auto">
        <div className="max-w-7xl mx-auto w-full">
          {/* Header */}
          <div className="mb-8 text-center">
            <h1 className="text-5xl sm:text-6xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-sky-400 via-blue-400 to-violet-500">
              SkillSense Profile
            </h1>
            <p className="text-gray-300 text-lg mb-6">
              AI-powered skill discovery and job matching
            </p>

            {/* Continue to Job Matching Button */}
            <div className="mb-6">
              {profile.skills.filter((s) => s.manual_status === 'suggested').length > 0 && (
                <div className="mb-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 max-w-2xl mx-auto">
                  <p className="text-yellow-300 text-sm text-center">
                    ⚠️ You have{' '}
                    {profile.skills.filter((s) => s.manual_status === 'suggested').length} suggested
                    skill(s) pending review. Please accept or reject them before continuing to job
                    matching.
                  </p>
                </div>
              )}
              <button
                onClick={() => {
                  const suggestedCount = profile.skills.filter(
                    (s) => s.manual_status === 'suggested'
                  ).length;
                  if (suggestedCount > 0) {
                    // Scroll to skills section
                    document
                      .querySelector('[data-skills-section]')
                      ?.scrollIntoView({ behavior: 'smooth' });
                    return;
                  }
                  // Store resume ID and navigate to jobs page
                  if (typeof window !== 'undefined') {
                    localStorage.setItem('skillsense:lastResumeId', resumeId);
                  }
                  router.push('/jobs');
                }}
                disabled={profile.skills.filter((s) => s.manual_status === 'suggested').length > 0}
                className={`inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white bg-sky-600 hover:bg-sky-700 rounded-lg transition-colors duration-200 ${
                  profile.skills.filter((s) => s.manual_status === 'suggested').length > 0
                    ? 'opacity-50 cursor-not-allowed'
                    : ''
                }`}
              >
                Continue to Job Matching
                <ArrowRight className="ml-2 w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gray-900/70 backdrop-blur-sm rounded-lg border border-sky-500/30 p-6">
              <div className="text-3xl font-bold bg-gradient-to-r from-sky-400 to-blue-400 text-transparent bg-clip-text">
                {profile.skills.length}
              </div>
              <div className="text-sm text-gray-400">Total Skills</div>
            </div>
            <div className="bg-gray-900/70 backdrop-blur-sm rounded-lg border border-green-500/30 p-6">
              <div className="text-3xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 text-transparent bg-clip-text">
                {profile.skills.filter((s) => s.manual_status === 'accepted').length}
              </div>
              <div className="text-sm text-gray-400">Accepted</div>
            </div>
            <div className="bg-gray-900/70 backdrop-blur-sm rounded-lg border border-yellow-500/30 p-6">
              <div className="text-3xl font-bold bg-gradient-to-r from-yellow-400 to-orange-400 text-transparent bg-clip-text">
                {profile.skills.filter((s) => s.manual_status === 'suggested').length}
              </div>
              <div className="text-sm text-gray-400">Suggested</div>
            </div>
            <div className="bg-gray-900/70 backdrop-blur-sm rounded-lg border border-purple-500/30 p-6">
              <div className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 text-transparent bg-clip-text">
                {profile.skills.filter((s) => s.category === 'technical').length}
              </div>
              <div className="text-sm text-gray-400">Technical</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8" data-skills-section>
            {/* Left column: Skills */}
            <div className="lg:col-span-2 space-y-6">
              {/* Filter and Multi-select controls */}
              <div className="bg-gray-900/70 backdrop-blur-sm rounded-lg border border-gray-800/50 p-4 space-y-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <Filter className="w-4 h-4 text-sky-400" />
                  <span className="text-sm font-medium text-gray-300">Filter:</span>
                  {['all', 'suggested', 'accepted', 'rejected', 'edited'].map((status) => (
                    <Button
                      key={status}
                      onClick={() => setFilterStatus(status)}
                      variant={filterStatus === status ? 'default' : 'outline'}
                      size="sm"
                      className={
                        filterStatus === status
                          ? 'bg-gradient-to-r from-sky-500 to-blue-500 text-white border-0'
                          : 'bg-gray-800/50 text-gray-300 border-gray-700 hover:bg-gray-700/50'
                      }
                    >
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </Button>
                  ))}
                </div>

                {/* Multi-select mode controls */}
                <div className="flex items-center gap-2 flex-wrap border-t border-gray-800 pt-4">
                  <Button
                    onClick={() => {
                      setIsMultiSelectMode(!isMultiSelectMode);
                      setSelectedSkills(new Set());
                    }}
                    size="sm"
                    variant="outline"
                    className={
                      isMultiSelectMode
                        ? 'bg-gradient-to-r from-sky-500 to-blue-500 text-white border-0'
                        : 'bg-gray-800/50 text-gray-300 border-gray-700 hover:bg-gray-700/50'
                    }
                  >
                    {isMultiSelectMode ? '✓ Multi-Select Mode' : 'Enable Multi-Select'}
                  </Button>

                  {isMultiSelectMode && (
                    <>
                      <span className="text-sm text-gray-400">{selectedSkills.size} selected</span>
                      <Button
                        onClick={handleBulkAccept}
                        disabled={selectedSkills.size === 0}
                        size="sm"
                        className="bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
                      >
                        Accept Selected
                      </Button>
                      <Button
                        onClick={handleBulkReject}
                        disabled={selectedSkills.size === 0}
                        size="sm"
                        className="bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
                      >
                        Reject Selected
                      </Button>
                    </>
                  )}
                </div>
              </div>

              {/* Skills grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredSkills && filteredSkills.length > 0 ? (
                  filteredSkills.map((skill) => (
                    <SkillCard
                      key={skill.skill_id || skill.name}
                      skill={skill}
                      onAccept={handleAccept}
                      onReject={handleReject}
                      onEdit={handleEditStart}
                      onViewEvidence={handleViewEvidence}
                      isMultiSelectMode={isMultiSelectMode}
                      isSelected={selectedSkills.has(skill.name)}
                      onToggleSelect={handleToggleSelect}
                    />
                  ))
                ) : (
                  <div className="col-span-2 text-center py-12 text-gray-500">
                    No skills found for this filter
                  </div>
                )}
              </div>
            </div>

            {/* Right column: Export and info */}
            <div className="space-y-6">
              <ExportControls profileId={profile.profile_id} />

              {/* Profile info */}
              <div className="bg-gray-900/70 backdrop-blur-sm rounded-lg border border-gray-800/50 p-6">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-sky-400" />
                  Profile Info
                </h3>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-gray-400">Profile ID:</span>
                    <div className="font-mono text-xs text-gray-300 break-all mt-1 bg-gray-800/50 p-2 rounded">
                      {profile.profile_id}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400">Resume ID:</span>
                    <div className="font-mono text-xs text-gray-300 break-all mt-1 bg-gray-800/50 p-2 rounded">
                      {profile.resume_id}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400">Created:</span>
                    <div className="text-gray-300 mt-1">
                      {new Date(profile.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400">Last Updated:</span>
                    <div className="text-gray-300 mt-1">
                      {new Date(profile.updated_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <EvidenceModal
        skill={selectedSkill}
        isOpen={isEvidenceModalOpen}
        onClose={() => setIsEvidenceModalOpen(false)}
      />

      {editingSkill && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900/90 backdrop-blur-md border border-gray-800 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-xl font-bold mb-4 text-white">Edit Skill</h3>
            <input
              type="text"
              value={editedName}
              onChange={(e) => setEditedName(e.target.value)}
              className="w-full bg-gray-800/50 border border-gray-700 text-white rounded px-3 py-2 mb-4 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 outline-none"
              placeholder="Enter skill name"
            />
            <div className="flex gap-2">
              <Button
                onClick={handleEditSave}
                className="flex-1 bg-gradient-to-r from-sky-500 to-blue-500 hover:from-sky-600 hover:to-blue-600"
              >
                Save
              </Button>
              <Button
                onClick={() => setEditingSkill(null)}
                variant="outline"
                className="flex-1 border-gray-700 text-gray-300 hover:bg-gray-800"
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
