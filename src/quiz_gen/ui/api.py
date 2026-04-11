from fastapi import APIRouter, HTTPException
import asyncio
import uuid
from pydantic import BaseModel
from quiz_gen.agents.workflow import QuizGenerationWorkflow
from quiz_gen.agents.config import AgentConfig
from .projects import save_quiz, save_debug

router = APIRouter()
quiz_generation_lock = asyncio.Lock()

CURRENT_AGENT_CONFIG: dict = {}
REQUIRED_AGENT_CONFIG_KEYS = {
    "conceptual_provider",
    "practical_provider",
    "validator_provider",
    "refiner_provider",
    "judge_provider",
    "conceptual_model",
    "practical_model",
    "validator_model",
    "refiner_model",
    "judge_model",
}


class QuizRequest(BaseModel):
    content: str
    section_type: str = None
    number: str = None
    title: str = None
    metadata: dict = None
    hierarchy_path: list[str] | None = None
    project: str = "default"
    doc_id: str | None = None


class AgentConfigRequest(BaseModel):
    conceptual_provider: str | None = None
    practical_provider: str | None = None
    validator_provider: str | None = None
    refiner_provider: str | None = None
    judge_provider: str | None = None
    conceptual_model: str | None = None
    practical_model: str | None = None
    validator_model: str | None = None
    refiner_model: str | None = None
    judge_model: str | None = None


@router.post("/api/agent-config")
async def update_agent_config(request: AgentConfigRequest):
    updates = request.model_dump(exclude_none=True)
    CURRENT_AGENT_CONFIG.update(updates)
    return {"status": "ok", "config": CURRENT_AGENT_CONFIG}


@router.post("/api/generate-quiz")
async def generate_quiz(request: QuizRequest):
    missing_keys = REQUIRED_AGENT_CONFIG_KEYS - CURRENT_AGENT_CONFIG.keys()
    if missing_keys:
        missing_list = ", ".join(sorted(missing_keys))
        raise HTTPException(
            status_code=400,
            detail=f"Missing agent config. Set via /api/agent-config. Missing: {missing_list}",
        )
    chunk = {
        "section_type": request.section_type or "section",
        "number": request.number,
        "title": request.title or "Section",
        "content": request.content,
        "parent_section": None,
        "hierarchy_path": request.hierarchy_path or [request.title or "Section"],
        "metadata": request.metadata or {},
    }
    config = AgentConfig(
        conceptual_provider=CURRENT_AGENT_CONFIG["conceptual_provider"],
        practical_provider=CURRENT_AGENT_CONFIG["practical_provider"],
        validator_provider=CURRENT_AGENT_CONFIG["validator_provider"],
        refiner_provider=CURRENT_AGENT_CONFIG["refiner_provider"],
        judge_provider=CURRENT_AGENT_CONFIG["judge_provider"],
        conceptual_model=CURRENT_AGENT_CONFIG["conceptual_model"],
        practical_model=CURRENT_AGENT_CONFIG["practical_model"],
        validator_model=CURRENT_AGENT_CONFIG["validator_model"],
        refiner_model=CURRENT_AGENT_CONFIG["refiner_model"],
        judge_model=CURRENT_AGENT_CONFIG["judge_model"],
        auto_accept_valid=False,
        verbose=True,
    )
    try:
        config.validate()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config error: {e}")
    try:
        async with quiz_generation_lock:
            workflow = QuizGenerationWorkflow(config)
            result = workflow.run(chunk)
            questions = result.get("final_questions", [])
            for question in questions:
                if isinstance(question, dict) and "hierarchy_path" not in question:
                    question["hierarchy_path"] = chunk["hierarchy_path"]

            response_payload = {
                "questions": questions,
                "conceptual_generator": {"output": result.get("conceptual_qa", {})},
                "practical_generator": {"output": result.get("practical_qa", {})},
                "initial_validator": {
                    "results": result.get("initial_validation_results", [])
                },
                "refiner": {
                    "refined_conceptual": result.get("refined_conceptual_qa"),
                    "refined_practical": result.get("refined_practical_qa"),
                },
                "validator": {
                    "results": result.get("validation_results", []),
                    "all_valid": result.get("all_valid"),
                },
                "judge": {
                    "decision": result.get("judge_decision"),
                    "reasoning": result.get("judge_reasoning"),
                },
                "errors": result.get("errors", []),
            }

            # ── Persist to project ──────────────────────────────────────
            quiz_id = f"quiz_{uuid.uuid4().hex[:12]}"
            try:
                config_snapshot = {k: CURRENT_AGENT_CONFIG[k] for k in CURRENT_AGENT_CONFIG}
                save_quiz(
                    project=request.project,
                    quiz_id=quiz_id,
                    document_id=request.doc_id,
                    section_title=request.title,
                    section_type=request.section_type,
                    config_dict=config_snapshot,
                    questions=questions,
                    full_result={
                        "quiz_id": quiz_id,
                        "section_title": request.title,
                        "section_type": request.section_type,
                        "hierarchy_path": request.hierarchy_path,
                        **response_payload,
                    },
                )
                save_debug(
                    project=request.project,
                    quiz_id=quiz_id,
                    debug_data={
                        "quiz_id": quiz_id,
                        "request": {
                            "section_type": request.section_type,
                            "number": request.number,
                            "title": request.title,
                            "hierarchy_path": request.hierarchy_path,
                            "project": request.project,
                            "doc_id": request.doc_id,
                        },
                        "config": config_snapshot,
                        "raw_result": {
                            k: v for k, v in result.items()
                            if k != "final_questions"
                        },
                        "final_questions": questions,
                    },
                )
            except Exception as save_err:
                # Don't fail the request if persistence fails
                print(f"[projects] Failed to save quiz {quiz_id}: {save_err}")

            response_payload["quiz_id"] = quiz_id
            return response_payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation error: {e}")
