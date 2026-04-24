# User Flow (유저 플로우)

## 1. Main Journey

```mermaid
graph TD
    A[Start: Landing Page] --> B{Logged In?}
    B -- No --> C[Login: GitHub/Google]
    C --> D[Analysis Dashboard]
    B -- Yes --> D
    
    D --> E[Enter GitHub Repo URL]
    E --> F[Select AI Tier: Standard/Premium]
    F --> G[Run Analysis Pipeline]
    
    subgraph Analysis_Pipeline
        G1[Collection] --> G2[Parsing]
        G2 --> G3[Vectorize]
        G3 --> G4[Storage]
        G4 --> G5[Generation]
        G5 --> G6[Review]
    end
    
    G6 --> H[Analysis Complete: View README/Architecture]
    H --> I[Open Chat Interface]
    I --> J[Ask Questions about Code]
    J --> K[AI Response with Source Trace]
    
    H --> L[MyPage: View History]
    L --> M[Upgrade to Pro]
    M --> D
```

## 2. Subscription Flow
1. User clicks "Upgrade to Pro" in Header.
2. Confirmation Modal appears.
3. User confirms (Mock Payment).
4. Tier updated to 'pro' in DB.
5. All models (Groq/OpenAI) unlocked.
