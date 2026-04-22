from typing import Annotated, TypedDict, List, Dict, Any, Union
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
import json

class ReadmeState(TypedDict):
    project_context: str
    user_inputs: Dict[str, Any]
    archetype: str  # BE, FE, ML, Library 등
    analysis_report: str
    draft: str
    feedback: str
    iteration_count: int
    final_readme: str

class ReadmeAgent:
    def __init__(self, llm):
        self.llm = llm
        self.workflow = self._create_workflow()

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

    def analyzer_node(self, state: ReadmeState) -> Dict[str, Any]:
        """프로젝트 구조를 스캔하고 아키타입 정의"""
        print("🔍 [Analyzer] 분석 시작...")
        prompt = f"""
        당신은 프로젝트 분석 전문가입니다. 다음 프로젝트 컨텍스트를 보고 핵심 아키타입과 요약 리포트를 작성하세요.
        
        [Context]
        {state['project_context']}
        
        [출력 형식 - 반드시 JSON만 출력하세요]
        {{
          "archetype": "Backend / Frontend / ML / Library 중 하나",
          "summary": "프로젝트의 핵심 비즈니스 로직 및 구조 요약"
        }}
        """
        response = self.llm.invoke([SystemMessage(content=prompt)])
        try:
            content = self._extract_json(response.content)
            res = json.loads(content)
            return {
                "archetype": res.get("archetype", "Unknown"),
                "analysis_report": res.get("summary", ""),
                "iteration_count": 0
            }
        except:
            return {"archetype": "General", "analysis_report": "분석 실패", "iteration_count": 0}

    def router_node(self, state: ReadmeState) -> Dict[str, Any]:
        """분석 결과에 따른 프롬프트 전략 수립"""
        print(f"🔀 [Router] 분기 처리 중... ({state['archetype']})")
        # 실제로는 여기서 state를 보고 특정 시스템 프롬프트를 고르는 로직
        # 현재는 iteration_count 등 상태 초기화 역할도 수행
        return {}

    def writer_node(self, state: ReadmeState) -> Dict[str, Any]:
        """README 마크다운 초안 작성"""
        print(f"✍️ [Writer] 초안 작성 중... (반복: {state['iteration_count']})")
        feedback_context = f"\n[Reviewer Feedback]: {state.get('feedback', '')}" if state.get('feedback') else ""
        
        prompt = f"""
        당신은 테크니컬 라이팅 전문가입니다. 
        분석 리포트와 사용자 정보를 바탕으로 압도적인 퀄리티의 README.md를 작성하세요.
        
        [Archetype]: {state['archetype']}
        [Analysis Report]: {state['analysis_report']}
        [User Inputs]: {json.dumps(state['user_inputs'], ensure_ascii=False)}
        {feedback_context}
        
        작성 규칙:
        - 대제목, 기능 요약, 기술 스택, 폴더 구조, 시작하기(Installation)를 포함할 것.
        - 피드백이 있다면 반드시 반영하여 수정할 것.
        - 오직 README.md 마크다운 텍스트만 출력하세요.
        """
        response = self.llm.invoke([SystemMessage(content=prompt)])
        return {"draft": response.content, "iteration_count": state['iteration_count'] + 1}

    def reviewer_node(self, state: ReadmeState) -> Dict[str, Any]:
        """초안 검토 및 승인 여부 결정"""
        print("🕵️ [Reviewer] 검토 진행 중...")
        prompt = f"""
        당신은 깐깐한 리뷰어 에이전트입니다. 다음 README 초안을 검사하세요.
        
        [README Draft]
        {state['draft']}
        
        체크리스트:
        1. 시작하기(Getting Started) 명령어가 명확하고 정확한가?
        2. 기술 스택 뱃지와 폴더 구조가 잘 포함되었는가?
        3. 프로젝트의 핵심 가치가 잘 설명되었는가?
        
        결정:
        - 부족함이 있다면 'REVISE'와 구체적인 피드백을 전달하세요.
        - 충분히 완벽하다면 'APPROVE'라고 답변하세요.
        
        [출력 형식 - 반드시 JSON만 출력하세요]
        {{
          "decision": "REVISE or APPROVE",
          "feedback": "피드백 내용 (APPROVE일 경우 비워둠)"
        }}
        """
        response = self.llm.invoke([SystemMessage(content=prompt)])
        try:
            content = self._extract_json(response.content)
            res = json.loads(content)
            return {
                "final_readme": state['draft'] if res.get("decision") == "APPROVE" else "",
                "feedback": res.get("feedback", ""),
                "decision": res.get("decision", "REVISE") # should_continue에서 사용
            }
        except:
            return {"decision": "APPROVE", "final_readme": state['draft']} # 실패 시 관용적으로 허용

    def should_continue(self, state: ReadmeState):
        """조건부 엣지 로직"""
        # 리뷰어의 결정에 따라 루프 여부 결정
        # 무한 루프 방지를 위해 최대 3회까지만 반복
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
            "iteration_count": 0
        }
        result = self.workflow.invoke(initial_state)
        return result.get("final_readme", result.get("draft", ""))
