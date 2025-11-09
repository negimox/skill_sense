# Skill Sense 🧠

> **AI-Powered Skill Discovery & Job Matching Platform**

SkillSense transforms the Resume-Matcher into an intelligent skill profiling system that:

- 🎯 **Extracts explicit & implicit skills** from resumes using AI embeddings
- 📊 **Calculates confidence scores** with evidence trails
- 🔍 **Matches against job descriptions** and identifies skill gaps
- 📤 **Exports in multiple formats** (JSON, CSV, SAP)
- 🔐 **Protects privacy** with PII masking and audit logs

---

## 🚀 Quick Start

```bash
# Setup and run (one command)
./setup.sh && npm run dev

# Then visit:
# - Dashboard: http://localhost:3000/dashboard
# - Upload resume, then go to /skill-profile/{resume_id}
```

## 📚 Documentation

- **[SKILLSENSE_README.md](./SKILLSENSE_README.md)** - Complete feature documentation
- **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** - Testing scenarios and API examples
- **[AGENTS.md](./AGENTS.md)** - Development guidelines
- **[SETUP.md](./SETUP.md)** - Installation instructions

---

## ✨ Core Features

### Skill Profile Generation

Automatically extract skills from resumes with:

- Pattern-based detection for 30+ common skills
- Context analysis for relevance scoring
- ESCO taxonomy mapping

### Interactive Management

- ✅ Accept suggested skills
- ❌ Reject false positives
- ✏️ Edit skill names
- 🔍 View evidence trails

### Job Matching

- Paste any job description
- Get match percentage (0-100%)
- See which skills you have
- Identify skill gaps
- Receive recommendations

### Export Options

- **JSON**: Full data with evidence
- **CSV**: Spreadsheet-friendly
- **SAP**: Enterprise-compatible with taxonomy IDs

---

## 🏗️ Tech Stack

- **Backend**: FastAPI + Python + SQLAlchemy
- **Frontend**: Next.js + React + TypeScript + Tailwind CSS
- **AI**: Ollama (`gemma3:4b` + `Qwen3-Embedding-0.6B`)
- **Database**: SQLite (async)
- **Standards**: ESCO taxonomy

---

## 📦 What's New in SkillSense

**Backend:**

- ✨ `SkillProfile` & `SkillAuditLog` models
- ✨ `SkillExtractionService` with AI-powered detection
- ✨ `JobMatchingService` using cosine similarity
- ✨ `/api/v1/skills/*` endpoints
- ✨ ESCO taxonomy mapping (30 skills)
- ✨ PII masking utilities

**Frontend:**

- ✨ `/skill-profile/[user_id]` page
- ✨ `SkillCard`, `EvidenceModal`, `JobMatchPanel` components
- ✨ Export controls with format selection
- ✨ Real-time filtering and stats

---

## 🎯 Use Cases

1. **Job Seekers**: Discover hidden skills and match them to jobs
2. **Recruiters**: Quickly assess candidate skill profiles
3. **HR Teams**: Export profiles to SAP or other systems
4. **Career Coaches**: Identify skill gaps and growth areas
5. **Developers**: Showcase portfolio with verified skills

---

## 🤝 Contributing

See [AGENTS.md](./AGENTS.md) for development guidelines.

---

## 📄 License

[Add your license here]

---

**Built with ❤️ using Ollama, FastAPI, and Next.js**
