import { useState, useEffect } from "react";

const steps = [
  {
    id: 1,
    icon: "⌨️",
    label: "URL 입력",
    sublabel: "/analyze API Endpoint",
    file: "main.py",
    desc: "사용자가 GitHub Repository URL 입력",
    color: "#7DF9C0",
    detail: "프론트엔드에서 GitHub Repository URL을 입력받아 /analyze 엔드포인트로 요청을 전달합니다.",
  },
  {
    id: 2,
    icon: "🐙",
    label: "프로젝트 전체 수집",
    sublabel: "GitHub API · Stream 다운로드",
    file: "github_fetcher.py",
    desc: "GitHubFetcher — 최신 커밋 확인 후 타겟 확장자 파일만 Generator로 스트리밍",
    color: "#60C6FF",
    detail: ".py .js .kt 등 사전 정의된 확장자만 필터링. Generator로 파일 단위 스트리밍하여 메모리 최적화.",
  },
  {
    id: 3,
    icon: "🔀",
    label: "확장자 라우팅",
    sublabel: "Parser Factory",
    file: "factory.py",
    desc: "get_parser_result — 확장자(ext) 확인 후 언어별 파서로 위임",
    color: "#FFD166",
    detail: "파일 확장자를 분석해 적합한 언어별 파서로 처리를 라우팅합니다.",
  },
  {
    id: 4,
    icon: "🔬",
    label: "언어별 AST 파싱",
    sublabel: "코드 메타데이터 추출",
    file: "parsers/",
    desc: "Python · JS/TS · C/C++ · Java · Kotlin · Generic",
    color: "#FF6B9D",
    isMulti: true,
    detail: null,
    parsers: [
      { lang: "Python", file: "ts_python.py", tags: ["Tree-sitter", "Docstring", "Imports"] },
      { lang: "JS/TS/JSX", file: "ts_javascript.py", tags: ["React", "Hooks", "ES6+"] },
      { lang: "Java", file: "ts_java.py", tags: ["Package", "Classes", "Annotations"] },
      { lang: "Kotlin", file: "ts_kotlin.py", tags: ["DSL", "Coroutines", "Nullable"] },
      { lang: "Go", file: "ts_go.py", tags: ["Structs", "Interfaces", "Gopath"] },
      { lang: "C/C++", file: "ts_cpp.py", tags: ["Namespace", "Templates", "Macros"] },
      { lang: "Rust", file: "ts_rust.py", tags: ["Ownership", "Traits", "Macros"] },
      { lang: "C#", file: "ts_csharp.py", tags: ["LINQ", "Attributes", "Namespaces"] },
      { lang: "Swift", file: "ts_swift.py", tags: ["Protocols", "Extensions", "SwiftUI"] },
      { lang: "Dart", file: "ts_dart.py", tags: ["Flutter", "Mixins", "AOT"] },
      { lang: "Ruby", file: "ts_ruby.py", tags: ["Gems", "Modules", "Blocks"] },
      { lang: "PHP", file: "ts_php.py", tags: ["Namespaces", "Traits", "Composer"] },
      { lang: "Config", file: "config/", tags: ["JSON", "YAML", "XML", "Gradle", "SQL"], highlight: true },
    ],
  },
  {
    id: 5,
    icon: "🕸️",
    label: "의존성 그래프 구축",
    sublabel: "NetworkX",
    file: "graph_builder.py",
    desc: "DependencyGraphBuilder — all_meta 통합 후 Node·Edge 의존성 네트워크 생성",
    color: "#A78BFA",
    detail: "각 파서의 metadata를 통합하여 파일 간 의존 관계를 NetworkX 그래프(Node/Edge)로 구성합니다.",
  },
  {
    id: 6,
    icon: "🧠",
    label: "저장 & RAG 엔진 구동",
    sublabel: "PostgreSQL · ChatFolio Engine",
    file: "engine.py",
    desc: "PostgreSQL 캐싱 → ChatFolioEngine RAG 적용 → LLM 채팅 모드 완성",
    color: "#FB923C",
    detail: "파일 라인수·키워드·그래프를 PostgreSQL에 저장 후, ChatFolioEngine에 주입하여 RAG 기반 LLM 채팅 인터페이스를 완성합니다.",
  },
];

