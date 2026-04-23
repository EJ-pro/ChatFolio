# ChatFolio Backend Documentation

The ChatFolio backend is built on FastAPI and provides GitHub repository analysis, dependency graph construction, and a RAG (Retrieval-Augmented Generation)-based AI chatbot.

## 📂 Directory Structure

```text
backend/
├── main.py                # System entry point and API endpoint definitions
├── api/
│   └── auth.py            # GitHub OAuth and JWT authentication logic
├── core/
│   ├── parser/            # Code collection and parsing
│   │   ├── github_fetcher.py   # GitHub API integration (file streaming and metadata extraction)
│   │   └── kotlin_parser.py    # Kotlin code analysis (class/function/dependency extraction)
│   ├── graph/             # Architecture analysis foundation
│   │   └── graph_builder.py    # Build dependency graph from analyzed data
│   └── rag/               # AI and chatbot engine
│       └── engine.py           # ChatFolioEngine (RAG logic, Mermaid generation, README generation)
├── database/              # Data persistence layer
│   ├── database.py        # SQLAlchemy configuration and DB connection session management
│   └── models.py          # DB schema definitions (User, Project, ChatSession, etc.)
├── models/
│   └── schemas.py         # Pydantic-based API request/response schemas
└── requirements.txt       # Dependency package list
```

---

## 🛠 Key File Descriptions

### 1. `main.py`
The orchestrator of the entire system.
- **`/analyze`**: Accepts a repository URL, collects files, builds a graph, and performs analysis. Sends real-time logs to the frontend via `StreamingResponse`.
- **`/chat`**: Generates answers to user questions based on the analyzed codebase and graph information.
- **`/generate/*`**: Requests generation of Mermaid architecture diagrams or README.md.

### 2. `core/parser/github_fetcher.py` (`GitHubFetcher`)
- Collects source code from a specific repository using the GitHub API.
- Processes files in a streaming fashion using a **Generator** instead of loading everything into memory at once, ensuring memory efficiency for large-scale project analysis.

### 3. `core/parser/kotlin_parser.py`
- Tracks `import`, `class`, and `function` keywords within code to identify inter-file relationships.
- Currently specialized for Kotlin, but designed to be extensible to other languages.

### 4. `core/rag/engine.py` (`ChatFolioEngine`)
The core brain of the project.
- **RAG (Search)**:
    1. **Vector Search**: Searches `InMemoryVectorStore` for code snippets semantically similar to the user's question.
    2. **Graph Search**: Traverses the dependency graph of retrieved key files to additionally gather upstream/downstream context of files that reference or are referenced by them.
- **Prompting**: Instructs the LLM (Groq/OpenAI) to generate a professional answer based on the collected "code snippets + graph information".
- **Utility**: Uses the LLM to convert complex code into a structured Mermaid diagram or a high-quality README.

### 5. `database/models.py`
- **User**: User information and GitHub token management.
- **Project**: Analyzed repository information, file content, and graph data (JSON) storage.
- **ChatSession/ChatMessage**: Stores conversation history and referenced source code information (Sources).

---

## 🔄 Key Workflows

### Analysis Process
1. User enters a GitHub URL.
2. `GitHubFetcher` checks the latest commit and starts collecting files.
3. `kotlin_parser` extracts metadata for each collected file.
4. `DependencyGraphBuilder` completes the inter-file connection network (Graph).
5. All data is saved to DB and an analysis completion response is returned.

### Chat Process
1. User enters a question ("Where is the login logic in this project?").
2. The system performs a **vector similarity search** on the question's keywords → finds the most relevant code (e.g., `AuthService.kt`).
3. **Upstream/downstream dependencies** of the retrieved file are explored in the graph → linked files (e.g., `UserRepository.kt`, `LoginController.kt`) are added as context.
4. The LLM aggregates all information and generates an answer such as "The login logic is defined in AuthService.kt and references UserRepository.kt..."

---

## 🚀 Chatbot Implementation Guide (Reference)
To customize the chatbot feature, you will primarily modify `backend/core/rag/engine.py`.
- To change how questions are answered, modify the prompt inside the `ask()` method.
- To improve search performance, tune the chunking strategy in `_prepare_vector_db()` or the search logic.
