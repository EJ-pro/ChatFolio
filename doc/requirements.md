# Requirements Specification (요구사항 명세서)

## 1. Project Overview
- **Project Name**: ChatFolio
- **Goal**: Help developers understand complex GitHub repositories quickly through AI-driven analysis, architecture visualization, and interactive chat.
- **Target Audience**: Developers, Technical Recruiters, Students, and Project Managers.

## 2. Key Requirements

### R1. Repository Analysis
- **R1.1**: Support public GitHub repository analysis via URL.
- **R1.2**: Extract tech stack, file structure, and code dependencies.
- **R1.3**: Generate professional README.md automatically.
- **R1.4**: Visualize project architecture using Mermaid diagrams.

### R2. Interactive Chat (RAG)
- **R2.1**: Provide a chat interface to ask questions about the analyzed codebase.
- **R2.2**: Use Retrieval Augmented Generation (RAG) to provide contextually accurate answers.
- **R2.3**: Show sources (file paths) used for AI responses.
- **R2.4**: Visualize the "Graph Trace" of how AI explored the project dependencies.

### R3. Subscription & Tiering
- **R3.1**: **Free Tier**: Limited to Standard AI (Eco) models.
- **R3.2**: **Pro Tier**: Access to Premium AI (OpenAI) and Fast AI (Groq) models.
- **R3.3**: Tiered access for advanced features like deep architecture analysis.

### R4. User Management
- **R4.1**: Social login support (GitHub/Google).
- **R4.2**: Personal dashboard to view analysis history.
- **R4.3**: Profile management including occupation and country settings.

### R5. Performance & UX
- **R5.1**: Real-time analysis pipeline visualization (7-stage pipeline).
- **R5.2**: Responsive design for desktop and tablet views.
- **R5.3**: Fast response times using high-speed inference engines (Groq).