const parserColors = {
  "Python": "#3B82F6",
  "JS/TS/JSX": "#F59E0B",
  "C/C++": "#10B981",
  "Java": "#EF4444",
  "Kotlin": "#8B5CF6",
  "기타/Swift*": "#6B7280",
};

export default function ChatFolioPipeline() {
  const [active, setActive] = useState(null);
  const [revealed, setRevealed] = useState([]);

  useEffect(() => {
    steps.forEach((s, i) => {
      setTimeout(() => {
        setRevealed(prev => [...prev, s.id]);
      }, i * 160);
    });
  }, []);

  const activeStep = steps.find(s => s.id === active);

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0A0D14",
      fontFamily: "'DM Mono', 'Fira Code', monospace",
      padding: "40px 20px",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
    }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 48 }}>
        <div style={{ fontSize: 11, letterSpacing: "0.3em", color: "#4B5563", textTransform: "uppercase", marginBottom: 8 }}>
          System Architecture
        </div>
        <h1 style={{
          fontSize: "clamp(22px, 4vw, 36px)",
          fontFamily: "'Space Grotesk', 'DM Mono', sans-serif",
          fontWeight: 700,
          color: "#F9FAFB",
          margin: 0,
          letterSpacing: "-0.02em",
        }}>
          ChatFolio <span style={{ color: "#7DF9C0" }}>Pipeline</span>
        </h1>
        <div style={{ fontSize: 12, color: "#6B7280", marginTop: 8 }}>
          Analysis Flow · AST Parsing → RAG Engine
        </div>
      </div>

      {/* Pipeline */}
      <div style={{ width: "100%", maxWidth: 680, position: "relative" }}>
        {steps.map((step, idx) => {
          const isVisible = revealed.includes(step.id);
          const isActive = active === step.id;

          return (
            <div key={step.id} style={{ position: "relative" }}>
              {/* Connector line */}
              {idx < steps.length - 1 && (
                <div style={{
                  position: "absolute",
                  left: "50%",
                  bottom: -1,
                  transform: "translateX(-50%)",
                  width: 2,
                  height: 32,
                  background: `linear-gradient(to bottom, ${step.color}55, ${steps[idx + 1].color}55)`,
                  zIndex: 0,
                }} />
              )}

              {/* Card */}
              <div
                onClick={() => setActive(isActive ? null : step.id)}
                style={{
                  position: "relative",
                  zIndex: 1,
                  marginBottom: 32,
                  background: isActive
                    ? `linear-gradient(135deg, #1A1D2E, #12151F)`
                    : "#111420",
                  border: `1px solid ${isActive ? step.color : "#1F2437"}`,
                  borderRadius: 16,
                  padding: "20px 24px",
                  cursor: "pointer",
                  transition: "all 0.25s ease",
                  boxShadow: isActive
                    ? `0 0 32px ${step.color}22, 0 4px 24px #00000060`
                    : "0 2px 12px #00000040",
                  opacity: isVisible ? 1 : 0,
                  transform: isVisible ? "translateY(0)" : "translateY(12px)",
                }}
              >
                {/* Step number badge */}
                <div style={{
                  position: "absolute",
                  top: -1,
                  left: 24,
                  transform: "translateY(-50%)",
                  background: step.color,
                  color: "#0A0D14",
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  padding: "2px 10px",
                  borderRadius: 20,
                }}>
                  STEP {step.id}
                </div>

                {/* Main row */}
                <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 4 }}>
                  <div style={{
                    fontSize: 28,
                    width: 52,
                    height: 52,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: `${step.color}18`,
                    borderRadius: 12,
                    flexShrink: 0,
                    border: `1px solid ${step.color}30`,
                  }}>
                    {step.icon}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                      <span style={{ fontSize: 16, fontWeight: 700, color: "#F1F5F9", letterSpacing: "-0.01em" }}>
                        {step.label}
                      </span>
                      <span style={{
                        fontSize: 10,
                        color: step.color,
                        background: `${step.color}15`,
                        padding: "2px 8px",
                        borderRadius: 6,
                        fontWeight: 600,
                        letterSpacing: "0.05em",
                      }}>
                        {step.sublabel}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: "#94A3B8", marginTop: 4 }}>
                      {step.desc}
                    </div>
                    <div style={{
                      display: "inline-block",
                      marginTop: 6,
                      fontSize: 10,
                      color: "#4B5563",
                      background: "#1A1D2E",
                      padding: "2px 8px",
                      borderRadius: 4,
                      border: "1px solid #252A3D",
                    }}>
                      📄 {step.file}
                    </div>
                  </div>

                  <div style={{
                    color: isActive ? step.color : "#374151",
                    fontSize: 18,
                    transition: "transform 0.2s",
                    transform: isActive ? "rotate(180deg)" : "rotate(0deg)",
                    flexShrink: 0,
                  }}>
                    ▾
                  </div>
                </div>

                {/* Expanded detail */}
                {isActive && (
                  <div style={{
                    marginTop: 16,
                    paddingTop: 16,
                    borderTop: `1px solid ${step.color}25`,
                  }}>
                    {step.parsers ? (
                      <div>
                        <div style={{ fontSize: 11, color: "#6B7280", marginBottom: 12, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                          언어별 파서 라우팅
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 10 }}>
                          {step.parsers.map(p => (
                            <div key={p.lang} style={{
                              background: "#0A0D14",
                              border: `1px solid ${parserColors[p.lang]}${p.dim ? "44" : "55"}`,
                              borderRadius: 10,
                              padding: "10px 12px",
                              opacity: p.dim ? 0.5 : 1,
                            }}>
                              <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                                <div style={{
                                  width: 8, height: 8, borderRadius: "50%",
                                  background: parserColors[p.lang],
                                  flexShrink: 0,
                                }} />
                                <span style={{ fontSize: 12, fontWeight: 700, color: "#E2E8F0" }}>{p.lang}</span>
                              </div>
                              <div style={{ fontSize: 9, color: "#4B5563", marginBottom: 6 }}>📄 {p.file}</div>
                              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                                {p.tags.map(t => (
                                  <span key={t} style={{
                                    fontSize: 9,
                                    background: `${parserColors[p.lang]}18`,
                                    color: parserColors[p.lang],
                                    padding: "1px 6px",
                                    borderRadius: 4,
                                  }}>{t}</span>
                                ))}
                              </div>
                              {p.dim && <div style={{ fontSize: 9, color: "#6B7280", marginTop: 6 }}>* 추후 개발 예정</div>}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <p style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.7, margin: 0 }}>
                        {step.detail}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Final output badge */}
        <div style={{
          textAlign: "center",
          marginTop: 8,
          padding: "16px 24px",
          background: "linear-gradient(135deg, #7DF9C015, #FB923C15)",
          border: "1px solid #7DF9C030",
          borderRadius: 12,
        }}>
          <div style={{ fontSize: 11, color: "#7DF9C0", letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 4 }}>
            Output
          </div>
          <div style={{ fontSize: 14, color: "#F1F5F9", fontWeight: 600 }}>
            🎯 RAG 기반 LLM 채팅 인터페이스 완성
          </div>
          <div style={{ fontSize: 11, color: "#6B7280", marginTop: 4 }}>
            AST Parsing → Dependency Graph → Vector DB → ChatFolio Engine
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ marginTop: 40, fontSize: 10, color: "#2D3348", letterSpacing: "0.1em" }}>
        CHATFOLIO · PIPELINE ARCHITECTURE · 2025
      </div>
    </div>
  );
}