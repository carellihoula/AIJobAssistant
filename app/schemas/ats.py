from pydantic import BaseModel


class ATSAnalysisOut(BaseModel):
    ats_score: int
    keyword_match_rate: float
    present_keywords: list[str]
    missing_keywords: list[str]
    format_issues: list[str]
    improvement_suggestions: list[str]
    tailored_summary: str