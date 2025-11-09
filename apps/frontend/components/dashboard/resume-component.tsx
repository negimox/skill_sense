import React from 'react';

interface PersonalInfo {
	name?: string;
	title?: string;
	email?: string;
	phone?: string;
	location?: string;
	website?: string;
	linkedin?: string;
	github?: string;
}

interface Experience {
    id: number;
    title?: string;
    company?: string;
    location?: string;
    years?: string;
    description?: string[];
}

interface Education {
    id: number;
    institution?: string;
    degree?: string;
    years?: string;
    description?: string;
}

interface Project {
    id: number;
    name?: string;
    role?: string;
    years?: string;
    description?: string[];
}

interface AdditionalInfo {
    technicalSkills?: string[];
    languages?: string[];
    certificationsTraining?: string[];
    awards?: string[];
}

interface GitHubTopRepository {
    name: string;
    description?: string;
    stars: number;
    language?: string;
    url: string;
}

interface GitHubProfile {
    username?: string;
    profileUrl?: string;
    topLanguages?: string[];
    totalStars?: number;
    totalRepos?: number;
    followers?: number;
    topRepositories?: GitHubTopRepository[];
    recentContributions?: number;
}

interface ResumeData {
    personalInfo?: PersonalInfo;
    summary?: string;
    workExperience?: Experience[];
    education?: Education[];
    personalProjects?: Project[];
    additional?: AdditionalInfo;
    githubProfile?: GitHubProfile;
}

interface ResumeProps {
	resumeData: ResumeData;
}

