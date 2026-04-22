from typing import Annotated, TypedDict, List, Dict, Any, Union
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
import json
import traceback
import os

class ReadmeState(TypedDict, total=False):
    project_context: str
    user_inputs: Dict[str, Any]
    archetype: str  # BE, FE, ML, Library 등
    analysis_report: str
    draft: str
    feedback: str
    iteration_count: int
    decision: str
    final_readme: str
    provider: str
    model_name: str

class ReadmeAgent:
    def __init__(self, llm, provider="groq", model_name=None):
        self.llm = llm
        self.provider = provider
        self.model_name = model_name
        self.workflow = self._create_workflow()
        self.log_path = "/app/.backend_error.log" if os.path.exists("/app") else ".backend_error.log"

    def _create_workflow(self):
        workflow = StateGraph(ReadmeState)

        # 1. Analyzer Node
        workflow.add_node("analyzer", self.analyzer_node)
        # 2. Router Node
        workflow.add_node("router", self.router_node)
        # 3. Draft Writer Node
        workflow.add_node("writer", self.writer_node)
        # 4. Reviewer Node
        workflow.add_node("reviewer", self.reviewer_node)

        # 엣지 연결
        workflow.set_entry_point("analyzer")
        workflow.add_edge("analyzer", "router")
        workflow.add_edge("router", "writer")
        workflow.add_edge("writer", "reviewer")

        # 조건부 엣지 (Reviewer -> Writer or END)
        workflow.add_conditional_edges(
            "reviewer",
            self.should_continue,
            {
                "revise": "writer",
                "approve": END
            }
        )

        return workflow.compile()

    def _safe_invoke(self, messages: List[Union[SystemMessage, HumanMessage]]):
        """에러 발생 시 폴백 모델을 시도하는 안전한 호출 메서드"""
        try:
            return self.llm.invoke(messages)
        except Exception as e:
            err_msg = str(e)
            print(f"⚠️ Primary LLM failed: {err_msg[:200]}...")
            
            # Fallback strategy
            fallback_models = []
            if self.provider == "groq":
                # 최신 Groq 모델 명칭 반영
                fallback_models = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant"]
            elif self.provider == "openai":
                fallback_models = ["gpt-4o-mini", "gpt-3.5-turbo"]
            
            for f_model in fallback_models:
                if f_model == self.model_name: continue
                try:
                    print(f"🔄 Trying fallback model: {f_model}")
                    if self.provider == "openai":
                        alt_llm = ChatOpenAI(model=f_model, temperature=0)
                    else:
                        alt_llm = ChatGroq(model=f_model, temperature=0)
                    return alt_llm.invoke(messages)
                except Exception as ex:
                    print(f"❌ Fallback {f_model} failed: {str(ex)[:100]}")
                    continue
                    
            raise e

    def _get_cheap_llm(self):
        """단순 분석 작업을 위한 저비용 모델 반환"""
        if self.provider == "groq":
            return ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        elif self.provider == "openai":
            return ChatOpenAI(model="gpt-4o-mini", temperature=0)
        return self.llm

    def analyzer_node(self, state: ReadmeState) -> Dict[str, Any]:
        """프로젝트 구조를 스캔하고 아키타입 정의 (경량 모델 사용)"""
        print("🔍 [Analyzer] 분석 시작...")
        cheap_llm = self._get_cheap_llm()
        try:
            system_prompt = "당신은 프로젝트 분석 전문가입니다. 주어진 프로젝트 컨텍스트를 분석하여 핵심 아키타입을 분류하고 리포트를 JSON으로 작성하세요."
            user_prompt = f"""
            [Context]
            {state['project_context']}
            
                "analysis_report": res.get("summary", "분석 완료"),
                "iteration_count": 0
            }
        except Exception as e:
            print(f"❌ [Analyzer] 오류 발생: {e}")
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"--- [Analyzer Error] ---\n{str(e)}\n{traceback.format_exc()}\n")
            return {"archetype": "General", "analysis_report": "분석 중 오류 발생", "iteration_count": 0}

    def router_node(self, state: ReadmeState) -> Dict[str, Any]:
        """분석 결과에 따른 프롬프트 전략 수립"""
        print(f"🔀 [Router] 분기 처리 중... ({state.get('archetype', 'Unknown')})")
        return {"iteration_count": state.get("iteration_count", 0)}

    def writer_node(self, state: ReadmeState) -> Dict[str, Any]:
        """README 마크다운 초안 작성"""
        curr_iter = state.get("iteration_count", 0)
        print(f"✍️ [Writer] 초안 작성 중... (반복: {curr_iter})")
        
        try:
            # Context Truncation to stay within Ratelimits
            truncated_context = state.get('project_context', '')
            if len(truncated_context) > 12000: # 조금 더 보수적으로 12k로 제한
                truncated_context = truncated_context[:12000] + "\n... (Long context truncated for stability)"
            
            feedback_context = f"\n[Reviewer Feedback]: {state.get('feedback', '')}" if state.get('feedback') else ""
            
            system_prompt = "당신은 테크니컬 라이팅 전문가입니다. 분석 리포트와 실제 소스코드 컨텍스트, 그리고 사용자 정보를 바탕으로 프로젝트의 진정한 가치를 전달하는 압도적인 퀄리티의 README.md를 작성하세요."
            user_prompt = f"""
            [Archetype]: {state.get('archetype', 'General')}
            [Analysis Report]: {state.get('analysis_report', '')}
            [Project Context (Source Code)]:
            {truncated_context}

            [User Inputs]: {json.dumps(state.get('user_inputs', {}), ensure_ascii=False)}
            {feedback_context}
            
            작성 지침:
            1. **추론(Inference) 우선**: 사용자가 직접 입력하지 않은 항목(프로젝트 이름, 설명, 기술 스택, 시작하기 등)은 반드시 [Project Context]의 실제 코드를 분석하여 스스로 채워 넣으세요. 절대 "입력되지 않았습니다"와 같은 문구를 쓰지 마세요.
            2. **구조화**: 대제목, 한 줄 소개, 해결하려는 문제(분석 보고서 기반), 주요 기능(코드 기반), 기술 스택(뱃지 포함), 폴더 구조(트리 형태), 시작하기(Installation)를 반드시 포함하세요.
            3. **디테일**: 실제 파일명과 기술 스택을 언급하여 신뢰도를 높이세요.
            4. **피드백 반영**: 리퀘스트된 피드백이 있다면 최우선으로 반영하세요.
            5. **출력**: 오직 README.md 마크다운 텍스트만 출력하세요. 인사말이나 "네, 작성하겠습니다" 같은 지시어는 모두 생략하세요.
            """
            
            response = self._safe_invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            return {"draft": response.content, "iteration_count": curr_iter + 1}
        except Exception as e:
            print(f"❌ [Writer] 오류 발생: {e}")
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"--- [Writer Error] ---\n{str(e)}\n{traceback.format_exc()}\n")
            
            # Fallback README Generation (Simple)
            fallback_readme = f"# {state.get('archetype', 'Project')} README\n\nAI가 분석 중 오류가 발생하여 기본 정보를 출력합니다.\n\n## 분석 요약\n{state.get('analysis_report', '분석 정보가 없습니다.')}\n\n## 기술 스택\n{state.get('archetype', 'General')}"
            return {"draft": fallback_readme, "iteration_count": curr_iter + 1}

    def reviewer_node(self, state: ReadmeState) -> Dict[str, Any]:
        """초안 검토 및 승인 여부 결정"""
        print("🕵️ [Reviewer] 검토 진행 중...")
        try:
            system_prompt = "당신은 깐깐한 리뷰어 에이전트입니다. README 초안을 검사하여 승인 여부와 피드백을 JSON으로 응답하세요."
            user_prompt = f"""
            [README Draft]
            {state.get('draft', '')}
            
            체크리스트:
            1. 시작하기(Getting Started)가 정확한가?
            2. 기술 스택 뱃지와 폴더 구조가 포함되었는가?
            3. 프로젝트의 핵심 가치가 잘 설명되었는가?
            
            [출력 형식 - 반드시 JSON만 출력하세요]
            {{
              "decision": "REVISE or APPROVE",
              "feedback": "개선이 필요한 구체적인 피드백 (APPROVE일 경우 비워둠)"
            }}
            """
            response = self._safe_invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            content = self._extract_json(response.content)
            res = json.loads(content)
            decision = res.get("decision", "REVISE")
            
            return {
                "final_readme": state.get('draft', '') if decision == "APPROVE" else "",
                "feedback": res.get("feedback", ""),
                "decision": decision
            }
        except Exception as e:
            print(f"❌ [Reviewer] 오류 발생: {e}")
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"--- [Reviewer Error] ---\n{str(e)}\n{traceback.format_exc()}\n")
            return {"decision": "APPROVE", "final_readme": state.get('draft', '')}

    def should_continue(self, state: ReadmeState):
        """조건부 엣지 로직"""
        if state.get("decision") == "APPROVE" or state.get("iteration_count", 0) >= 3:
            return "approve"
        return "revise"

    def _extract_json(self, text: str) -> str:
        if "```json" in text:
            return text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    def run(self, project_context: str, user_inputs: dict) -> str:
        initial_state = {
            "project_context": project_context,
            "user_inputs": user_inputs,
            "iteration_count": 0,
            "provider": self.provider,
            "model_name": self.model_name
        }
        try:
            result = self.workflow.invoke(initial_state)
            return result.get("final_readme") or result.get("draft") or "README 생성 실패"
        except Exception as e:
            print(f"❌ [ReadmeAgent.run] 크리티컬 오류: {e}")
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"--- [Critical Run Error] ---\n{str(e)}\n{traceback.format_exc()}\n")
            return f"에이전트 실행 중 오류가 발생했습니다: {str(e)}"
