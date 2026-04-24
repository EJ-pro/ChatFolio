# API Specification (API 명세서)

## 1. Authentication (Auth)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/auth/github/login` | Redirect to GitHub OAuth login. |
| GET | `/auth/github/callback` | GitHub OAuth callback handler. |
| GET | `/auth/google/login` | Redirect to Google OAuth login. |
| GET | `/auth/google/callback` | Google OAuth callback handler. |
| GET | `/auth/me` | Get current logged-in user info (Profile, Tier). |
| POST | `/auth/profile` | Update user profile (Country, Job). |
| POST | `/auth/upgrade` | Upgrade user tier to 'pro'. |

## 2. Analysis & Projects
| Method | Endpoint | Description |
|---|---|---|
| POST | `/analyze` | Start repository analysis (returns StreamingResponse for logs). |
| GET | `/projects` | List all projects analyzed by the user. |
| GET | `/projects/{project_id}` | Get detailed project data (Graph, Mermaid, Stats). |
| DELETE | `/projects/{project_id}` | Delete project data. |
| POST | `/projects/check-update` | Check if repo has new commits since last analysis. |

## 3. Chat & AI
| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat/session/new` | Initialize a new chat session for a project. |
| POST | `/chat` | Send a query to AI and get a context-aware response. |
| GET | `/chat/sessions` | List active chat sessions. |
| GET | `/chat/history/{session_id}` | Get message history for a specific session. |
| DELETE | `/chat/session/{session_id}` | Delete/Hide a chat session. |

## 4. Documentation
| Method | Endpoint | Description |
|---|---|---|
| POST | `/generate-readme` | Manually trigger a README generation with specific settings. |
| GET | `/readmes/{project_id}` | Get history of generated readmes for a project. |
| POST | `/analyze-architecture` | Generate a deep architecture analysis report. |

## 5. Metadata & Stats
| Method | Endpoint | Description |
|---|---|---|
| GET | `/dashboard/stats` | Get usage statistics (Total tokens, projects, etc.). |
| GET | `/inquiries` | List user support inquiries. |
