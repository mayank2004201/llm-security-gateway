from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.api.schemas import ChatCompletionRequest
from core.security.input_guards import InputGuards
from core.security.output_guards import OutputGuards
from core.llm.groq_client import GroqClient
from core.llm.ollama_client import OllamaClient
from data.repository import Repository
import uuid
import time

router = APIRouter()
groq_client = GroqClient()
ollama_client = OllamaClient()

@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    request_id = str(uuid.uuid4())
    user_prompt = request.messages[-1].content
    user_id = request.user
    
    # 1. Input Guardrails
    if InputGuards.detect_prompt_injection(user_prompt):
        return {"error": "Security Block: Prompt Injection Detected", "request_id": request_id}, 403
        
    risk_score = InputGuards.calculate_risk_score(user_prompt)
    
    # 2. Policy: Human-in-the-loop for high risk
    if risk_score > 50:
        Repository.add_to_approval_queue(request_id, user_id, request.model, user_prompt)
        return {"status": "Pending Approval", "request_id": request_id, "message": "High-risk request queued for admin review."}

    # 3. LLM Interaction
    start_time = time.time()
    try:
        if "groq" in request.model.lower():
            response_data = groq_client.complete(request.model, user_prompt)
            llm_response = response_data['choices'][0]['message']['content']
            tokens = response_data.get('usage', {}).get('total_tokens', 0)
        else:
            response_data = ollama_client.complete(request.model, user_prompt)
            llm_response = response_data['message']['content']
            tokens = 0 # Ollama API varies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    latency = round(time.time() - start_time, 2)
    cost = (tokens / 1000) * 0.002 # Semi-static cost estimation
    
    # 4. Output Guardrails
    harm_category = OutputGuards.detect_harmful_content(llm_response)
    if harm_category:
        Repository.log_harmful(request_id, user_id, user_prompt, harm_category, risk_score)
        raise HTTPException(status_code=403, detail=f"Blocked: {harm_category} detected in output.")

    # 5. Success Logging
    Repository.log_request(request_id, user_id, request.model, user_prompt, llm_response, tokens, cost, risk_score, latency)
    
    return {
        "id": request_id,
        "choices": [{"message": {"role": "assistant", "content": llm_response}}],
        "usage": {"total_tokens": tokens}
    }

@router.post("/api/approve/{request_id}")
async def approve(request_id: str):
    Repository.approve_request(request_id)
    return {"status": "approved"}

@router.post("/api/deny/{request_id}")
async def deny(request_id: str):
    Repository.deny_request(request_id)
    return {"status": "denied"}
