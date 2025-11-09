// API client for skill profile management

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface EvidenceItem {
  source: string;
  snippet: string;
  score: number;
  offset?: number;
  href?: string;
  page_number?: number;
  line_number?: number;
}

export interface SkillItem {
  skill_id?: string;
  name: string;
  category: string;
  confidence: number;
  evidence: EvidenceItem[];
  mapped_taxonomy_id?: string;
  manual_status: 'suggested' | 'accepted' | 'rejected' | 'edited';
  edited_name?: string;
  tags?: string[];
}

export interface SkillProfile {
  profile_id: string;
  resume_id: string;
  skills: SkillItem[];
  privacy_settings: Record<string, boolean>;
  created_at: string;
  updated_at: string;
}

export interface SkillActionRequest {
  profile_id: string;
  skill_name: string;
  action: 'accept' | 'reject' | 'edit';
  edited_name?: string;
  edited_category?: string;
}

export interface MatchedSkill {
  name: string;
  score: number;
  category: string;
  confidence: number;
}

export interface MissingSkill {
  name: string;
  estimated_gap: number;
  category: string;
  from_job_section?: string;
}

export interface JobMatchResponse {
  match_score: number;
  matched_skills: MatchedSkill[];
  missing_skills: MissingSkill[];
  recommendations: string[];
}

export interface JobMatchRequest {
  profile_id: string;
  job_text: string;
  top_k?: number;
}

/**
 * Get skill profile by ID
 */
export async function getSkillProfile(profileId: string): Promise<SkillProfile> {
  const res = await fetch(`${API_URL}/api/v1/skills/profile/${profileId}`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!res.ok) {
    throw new Error(`Failed to load skill profile (status ${res.status})`);
  }

  return await res.json();
}

/**
 * Get skill profile by resume ID
 */
export async function getSkillProfileByResumeId(resumeId: string): Promise<SkillProfile> {
  const res = await fetch(`${API_URL}/api/v1/skills/profile/by-resume/${resumeId}`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!res.ok) {
    throw new Error(`Failed to load skill profile (status ${res.status})`);
  }

  return await res.json();
}

/**
 * Accept, reject, or edit a skill
 */
export async function updateSkillAction(request: SkillActionRequest): Promise<{
  success: boolean;
  message: string;
  updated_skill?: SkillItem;
}> {
  const res = await fetch(`${API_URL}/api/v1/skills/skill/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    throw new Error(`Skill action failed (status ${res.status})`);
  }

  return await res.json();
}

/**
 * Match user skills against a job description
 */
export async function matchJob(request: JobMatchRequest): Promise<JobMatchResponse> {
  const res = await fetch(`${API_URL}/api/v1/skills/match-job`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    throw new Error(`Job matching failed (status ${res.status})`);
  }

  return await res.json();
}

/**
 * Export skill profile in various formats
 */
export async function exportProfile(
  profileId: string,
  format: 'json' | 'csv' | 'sap' = 'json',
  maskPii: boolean = true
): Promise<Blob> {
  const params = new URLSearchParams({
    format,
    mask_pii: maskPii.toString(),
  });

  const res = await fetch(`${API_URL}/api/v1/skills/export/${profileId}?${params}`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!res.ok) {
    throw new Error(`Export failed (status ${res.status})`);
  }

  return await res.blob();
}

/**
 * Download exported profile
 */
export async function downloadExportedProfile(
  profileId: string,
  format: 'json' | 'csv' | 'sap' = 'json',
  maskPii: boolean = true
) {
  const blob = await exportProfile(profileId, format, maskPii);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `skill_profile_${profileId}.${format}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}
