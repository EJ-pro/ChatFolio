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

    async def generate_persona(self, metrics: dict, language: str = "English"):
        system_prompt = SystemMessage(content="""
        You are a 'Coder Persona Expert' who analyzes developers' coding habits and styles to give them witty nicknames.
        Based on the provided data (language ratio, comment density, modularization level, activity time), generate a 'Coding MBTI' and a 'Witty Title' for the developer.
        
        [Output Format (JSON only)]
        {
          "title": "3 AM Vampire Hacker",
          "description": "A ruler of the deep night who writes the sharpest code while everyone else is asleep.",
          "traits": ["Night Owl", "Comment Enthusiast", "Modularization Master"],
          "mbti_type": "VMPR (Vampire)"
        }
        
        IMPORTANT: Your output (title, description, traits) MUST be in {language}.
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
                "title": "Code Analyst",
                "description": "An error occurred during data analysis, but your passion was confirmed.",
                "traits": ["Full of Passion", "Analyzing"],
                "mbti_type": "UNKNOWN"
            }
