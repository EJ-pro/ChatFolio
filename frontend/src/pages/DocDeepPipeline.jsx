import React, { useState } from "react";
import { 
  Database, Github, Braces, Layers, Link2, 
  Cpu, FileCode2, Code, ArrowRight, Share2, Info, CheckCircle2,
  Lock, Search, CloudDownload, Terminal, BarChart3, Binary, RefreshCw
} from "lucide-react";

export default function DocDeepPipeline() {
  const [activeNode, setActiveNode] = useState(0);
  const [viewType, setViewType] = useState("pipeline"); // "pipeline" or "agent"

  const steps = [
    {
      id: "auth",
      title: "Analysis Request & Auth",
      icon: <Lock size={22} />,
      color: "#3b82f6",
      file: "main.py > /analyze",
      desc: "API endpoint entry and security validation",
      tech: ["FastAPI", "OAuth2"],
      details: {
        payload: { user_id: "EJ-pro", repo_url: "..." },
        actions: [
          "Validate user's GitHub Personal Access Token (PAT)",
          "Normalize analysis request parameters (URL, Branch)",
          "Check Rate Limit and API access permission status"
        ]
      }
    },
    {
      id: "cache",
      title: "Code Update Check",
      icon: <Search size={22} />,
      color: "#0ea5e9",
      file: "main.py",
      desc: "Compare code update history and decide caching strategy",
      tech: ["PostgreSQL", "SHA-256"],
      details: {
        payload: { last_commit: "a1b2c3d...", is_updated: true },
        actions: [
          "Real-time latest commit hash (SHA) check via GitHub API",
          "Determine whether new analysis is needed by comparing with existing database",
          "Invalidate existing data when Force Update is requested"
        ]
      }
    },
    {
      id: "scan",
      title: "Target Scanning",
      icon: <Binary size={22} />,
      color: "#22d3ee",
      file: "github_fetcher.py",
      desc: "Understand and filter project structure",
      tech: ["Recursive Tree", "Globs"],
      details: {
        payload: { total_files: 142, targets: 89 },
        actions: [
          "Recursive directory traversal and full file tree construction",
          "Select analysis targets based on target extensions (code, config, docs)",
          "Exclude .gitignore and unnecessary binary files from analysis"
        ]
      }
    },
    {
      id: "fetch",
      title: "Streaming Data Collection",
      icon: <CloudDownload size={22} />,
      color: "#2dd4bf",
      file: "github_fetcher.py",
      desc: "Memory-optimized file loading",
      tech: ["Python Generator", "Streaming"],
      details: {
        payload: "yield (path, content)",
        actions: [
          "Sequential loading of large volumes of files using Generator pattern",
          "Asynchronous Base64 payload decoding per file",
          "Prevent Out-of-Memory (OOM) when loading large repositories"
        ]
      }
    },
    {
      id: "factory",
      title: "Parser Factory Routing",
      icon: <Terminal size={22} />,
      color: "#10b981",
      file: "core/parser/factory.py",
      desc: "Assign language-optimized analyzers",
      tech: ["Factory Pattern"],
      details: {
        payload: "get_parser_result(ext)",
        actions: [
          "Match language-specific parsers after analyzing input file extensions",
          "Support concurrent analysis of multi-language (Polyglot) projects",
          "Fall back to default metadata extractor for unknown formats"
        ]
      }
    },
    {
      id: "parse",
      title: "Deep AST Parsing",
      icon: <FileCode2 size={22} />,
      color: "#84cc16",
      file: "core/parser/lang/*.py",
      desc: "Structure extraction using native AST and Regex engine",
      tech: ["Native AST (Python)", "Regex Engine (JS/JAVA/KT)"],
      details: {
        payload: { classes: ["Auth"], functions: ["login"] },
        actions: [
          "High-speed metadata extraction using Python's built-in ast module and per-language regex engines",
          "Accurate identification and normalization of classes, functions, namespaces, and import statements",
          "Remove OS dependencies and ensure runtime stability in Docker container environments"
        ]
      }
    },
    {
      id: "persistence",
      title: "Persistent Data Storage",
      icon: <Database size={22} />,
      color: "#eab308",
      file: "database/models.py",
      desc: "Normalized DB storage of analysis data",
      tech: ["SQLAlchemy", "PostgreSQL"],
      details: {
        payload: { status: "commit_success", rows: 124 },
        actions: [
          "Save parsed data and original code in a PostgreSQL transaction",
          "Store per-file line count, keywords, and metadata as JSON fields",
          "Update project record and record analysis timestamp"
        ]
      }
    },
    {
      id: "graph",
      title: "Dependency Network Construction",
      icon: <Share2 size={22} />,
      color: "#f97316",
      file: "core/graph/graph_builder.py",
      desc: "Establish cross-reference relationships using Resolver Factory",
      tech: ["Resolver Factory", "Language Resolvers", "NetworkX"],
      details: {
        payload: "nx.DiGraph(nodes=89, edges=234)",
        actions: [
          "Assign language-specific custom resolvers (PythonResolver, JSResolver, etc.) via ResolverFactory",
          "Normalize and map import statement dot notation and relative paths to actual filesystem paths",
          "Build global module dependency network and topology using NetworkX DiGraph"
        ]
      }
    },
    {
      id: "metrics",
      title: "Network Statistics Analysis",
      icon: <BarChart3 size={22} />,
      color: "#ef4444",
      file: "main.py / graph_builder",
      desc: "Process data for architecture visualization",
      tech: ["Graph Algorithm", "JSON"],
      details: {
        payload: { degree_dict: { "main.py": 12 } },
        actions: [
          "Identify central files by calculating per-node connection degree",
          "Convert to JSON for frontend visualization (D3.js/3D-Force)",
          "Generate project architecture topology data"
        ]
      }
    },
    {
      id: "engine",
      title: "RAG Engine & Session Activation",
      icon: <Cpu size={22} />,
      color: "#ec4899",
      file: "engine.py",
      desc: "Prepare LLM conversation and load engine",
      tech: ["LangChain", "Vector Store"],
      details: {
        payload: "ChatFolioEngine.ask()_ready",
        actions: [
          "Load all analyzed data into the ChatFolioEngine context",
          "Configure vector embedding and Retrieval-Augmented Generation (RAG) pipeline",
          "Open a chat session for user interaction"
        ]
      }
    }
  ];

  const agentSteps = [
    {
      id: "analyzer",
      title: "🔍 Analyzer Agent",
      desc: "Scan project structure and business logic",
      detail: "Generates a summary report by identifying the overall tech stack, core directories, DB schema, etc., using the GitHub URL entered by the user and RAG (Retrieval-Augmented Generation).",
      tip: "This is the stage that establishes the project's 'identity', such as Spring Boot, React, FastAPI, etc."
    },
    {
      id: "router",
      title: "🔀 Router",
      desc: "Dynamic branching based on analysis results",
      detail: "Hands off work to the appropriate Draft Writer based on the analysis report archetype (BE/FE/ML, etc.). Dynamically selects a prompt template optimized for the tech stack.",
      tip: "Shifts strategy to API spec-centric for backends, and UI/UX getting-started guides for frontends."
    },
    {
      id: "writer",
      title: "✍️ Draft Writer Agent",
      desc: "Write draft file in Markdown",
      detail: "Writes a README.md draft by combining the router's strategy and the analyzer's report. Shapes installation instructions, tech stack badges, key features, folder structure, and more.",
      tip: "Maximizes Markdown readability to deliver a professional feel."
    },
    {
      id: "reviewer",
      title: "🕵️ Reviewer Agent (Critic)",
      desc: "Markdown quality review and loop control",
      detail: "Rigorously reviews the writer's output. Checks whether execution commands are accurate and required sections are present, and sends feedback back to the writer if anything is lacking.",
      tip: "Guarantees a final output that requires no manual corrections through LangGraph's core 'Loop' mechanism."
    }
  ];

  const active = steps[activeNode];

  return (
    <div className="min-h-screen bg-[#030712] text-[#e2e8f0] p-8 flex flex-col items-center" style={{ fontFamily: "Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}>
      {/* Header Area */}
      <div className="w-full max-w-6xl mb-12 text-center md:text-left flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-slate-800/50 border border-slate-700 rounded-full text-xs text-emerald-400 font-bold uppercase tracking-widest mb-4">
            <Database size={14} /> Architecture Deep Dive
          </div>
          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-white mb-2 leading-tight">
            Doc<span className="text-emerald-400">DeepPipeline</span>
          </h1>
          <p className="text-slate-400 text-lg">Internal data execution flow and 10-step core pipeline guide</p>
        </div>
        
        <div className="flex flex-col gap-6">
          {/* View Toggle */}
          <div className="flex bg-slate-900/50 p-1 rounded-2xl border border-slate-800 self-center md:self-end">
            <button 
              onClick={() => setViewType("pipeline")}
              className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${viewType === "pipeline" ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/20" : "text-slate-500 hover:text-slate-300"}`}
            >
              Main Pipeline
            </button>
            <button 
              onClick={() => setViewType("agent")}
              className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${viewType === "agent" ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/20" : "text-slate-500 hover:text-slate-300"}`}
            >
              README Agent
            </button>
          </div>

          <div className="flex gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 min-w-[140px] shadow-lg">
              <div className="text-[11px] text-slate-500 mb-1 font-bold tracking-wider uppercase">{viewType === "pipeline" ? "Pipeline Steps" : "Agent Count"}</div>
              <div className="text-2xl font-black text-slate-100">{viewType === "pipeline" ? "10 Steps" : "4 Agents"}</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 min-w-[140px] shadow-lg">
              <div className="text-[11px] text-slate-500 mb-1 font-bold tracking-wider uppercase">Engine Status</div>
              <div className="text-2xl font-black text-emerald-400 animate-pulse">READY</div>
            </div>
          </div>
        </div>
      </div>

      {viewType === "pipeline" ? (
        <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-10">
          
          {/* Left Side: Pipeline Navigation */}
          <div className="lg:col-span-5 relative flex flex-col gap-3">
            <div className="absolute left-7 top-10 bottom-10 w-[2px] bg-slate-800/50 z-0"></div>
            
            {steps.map((step, idx) => (
              <div 
                key={step.id} 
                className="relative z-10 flex gap-5 cursor-pointer group"
                onClick={() => setActiveNode(idx)}
              >
                <div className="flex flex-col items-center mt-1">
                  <div 
                    className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 shadow-xl ${
                      activeNode === idx 
                      ? 'scale-110 ring-4 ring-offset-4 ring-offset-[#030712] ring-opacity-20 border-2' 
                      : 'bg-slate-900/80 border border-slate-800 opacity-50 group-hover:opacity-100 group-hover:bg-slate-800'
                    }`}
                    style={{
                      backgroundColor: activeNode === idx ? `${step.color}20` : '',
                      borderColor: activeNode === idx ? step.color : '',
                      color: activeNode === idx ? step.color : '#64748b',
                      boxShadow: activeNode === idx ? `0 0 30px ${step.color}30` : '',
                      ringColor: activeNode === idx ? step.color : 'transparent'
                    }}
                  >
                    {step.icon}
                  </div>
                  {idx < steps.length - 1 && (
                    <div className={`w-[2px] h-full my-1 transition-colors ${activeNode >= idx ? 'bg-emerald-500/40' : 'bg-slate-800'}`}></div>
                  )}
                </div>
                
                <div className={`flex-1 p-4 rounded-2xl border transition-all duration-300 ${
                  activeNode === idx 
                  ? 'bg-slate-900 border-slate-700 shadow-2xl translate-x-1' 
                  : 'bg-transparent border-transparent opacity-50 group-hover:opacity-100 group-hover:translate-x-1'
                }`}>
                  <div className="text-[11px] font-black tracking-widest mb-1 uppercase" style={{ color: step.color }}>
                    Step 0{idx + 1}
                  </div>
                  <div className={`font-bold text-lg ${activeNode === idx ? 'text-white' : 'text-slate-400'}`}>
                    {step.title}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Right Side: Step Insights */}
          <div className="lg:col-span-7">
            <div className="sticky top-8 bg-slate-900/60 backdrop-blur-2xl border border-slate-800 rounded-[2.5rem] p-10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] relative overflow-hidden h-full min-h-[650px] flex flex-col">
              
              <div 
                className="absolute -top-24 -right-24 w-96 h-96 blur-[120px] rounded-full opacity-30 pointer-events-none transition-colors duration-1000"
                style={{ backgroundColor: active.color }}
              ></div>

              <div className="relative z-10 border-b border-slate-800 pb-8 mb-8">
                <div className="flex items-center gap-5 mb-3">
                  <div className="p-3 rounded-2xl bg-black border border-slate-800 shadow-inner" style={{ color: active.color }}>
                    {active.icon}
                  </div>
                  <div>
                    <h2 className="text-3xl font-black text-white tracking-tight">{active.title}</h2>
                    <p className="text-slate-400 text-base mt-2 font-medium">{active.desc}</p>
                  </div>
                </div>
              </div>

              <div className="relative z-10 flex-1 flex flex-col gap-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="bg-black/40 rounded-2xl p-5 border border-slate-800/80 shadow-md">
                    <div className="text-[11px] text-slate-500 mb-3 tracking-widest font-black uppercase flex items-center gap-2">
                      <Terminal size={14} /> Source File
                    </div>
                    <div className="font-bold text-emerald-400 text-sm font-mono break-all leading-relaxed">
                      {active.file}
                    </div>
                  </div>

                  <div className="bg-black/40 rounded-2xl p-5 border border-slate-800/80 shadow-md">
                    <div className="text-[11px] text-slate-500 mb-3 tracking-widest font-black uppercase flex items-center gap-2">
                      <Layers size={14} /> Core Tech
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {active.tech.map(t => (
                        <span key={t} className="px-3 py-1 bg-slate-800/80 rounded-lg text-[11px] font-bold shadow-sm" style={{ color: active.color }}>
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex-1 bg-black/40 rounded-3xl border border-slate-800/80 p-8 mt-2 flex flex-col shadow-2xl ring-1 ring-white/5">
                  <div className="text-[11px] text-slate-500 mb-6 tracking-widest font-black uppercase flex items-center gap-2">
                    <Info size={16} /> Internal Logic
                  </div>
                  
                  <div className="space-y-5 mb-10">
                    {active.details.actions.map((act, i) => (
                      <div key={i} className="flex items-start gap-4 text-[15px] text-slate-200 leading-relaxed font-medium">
                        <CheckCircle2 size={18} className="mt-1 shrink-0" style={{ color: active.color }} />
                        <span>{act}</span>
                      </div>
                    ))}
                  </div>

                  <div className="mt-auto pt-8 border-t border-slate-800">
                    <div className="text-[11px] text-slate-500 mb-4 tracking-widest font-black uppercase flex items-center justify-between">
                      <span>Data Structure</span>
                      <span className="text-emerald-500/70 bg-emerald-500/10 px-2 py-0.5 rounded text-[9px]">LIVE_INSTANCE</span>
                    </div>
                    <pre className="bg-black/80 border border-slate-800 p-6 rounded-2xl text-[12px] overflow-x-auto text-pink-400 font-mono shadow-inner leading-relaxed custom-scrollbar max-h-[180px]">
                      <code>{JSON.stringify(active.details.payload, null, 2)}</code>
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Agent Workflow View */
        <div className="w-full max-w-6xl space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative">
            {/* Connection Arrows Overlay (Desktop Only) */}
            <div className="hidden lg:block absolute top-[40px] left-[15%] right-[15%] h-[2px] bg-slate-800 z-0"></div>
            
            {agentSteps.map((agent, idx) => (
              <div key={agent.id} className="relative z-10 glass-panel bg-slate-900/40 border border-slate-800 rounded-3xl p-8 hover:border-emerald-500/30 transition-all group">
                <div className="w-16 h-16 rounded-2xl bg-black border border-slate-800 flex items-center justify-center mb-6 text-emerald-400 group-hover:scale-110 transition-transform">
                  <span className="text-2xl">{idx + 1}</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3 tracking-tight">{agent.title}</h3>
                <p className="text-emerald-500/80 text-sm font-bold mb-4">{agent.desc}</p>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">{agent.detail}</p>
                
                <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl">
                  <div className="text-[10px] text-emerald-500 font-black uppercase tracking-widest mb-1 flex items-center gap-1">
                    <Info size={12} /> Insight
                  </div>
                  <p className="text-xs text-slate-300 italic">"{agent.tip}"</p>
                </div>

                {idx === 3 && (
                  <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-4 py-1.5 rounded-full text-[11px] font-black animate-bounce">
                    <RefreshCw size={12} /> CONDITIONAL LOOP BACK TO WRITER
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-20 glass-panel bg-slate-900/60 border border-slate-800 rounded-[2.5rem] p-12 overflow-hidden relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 blur-[80px] rounded-full"></div>
            <div className="relative z-10">
              <h2 className="text-3xl font-black text-white mb-8 tracking-tighter flex items-center gap-3">
                <CheckCircle2 className="text-emerald-500" />
                Final Output
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                <div className="space-y-6">
                  <p className="text-slate-300 text-lg leading-relaxed">
                    A perfect <b>README.md</b>, approved by the Reviewer Agent, is delivered to the user.
                    Experience high-quality documentation that professionally explains the core value and architecture of the project — not just a list of code.
                  </p>
                  <ul className="space-y-3">
                    {["Automatic custom section composition", "Derive core project features", "Accurate installation and execution guide", "Elegant tech stack badge auto-insertion"].map(item => (
                      <li key={item} className="flex items-center gap-3 text-slate-400 text-sm font-medium">
                        <ArrowRight size={14} className="text-emerald-500" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="bg-black/40 rounded-3xl p-8 border border-white/5 font-mono text-[13px] text-pink-400/90 whitespace-pre-wrap leading-relaxed shadow-inner">
                  # 🚀 AwesomeProject{"\n"}
                  &gt; "The ultimate productivity tool for developers"{"\n\n"}
                  ## ✨ Key Features{"\n"}
                  - ⚡ **Real-time Sync**: WebSocket-based...{"\n"}
                  - 🔒 **Secure Auth**: JWT-based OAuth...{"\n\n"}
                  ## 📂 Folder Structure{"\n"}
                  📦 src/{"\n"}
                   ┣ 📂 components{"\n"}
                   ┗ 📂 utils
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
