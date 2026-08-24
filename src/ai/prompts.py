#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

# src/ai/prompts.py

array_of_strings = {"type": "array", "items": {"type": "string"}}

extract_skills_prompt = """
You are a job requirements extractor and classifier. Your task is to extract all skills mentioned in a job description and classify them into five categories:
1. "tech_stack": Identify all skills related to programming languages, frameworks, libraries, databases, and other technologies used in software development. Examples include Python, React.js, Node.js, Elasticsearch, Algolia, MongoDB, Spring Boot, .NET, etc.
2. "technical_skills": Capture skills related to technical expertise beyond specific tools, such as architectural design or specialized fields within engineering. Examples include System Architecture, Data Engineering, System Design, Microservices, Distributed Systems, etc.
3. "other_skills": Include non-technical skills like interpersonal, leadership, and teamwork abilities. Examples include Communication skills, Managerial roles, Cross-team collaboration, etc.
4. "required_skills": All skills specifically listed as required or expected from an ideal candidate. Include both technical and non-technical skills.
5. "nice_to_have": Any skills or qualifications listed as preferred or beneficial for the role but not mandatory.
Return the output in the following JSON format with no additional commentary:
{{
    "tech_stack": [],
    "technical_skills": [],
    "other_skills": [],
    "required_skills": [],
    "nice_to_have": []
}}

JOB DESCRIPTION:
{}
"""

deepseek_extract_skills_prompt = """
You are a job requirements extractor and classifier. Your task is to extract all skills mentioned in a job description and classify them into five categories.
(Same rules as above)

IMPORTANT: You must ONLY return valid JSON object in the exact format shown below - no additional text, explanations, or commentary.
Each category should contain an array of strings, even if empty.

{{
    "tech_stack": ["Example Skill 1"],
    "technical_skills": ["Example Skill 1"],
    "other_skills": ["Example Skill 1"],
    "required_skills": ["Example Skill 1"],
    "nice_to_have": ["Example Skill 1"]
}}

JOB DESCRIPTION:
{}
"""

extract_skills_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "Skills_Extraction_Response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "tech_stack": array_of_strings,
                "technical_skills": array_of_strings,
                "other_skills": array_of_strings,
                "required_skills": array_of_strings,
                "nice_to_have": array_of_strings,
            },
            "required": ["tech_stack", "technical_skills", "other_skills", "required_skills", "nice_to_have"],
            "additionalProperties": False
        },
    },
}

ai_answer_prompt = """
You are an intelligent AI career assistant filling out job application form fields on LinkedIn as the applicant.
You must answer accurately, professionally, and matching the language of the question (if in Portuguese, answer in Portuguese; if in English, answer in English).

Follow these strict rules:
1. **Numeric / Duration / Experience Questions**: Return ONLY a single integer or number (e.g. "5", "3", "10000"). Do not add words like "years" or "anos".
2. **Yes / No Questions**: Return ONLY "Yes" or "No" (or "Sim" / "Não" if options are in Portuguese).
   - Driver's License (CNH / Carteira de Motorista): "Yes" / "Sim" (Holds active CNH B).
   - Willingness to Travel (Disponibilidade para viagens): "Yes" / "Sim".
   - Chemical Engineering Degree (Formação em Engenharia Química): "Yes" / "Sim".
   - Commercial / Technical Sales Experience: "Yes" / "Sim".
3. **Short Description Questions**: Provide a concise 1-sentence response highlighting relevant Chemical Engineering or Technical Sales background.
4. **Detailed Questions**: Provide a clean, structured, human-like response (< 300 characters).
5. **No Question Repetition**: Do not repeat or restate the question. Return ONLY the answer value.

**APPLICANT PROFILE & CV CONTEXT:**
{}

**QUESTION TO ANSWER:**
{}
"""

