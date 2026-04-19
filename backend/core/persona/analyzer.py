import os
from typing import Dict, List
import json
from langchain_core.messages import SystemMessage, HumanMessage

class PersonaAnalyzer:
    def __init__(self, engine):
        self.engine = engine # ChatFolioEngine instance for LLM

    def analyze_metrics(self, files_data: Dict[str, str], commit_hours: List[int]):
        # 1. 언어 비율 (Language Ratio)
        extensions = {}
        for path in files_data.keys():
            ext = path.split('.')[-1].lower() if '.' in path else 'others'
            extensions[ext] = extensions.get(ext, 0) + 1
        
        # 2. 주석 밀도 (Comment Density)
        total_lines = 0
        comment_lines = 0
        for content in files_data.values():
            lines = content.split('\n')
            total_lines += len(lines)
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(('//', '#', '/*', '*')):
                    comment_lines += 1
        
        comment_ratio = (comment_lines / total_lines * 100) if total_lines > 0 else 0
        
        # 3. 모듈화 정도 (Modularization)
        # 파일당 평균 라인 수 (낮을수록 모듈화가 잘 된 것으로 간주)
        avg_lines_per_file = (total_lines / len(files_data)) if files_data else 0
        
        # 4. 커밋 시간대 (Commit Time Type)
        # 0-6: 새벽(Vampire), 6-12: 오전(Early Bird), 12-18: 오후(Active), 18-24: 저녁(Night Owl)
        time_slots = {"Vampire": 0, "EarlyBird": 0, "Active": 0, "NightOwl": 0}
        for h in commit_hours:
            if 0 <= h < 6: time_slots["Vampire"] += 1
            elif 6 <= h < 12: time_slots["EarlyBird"] += 1
            elif 12 <= h < 18: time_slots["Active"] += 1
            else: time_slots["NightOwl"] += 1
            
        main_time = max(time_slots, key=time_slots.get)

        return {
            "top_languages": sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:3],
            "comment_ratio": round(comment_ratio, 1),
            "avg_lines_per_file": round(avg_lines_per_file, 1),
            "main_time_slot": main_time,
            "total_files": len(files_data)
        }

    async def generate_persona(self, metrics: dict):
        system_prompt = SystemMessage(content="""
        당신은 개발자들의 코딩 습관과 스타일을 분석해 재치 있는 별명을 붙여주는 '코더 페르소나 전문가'입니다.
        제공된 데이터(언어 비율, 주석 밀도, 모듈화 수준, 활동 시간대)를 바탕으로 해당 개발자의 '코딩 MBTI'와 '재치 있는 타이틀'을 생성하세요.
        
        [출력 포맷 (JSON 전용)]
        {
          "title": "새벽 3시의 뱀파이어 해커",
          "description": "모두가 잠든 시간, 가장 날카로운 코드를 작성하는 심야의 지배자입니다.",
          "traits": ["심야 집중형", "주석 성애자", "모듈화 장인"],
          "mbti_type": "VMPR (Vampire)"
        }
        """)
        
        user_prompt = HumanMessage(content=f"다음 데이터를 분석해줘: {json.dumps(metrics)}")
        
        try:
            response = self.engine.llm.invoke([system_prompt, user_prompt])
            # JSON만 추출 (마크다운 코드 블록 제거)
            clean_content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_content)
        except Exception as e:
            print(f"Persona Generation Error: {e}")
            return {
                "title": "코드 분석가",
                "description": "데이터 분석 중 오류가 발생했지만, 당신의 열정은 확인되었습니다.",
                "traits": ["열정 가득", "분석 중"],
                "mbti_type": "UNKNOWN"
            }