const Resume: React.FC<ResumeProps> = ({ resumeData }) => {
    console.log('Rendering Resume Component with data:', resumeData);
    const { personalInfo, summary, workExperience, education, personalProjects, additional, githubProfile } = resumeData;

	// Helper function to render contact details only if they exist
	const renderContactDetail = (label: string, value?: string, hrefPrefix: string = '') => {
		if (!value) return null;
		// Ensure website, linkedin, github links start with https:// if not already present
		let finalHrefPrefix = hrefPrefix;
		if (
			['Website', 'LinkedIn', 'GitHub'].includes(label) &&
			!value.startsWith('http') &&
			!value.startsWith('//')
		) {
			finalHrefPrefix = 'https://';
		}
		const href = finalHrefPrefix + value;
		const isLink =
			finalHrefPrefix.startsWith('http') ||
			finalHrefPrefix.startsWith('mailto:') ||
			finalHrefPrefix.startsWith('tel:');

		return (
			<div className="text-sm">
				<span className="font-semibold text-gray-200">{label}:</span>{' '}
				{isLink ? (
					<a
						href={href}
						target="_blank"
						rel="noopener noreferrer"
						className="text-blue-400 hover:underline break-all"
					>
						{value}
					</a>
				) : (
					<span className="break-all text-gray-300">{value}</span>
				)}
			</div>
		);
	};

	return (
		// Main container with dark background and base text color
		<div className="font-mono bg-gray-950 text-gray-300 p-4 shadow-lg rounded-lg max-w-4xl mx-auto border border-gray-600">
			{/* --- Personal Info Section --- */}
			{personalInfo && (
				<div className="text-center mb-4 text-md pb-6 border-gray-700">
					{/* Lighter text for main headings */}
					{personalInfo.name && (
						<h1 className="text-3xl font-bold mb-2 text-white">{personalInfo.name}</h1>
					)}
					{/* Slightly lighter text for subtitle */}
					{personalInfo.title && (
						<h2 className="text-xl text-gray-400 mb-4">{personalInfo.title}</h2>
					)}
					<div className="grid grid-cols-3 gap-1 text-left px-2">
						{renderContactDetail('Email', personalInfo.email, 'mailto:')}
						{renderContactDetail('Phone', personalInfo.phone, 'tel:')}
						{renderContactDetail('Location', personalInfo.location)}
						{renderContactDetail('Website', personalInfo.website)}
						{renderContactDetail('LinkedIn', personalInfo.linkedin)}
						{renderContactDetail('GitHub', personalInfo.github)}
					</div>
				</div>
			)}

			{/* --- Summary Section --- */}
			{summary && (
				<div className="mb-8">
					{/* Lighter text for section titles */}
					<h3 className="text-xl font-semibold border-b border-gray-700 pb-2 mb-3 text-gray-100">
						Summary
					</h3>
					{/* Base text color for paragraph */}
					<p className="text-sm leading-relaxed">{summary}</p>
				</div>
			)}

			{/* --- Work Experience Section --- */}
			{workExperience && workExperience.length > 0 && (
				<div className="mb-8">
					<h3 className="text-xl font-semibold border-b border-gray-700 pb-2 mb-4 text-gray-100">
						Work Experience
					</h3>
					{workExperience.map((exp) => (
						<div key={exp.id} className="mb-5 pl-4 border-l-2 border-blue-500">
							{/* Lighter text for job titles */}
							{exp.title && (
								<h4 className="text-lg font-semibold text-gray-100">{exp.title}</h4>
							)}
							{/* Adjusted gray for company/location */}
							{exp.company && (
								<p className="text-md font-medium text-gray-400">
									{exp.company} {exp.location && `| ${exp.location}`}
								</p>
							)}
							{/* Adjusted gray for dates */}
							{exp.years && <p className="text-sm text-gray-500 mb-2">{exp.years}</p>}
							{exp.description && exp.description.length > 0 && (
								// Base text color for list items
								<ul className="list-disc list-outside ml-5 text-sm space-y-1">
									{exp.description.map((desc, index) => (
										<li key={index}>{desc}</li>
									))}
								</ul>
							)}
						</div>
					))}
				</div>
			)}

			{/* --- Education Section --- */}
			{education && education.length > 0 && (
				<div className="mb-8">
					<h3 className="text-xl font-semibold border-b border-gray-700 pb-2 mb-4 text-gray-100">
						Education
					</h3>
					{education.map((edu) => (
						<div key={edu.id} className="mb-5 pl-4 border-l-2 border-green-500">
							{/* Lighter text for institution */}
							{edu.institution && (
								<h4 className="text-lg font-semibold text-gray-100">
									{edu.institution}
								</h4>
							)}
							{/* Adjusted gray for degree */}
							{edu.degree && (
								<p className="text-md font-medium text-gray-400">{edu.degree}</p>
							)}
							{/* Adjusted gray for dates */}
							{edu.years && <p className="text-sm text-gray-500 mb-2">{edu.years}</p>}
							{/* Base text color for description */}
							{edu.description && <p className="text-sm">{edu.description}</p>}
						</div>
					))}
				</div>
			)}

			{/* --- Personal Projects Section --- */}
			{personalProjects && personalProjects.length > 0 && (
				<div className="mb-8">
					<h3 className="text-xl font-semibold border-b border-gray-700 pb-2 mb-4 text-gray-100">
						Personal Projects
					</h3>
					{personalProjects.map((project) => (
						<div key={project.id} className="mb-5 pl-4 border-l-2 border-purple-500">
							{project.name && (
								<h4 className="text-lg font-semibold text-gray-100">{project.name}</h4>
							)}
							{project.role && (
								<p className="text-md font-medium text-gray-400">{project.role}</p>
							)}
							{project.years && <p className="text-sm text-gray-500 mb-2">{project.years}</p>}
							{project.description && project.description.length > 0 && (
								<ul className="list-disc list-outside ml-5 text-sm space-y-1">
									{project.description.map((desc, index) => (
										<li key={index}>{desc}</li>
									))}
								</ul>
							)}
						</div>
					))}
				</div>
			)}

			{/* --- Additional Section --- */}
			{additional && (
				(() => {
					if (!additional) return null;
					const { technicalSkills = [], languages = [], certificationsTraining = [], awards = [] } = additional;
					const hasContent =
						technicalSkills.length > 0 ||
						languages.length > 0 ||
						certificationsTraining.length > 0 ||
						awards.length > 0;
					if (!hasContent) return null;
					return (
						<div>
							<h3 className="text-xl font-semibold border-b border-gray-700 pb-2 mb-3 text-gray-100">
								Additional
							</h3>
							<div className="grid gap-4 md:grid-cols-2">
								{technicalSkills.length > 0 && (
									<div>
										<h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-1">
											Technical Skills
										</h4>
										<ul className="text-sm text-gray-300 list-disc ml-5 space-y-1">
											{technicalSkills.map((skill, index) => (
												<li key={index}>{skill}</li>
											))}
										</ul>
									</div>
								)}
								{languages.length > 0 && (
									<div>
										<h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-1">
											Languages
										</h4>
										<ul className="text-sm text-gray-300 list-disc ml-5 space-y-1">
											{languages.map((language, index) => (
												<li key={index}>{language}</li>
											))}
										</ul>
									</div>
								)}
								{certificationsTraining.length > 0 && (
									<div>
										<h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-1">
											Certifications & Training
										</h4>
										<ul className="text-sm text-gray-300 list-disc ml-5 space-y-1">
											{certificationsTraining.map((item, index) => (
												<li key={index}>{item}</li>
											))}
										</ul>
									</div>
								)}
								{awards.length > 0 && (
									<div>
										<h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-1">
											Awards
										</h4>
										<ul className="text-sm text-gray-300 list-disc ml-5 space-y-1">
											{awards.map((award, index) => (
												<li key={index}>{award}</li>
											))}
										</ul>
									</div>
								)}
							</div>
						</div>
					);
				})()
			)}

			{/* --- GitHub Profile Section --- */}
			{githubProfile && githubProfile.username && (
				<div className="mb-8">
					<h3 className="text-xl font-semibold border-b border-gray-700 pb-2 mb-4 text-gray-100">
						GitHub Profile
					</h3>
					<div className="pl-4 border-l-2 border-orange-500">
						<div className="flex items-center gap-2 mb-3">
							<svg className="w-6 h-6 text-gray-300" fill="currentColor" viewBox="0 0 24 24">
								<path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
							</svg>
							<a
								href={githubProfile.profileUrl}
								target="_blank"
								rel="noopener noreferrer"
								className="text-lg font-semibold text-blue-400 hover:underline"
							>
								@{githubProfile.username}
							</a>
						</div>

						{/* GitHub Stats */}
						<div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
							{githubProfile.totalRepos !== undefined && (
								<div className="bg-gray-900/50 p-3 rounded-md">
									<p className="text-xs text-gray-500">Repositories</p>
									<p className="text-lg font-bold text-gray-100">{githubProfile.totalRepos}</p>
								</div>
							)}
							{githubProfile.totalStars !== undefined && (
								<div className="bg-gray-900/50 p-3 rounded-md">
									<p className="text-xs text-gray-500">Total Stars</p>
									<p className="text-lg font-bold text-yellow-400">{githubProfile.totalStars}</p>
								</div>
							)}
							{githubProfile.followers !== undefined && (
								<div className="bg-gray-900/50 p-3 rounded-md">
									<p className="text-xs text-gray-500">Followers</p>
									<p className="text-lg font-bold text-gray-100">{githubProfile.followers}</p>
								</div>
							)}
							{githubProfile.recentContributions !== undefined && (
								<div className="bg-gray-900/50 p-3 rounded-md">
									<p className="text-xs text-gray-500">Recent Commits</p>
									<p className="text-lg font-bold text-green-400">{githubProfile.recentContributions}</p>
								</div>
							)}
						</div>

						{/* Top Languages */}
						{githubProfile.topLanguages && githubProfile.topLanguages.length > 0 && (
							<div className="mb-4">
								<h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-2">
									Top Languages
								</h4>
								<div className="flex flex-wrap gap-2">
									{githubProfile.topLanguages.map((lang, index) => (
										<span
											key={index}
											className="px-3 py-1 text-xs font-medium bg-blue-900/30 text-blue-300 rounded-full border border-blue-700/50"
										>
											{lang}
										</span>
									))}
								</div>
							</div>
						)}

						{/* Top Repositories */}
						{githubProfile.topRepositories && githubProfile.topRepositories.length > 0 && (
							<div>
								<h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-2">
									Notable Repositories
								</h4>
								<div className="space-y-3">
									{githubProfile.topRepositories.map((repo, index) => (
										<div key={index} className="bg-gray-900/50 p-3 rounded-md">
											<div className="flex items-start justify-between gap-2">
												<a
													href={repo.url}
													target="_blank"
													rel="noopener noreferrer"
													className="text-sm font-semibold text-blue-400 hover:underline"
												>
													{repo.name}
												</a>
												<div className="flex items-center gap-2 text-xs text-gray-500">
													{repo.language && (
														<span className="px-2 py-0.5 bg-gray-800 rounded">
															{repo.language}
														</span>
													)}
													<span className="flex items-center gap-1">
														<svg className="w-3 h-3 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
															<path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
														</svg>
														{repo.stars}
													</span>
												</div>
											</div>
											{repo.description && (
												<p className="text-xs text-gray-400 mt-1">{repo.description}</p>
											)}
										</div>
									))}
								</div>
							</div>
						)}
					</div>
				</div>
			)}
		</div>
	);
};

export default Resume;
