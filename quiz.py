from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from database import has_active_plan

router = APIRouter(prefix="/quiz", tags=["Quiz"])

QUIZ_QUESTIONS: List[Dict] = [
    {
        "id": "q1",
        "topic": "PAYE",
        "is_premium": False,
        "question": "By which day of the following month are PAYE deductions generally due in Kenya?",
        "options": [
            "5th day",
            "9th day",
            "20th day",
            "Last day of the month",
        ],
        "correct_index": 1,
        "explanation": "PAYE is generally due on or before the 9th day of the month following the deduction.",
    },
    {
        "id": "q2",
        "topic": "VAT",
        "is_premium": True,
        "question": "What is the main difference between zero-rated and exempt VAT supplies?",
        "options": [
            "Zero-rated allows input VAT recovery; exempt generally does not",
            "Exempt allows input VAT recovery; zero-rated does not",
            "Both are charged at the standard VAT rate on invoices",
            "There is no difference in iTax reporting",
        ],
        "correct_index": 0,
        "explanation": "Zero-rated supplies carry a 0% rate while permitting input VAT deduction on related taxable inputs, whereas exempt supplies generally do not allow input tax recovery.",
    },
    {
        "id": "q3",
        "topic": "TOT",
        "is_premium": True,
        "question": "Turnover Tax (TOT) is primarily calculated on which base?",
        "options": [
            "Net accounting profit after all expenses",
            "Gross business receipts/turnover",
            "Total fixed assets owned",
            "Employee headcount",
        ],
        "correct_index": 1,
        "explanation": "Turnover Tax applies to gross business sales/receipts for qualifying businesses within the statutory threshold.",
    },
]


class QuizSubmission(BaseModel):
    email: Optional[str] = None
    answers: Dict[str, int]  # maps question_id -> selected option index


@router.get("/questions")
def get_questions(
    topic: Optional[str] = Query(default=None),
    email: Optional[str] = Query(default=None),
):
    active = has_active_plan(email) if email else False
    filtered = QUIZ_QUESTIONS
    if topic:
        filtered = [q for q in filtered if q["topic"].lower() == topic.strip().lower()]

    public_questions = []
    for q in filtered:
        locked = q["is_premium"] and not active
        public_questions.append(
            {
                "id": q["id"],
                "topic": q["topic"],
                "is_premium": q["is_premium"],
                "locked": locked,
                "question": q["question"],
                "options": [] if locked else q["options"],
            }
        )

    return {"plan_active": active, "questions": public_questions}


@router.post("/submit")
def submit_quiz(submission: QuizSubmission):
    active = has_active_plan(submission.email) if submission.email else False
    total = 0
    correct = 0
    results = []

    for q in QUIZ_QUESTIONS:
        if q["is_premium"] and not active:
            continue
        total += 1
        selected = submission.answers.get(q["id"])
        is_correct = selected == q["correct_index"]
        if is_correct:
            correct += 1
        results.append(
            {
                "id": q["id"],
                "selected_index": selected,
                "correct_index": q["correct_index"],
                "is_correct": is_correct,
                "explanation": q["explanation"],
            }
        )

    if total == 0:
        raise HTTPException(
            status_code=403,
            detail="No accessible questions. Activate your 30-day plan to unlock premium quiz questions.",
        )

    score_percent = round((correct / total) * 100, 1)
    return {
        "correct": correct,
        "total": total,
        "score_percent": score_percent,
        "results": results,
    }