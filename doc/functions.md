# Functional Specification (기능 정의서)

## 1. Analysis Engine
### F1.1 Repository Fetcher
- Clone public repositories and traverse the file system.
- Filter out unnecessary files (lock files, hidden directories).

### F1.2 Multi-Language Parser
- Extract AST and metadata for multiple languages (Python, JS, TS, Java, Kotlin, etc.).
- Identify dependencies and imports to build a code graph.

### F1.3 Vectorization & RAG
- Chunk source code into meaningful segments.
- Generate embeddings and store them in an in-memory or persistent vector store.

## 2. AI Documentation Generation
### F2.1 Automatic README Generation
- Analyze project archetype (Backend, Frontend, etc.).
- Generate Markdown including title, introduction, tech stack, and installation guides.

### F2.2 Architecture Mapping
- Generate Mermaid.js code based on the internal dependency graph.
- Categorize files into subgraphs (Components, Services, API, etc.).

## 3. Communication (Chat)
### F3.1 Context-Aware Q&A
- Retrieve relevant code snippets based on user queries.
- Multi-turn conversation support with session history.

### F3.2 AI Model Selection
- **Standard (Eco)**: HuggingFace (Mistral/Llama).
- **Standard (Fast)**: Groq (Llama 70B).
- **Premium**: OpenAI (GPT-4o).

## 4. User Features
### F4.1 Personal Dashboard
- View analysis results history.
- Delete or re-analyze existing projects.

### F4.2 Subscription Management
- One-click upgrade to Pro tier.
- 30-day premium access management.

### F4.3 Developer Persona
- Future feature: Analyze coding style to generate a "Developer Persona" or MBTI-like profile.
