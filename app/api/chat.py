"""
Chat API Endpoints
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.services.chat_service import chat_service
from app.utils.excel_export import excel_exporter
from app.utils.query_cache import query_cache
from app.db.mongodb import mongodb_manager
from app.config import settings
from app.utils.json_sanitizer import sanitize_for_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model"""
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    session_id: Optional[str] = Field(None, description="Optional session ID for context")
    conversation_id: Optional[str] = Field(None, description="Optional conversation thread ID (like ChatGPT)")
    export_to_excel: Optional[bool] = Field(False, description="Export results to Excel file")
    include_data: Optional[bool] = Field(False, description="Include full data in response (may be large)")
    preview_rows: Optional[int] = Field(10, ge=0, le=100, description="Number of rows to include when include_data=false")


class CreateSessionRequest(BaseModel):
    """Create session request model"""
    user_name: Optional[str] = Field(None, max_length=200, description="User name")
    user_email: Optional[str] = Field(None, max_length=200, description="User email")
    user_metadata: Optional[dict] = Field(None, description="Additional user metadata (e.g., department, role)")


class ChatResponse(BaseModel):
    """
    Professional Chat Response Model
    
    All fields are clearly defined to help Frontend make decisions:
    - When to show charts (has_chart, chart_id)
    - When to show table (has_data, data_preview_rows)
    - When to show download button (has_more_data, has_excel)
    """
    success: bool = Field(..., description="Whether the request was successful")
    answer: Optional[str] = Field(None, description="Natural language answer to the question")
    
    # Data
    data: Optional[list] = Field(None, description="Data preview (limited to preview_rows)")
    has_data: bool = Field(False, description="True if query returned data")
    data_preview_rows: int = Field(0, description="Number of rows in data preview")
    data_total_rows: int = Field(0, description="Total rows available (before truncation)")
    has_more_data: bool = Field(False, description="True if there's more data beyond preview")
    
    # Visualization
    has_chart: bool = Field(False, description="True if a chart was generated")
    chart_id: Optional[str] = Field(None, description="Unique chart ID for retrieval")
    chart_url: Optional[str] = Field(None, description="URL path to access the chart image")
    chart_type: Optional[str] = Field(None, description="Type of chart: bar, line, scatter, pie")
    needs_visualization: bool = Field(False, description="AI suggests visualization would be helpful")
    visualization_type: Optional[str] = Field("none", description="Suggested visualization type")
    
    # Analysis
    statistical_insights: Optional[dict] = Field(None, description="Statistical analysis of the data")
    
    # Excel Export
    has_excel: bool = Field(False, description="True if Excel file is available")
    excel_url: Optional[str] = Field(None, description="URL to download Excel file")
    
    # IDs for data retrieval
    query_id: Optional[str] = Field(None, description="ID to get full data via /data/{query_id}")
    conversation_id: Optional[str] = Field(None, description="ID to retrieve conversation from history")
    
    # Error
    error: Optional[str] = Field(None, description="Error message if success=False")


def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> bool:
    """Verify API key if configured"""
    if settings.API_KEY:
        if not x_api_key or x_api_key != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True


def _to_safe_response(payload: dict) -> ChatResponse:
    """
    Ensure payload is JSON-serializable (no NaN/Inf) before returning it.
    """
    safe_payload = sanitize_for_json(payload)
    return ChatResponse(**safe_payload)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    _: bool = Depends(verify_api_key)
):
    """
    Chat endpoint - Ask questions about the database
    
    - **question**: Your question in natural language
    - **session_id**: Optional session ID for maintaining context
    """
    try:
        logger.info(
            f"Chat request received",
            extra={
                "question": request.question[:100],
                "session_id": request.session_id
            }
        )
        
        result = chat_service.handle_question(request.question)
        
        if not result["success"]:
            # Return professional error message in response body instead of raising exception
            # This allows the frontend to show the user-friendly message
            return _to_safe_response({
                "success": False,
                "answer": result.get("answer") or result.get("error", "Failed to process question"),
                "data": result.get("data"),
                "has_data": False,
                "data_preview_rows": 0,
                "data_total_rows": 0,
                "has_more_data": False,
                "has_chart": False,
                "chart_id": None,
                "chart_url": None,
                "chart_type": None,
                "needs_visualization": result.get("needs_visualization", False),
                "visualization_type": result.get("visualization_type", "none"),
                "has_excel": False,
                "excel_url": None,
                "error": result.get("error") or result.get("answer"),
            })
        
        # Export to Excel if requested
        excel_url = None
        if request.export_to_excel and result.get("data"):
            export_success, excel_path, export_error = excel_exporter.export_to_excel(
                data=result["data"],
                filename=f"query_{request.session_id or 'export'}"
            )
            
            if export_success:
                excel_url = f"/exports/{excel_path.split('/')[-1]}"
                logger.info(f"Excel file exported: {excel_path}")
            else:
                logger.warning(f"Excel export failed: {export_error}")
                # Don't fail the request, just log the error
        
        # Store full data in cache for later retrieval
        full_data = result.get("data")
        query_id = None
        if isinstance(full_data, list) and full_data:
            query_id = query_cache.store(
                data=full_data,
                question=request.question,
                sql_query=result.get("sql_query", ""),
                metadata=result.get("metadata", {})
            )
            result["query_id"] = query_id
        
        # Store message under a conversation thread (ChatGPT-like)
        conversation_id = None
        if mongodb_manager.is_connected():
            try:
                # Ensure conversation thread exists (if not provided, create one)
                conversation_id = request.conversation_id
                if not conversation_id:
                    title = (request.question or "New Conversation")[:80]
                    conversation_id = await mongodb_manager.create_conversation_thread(
                        session_id=request.session_id,
                        title=title,
                        user_metadata=None
                    )
                
                await mongodb_manager.append_message_to_conversation(
                    conversation_id=conversation_id,
                    question=request.question,
                    answer=result.get("answer", ""),
                    sql_query=result.get("sql_query"),
                    data=full_data,
                    query_id=query_id,
                    excel_file=excel_url,
                    chart=result.get("chart"),
                    metadata=result.get("metadata", {}),
                    session_id=request.session_id
                )
                result["conversation_id"] = conversation_id
                
                # Update session activity if session_id provided
                if request.session_id:
                    try:
                        await mongodb_manager.update_session_activity(request.session_id)
                        logger.debug(f"Session activity updated: {request.session_id}")
                    except Exception as e:
                        logger.warning(f"Failed to update session activity: {e}")
            except Exception as e:
                logger.error(f"Failed to store message in conversation: {e}", exc_info=True)
        else:
            logger.warning("MongoDB not connected, message not stored")
        
        # Process data for professional response
        data_val = result.get("data")
        has_data = isinstance(data_val, list) and len(data_val) > 0
        data_total_rows = len(data_val) if isinstance(data_val, list) else 0
        
        # Truncate data in response unless explicitly requested
        data_preview_rows = 0
        has_more_data = False
        
        if has_data:
            if not request.include_data:
                preview_n = request.preview_rows or 10
                if preview_n >= 0 and data_total_rows > preview_n:
                    result["data"] = data_val[:preview_n]
                    data_preview_rows = preview_n
                    has_more_data = True
                else:
                    data_preview_rows = data_total_rows
                    has_more_data = False
            else:
                data_preview_rows = data_total_rows
                has_more_data = False
        
        # Process chart information
        chart_info = result.get("chart")
        has_chart = chart_info is not None and chart_info.get("url") is not None
        chart_id = None
        chart_url = None
        chart_type = None
        
        if has_chart:
            chart_url = chart_info.get("url")
            chart_type = chart_info.get("type")
            # Extract chart ID from URL (e.g., /charts/generated/uuid.png -> uuid)
            if chart_url:
                chart_filename = chart_url.split("/")[-1]  # uuid.png
                chart_id = chart_filename.rsplit(".", 1)[0]  # uuid
        
        # Build professional response
        return _to_safe_response({
            "success": True,
            "answer": result.get("answer"),
            "data": result.get("data"),
            "has_data": has_data,
            "data_preview_rows": data_preview_rows,
            "data_total_rows": data_total_rows,
            "has_more_data": has_more_data,
            "has_chart": has_chart,
            "chart_id": chart_id,
            "chart_url": chart_url,
            "chart_type": chart_type,
            "needs_visualization": result.get("needs_visualization", False),
            "visualization_type": result.get("visualization_type", "none"),
            "statistical_insights": result.get("statistical_insights"),
            "has_excel": excel_url is not None or query_id is not None,  # Can export via query_id
            "excel_url": excel_url or (f"/api/v1/chat/export/{query_id}" if query_id else None),
            "query_id": query_id,
            "conversation_id": conversation_id,
            "error": None
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "llm_available": chat_service.sql_chain is not None
    }


@router.get("/data/{query_id}")
async def get_full_data(
    query_id: str,
    _: bool = Depends(verify_api_key)
):
    """
    Get full data for a query by query_id
    
    - **query_id**: Query ID returned from /chat endpoint
    - Returns complete data (not truncated)
    """
    cached = query_cache.get(query_id)
    
    if not cached:
        raise HTTPException(
            status_code=404,
            detail=f"Query not found or expired. Query ID: {query_id}"
        )
    
    return {
        "success": True,
        "query_id": query_id,
        "question": cached["question"],
        "data": cached["data"],
        "row_count": cached["row_count"]
    }


@router.get("/export/{query_id}")
async def export_to_excel(
    query_id: str,
    _: bool = Depends(verify_api_key)
):
    """
    Export query results to Excel file
    
    - **query_id**: Query ID returned from /chat endpoint
    - Returns Excel file download
    """
    from fastapi.responses import FileResponse
    import os
    
    cached = query_cache.get(query_id)
    
    if not cached:
        raise HTTPException(
            status_code=404,
            detail=f"Query not found or expired. Query ID: {query_id}"
        )
    
    # Export to Excel
    export_success, excel_path, export_error = excel_exporter.export_to_excel(
        data=cached["data"],
        filename=f"query_{query_id}"
    )
    
    if not export_success:
        raise HTTPException(
            status_code=500,
            detail=f"Excel export failed: {export_error}"
        )
    
    if not os.path.exists(excel_path):
        raise HTTPException(
            status_code=500,
            detail="Excel file not found after export"
        )
    
    # Return file for download
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(excel_path),
        headers={
            "Content-Disposition": f"attachment; filename={os.path.basename(excel_path)}"
        }
    )


@router.get("/history")
async def get_conversation_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    _: bool = Depends(verify_api_key)
):
    """
    Get conversation history from MongoDB
    
    - **session_id**: Filter by session ID (optional)
    - **limit**: Maximum number of conversations (default: 50)
    - **skip**: Skip N conversations for pagination (default: 0)
    """
    if not mongodb_manager.is_connected():
        raise HTTPException(
            status_code=503,
            detail="MongoDB not available"
        )
    
    try:
        conversations = await mongodb_manager.get_history(
            session_id=session_id,
            limit=limit,
            skip=skip
        )
        
        # Remove technical data from all conversations (for end users)
        clean_conversations = []
        for conv in conversations:
            clean_conv = {
                "conversation_id": conv.get("conversation_id"),
                "question": conv.get("question"),
                "answer": conv.get("answer"),
                "data": conv.get("data"),
                "chart": conv.get("chart"),
                "excel_file": conv.get("excel_file"),
                "query_id": conv.get("query_id"),
                "created_at": conv.get("created_at")
            }
            clean_conversations.append(clean_conv)
        
        return {
            "success": True,
            "count": len(clean_conversations),
            "conversations": clean_conversations
        }
    except Exception as e:
        logger.error(f"Failed to retrieve history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.get("/history/{conversation_id}")
async def get_conversation_detail(
    conversation_id: str,
    _: bool = Depends(verify_api_key)
):
    """
    Get specific conversation by ID from MongoDB
    
    - **conversation_id**: MongoDB conversation ID (24-character hex string)
    - Returns full conversation with all data, files, charts
    """
    # Validate conversation_id format
    if not conversation_id or conversation_id.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="conversation_id is required"
        )
    
    # Check for common invalid values (like "undefined", "null", etc.)
    invalid_values = ["undefined", "null", "None", ""]
    if conversation_id.lower() in invalid_values:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid conversation_id: '{conversation_id}'. Must be a valid MongoDB ObjectId (24-character hex string)"
        )
    
    # Validate ObjectId format (24 hex characters)
    if len(conversation_id) != 24 or not all(c in '0123456789abcdefABCDEF' for c in conversation_id):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid conversation_id format: '{conversation_id}'. Must be a 24-character hex string"
        )
    
    if not mongodb_manager.is_connected():
        raise HTTPException(
            status_code=503,
            detail="MongoDB not available"
        )
    
    try:
        conversation = await mongodb_manager.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation not found: {conversation_id}"
            )
        
        # Remove technical data from response (for end users)
        conversation.pop("sql_query", None)
        conversation.pop("metadata", None)
        
        # Keep only user-friendly data
        clean_conversation = {
            "conversation_id": conversation.get("conversation_id"),
            "question": conversation.get("question"),
            "answer": conversation.get("answer"),
            "data": conversation.get("data"),
            "chart": conversation.get("chart"),
            "excel_file": conversation.get("excel_file"),
            "query_id": conversation.get("query_id"),
            "created_at": conversation.get("created_at")
        }
        
        return {
            "success": True,
            "conversation": clean_conversation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve conversation: {e}", exc_info=True)
        # Check if it's an ObjectId validation error
        if "InvalidId" in str(type(e).__name__) or "ObjectId" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid conversation_id format: '{conversation_id}'. Must be a valid MongoDB ObjectId"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )


@router.get("/search")
async def search_conversations(
    q: str,
    limit: int = 20,
    _: bool = Depends(verify_api_key)
):
    """
    Search conversations by question or answer text
    
    - **q**: Search query
    - **limit**: Maximum number of results (default: 20)
    """
    if not mongodb_manager.is_connected():
        raise HTTPException(
            status_code=503,
            detail="MongoDB not available"
        )
    
    try:
        conversations = await mongodb_manager.search_conversations(
            search_text=q,
            limit=limit
        )
        
        # Remove technical data from all conversations (for end users)
        clean_conversations = []
        for conv in conversations:
            clean_conv = {
                "conversation_id": conv.get("conversation_id"),
                "question": conv.get("question"),
                "answer": conv.get("answer"),
                "data": conv.get("data"),
                "chart": conv.get("chart"),
                "excel_file": conv.get("excel_file"),
                "query_id": conv.get("query_id"),
                "created_at": conv.get("created_at")
            }
            clean_conversations.append(clean_conv)
        
        return {
            "success": True,
            "count": len(clean_conversations),
            "search_query": q,
            "conversations": clean_conversations
        }
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/session", response_model=dict)
async def create_session(
    request: CreateSessionRequest,
    _: bool = Depends(verify_api_key)
):
    """
    Create a new chat session with user information
    
    - **user_name**: Optional user name
    - **user_email**: Optional user email
    - **user_metadata**: Optional additional metadata (JSON object)
    
    Returns session_id for use in subsequent chat requests
    """
    if not mongodb_manager.is_connected():
        raise HTTPException(
            status_code=503,
            detail="MongoDB not available"
        )
    
    try:
        session_id = await mongodb_manager.create_session(
            user_name=request.user_name,
            user_email=request.user_email,
            user_metadata=request.user_metadata
        )
        
        logger.info(f"Session created: {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )


class CreateConversationRequest(BaseModel):
    """Create conversation thread request"""
    session_id: Optional[str] = Field(None, description="Session ID to associate the conversation with")
    title: Optional[str] = Field(None, max_length=200, description="Optional conversation title")
    user_metadata: Optional[dict] = Field(None, description="Optional metadata")


@router.post("/conversation", response_model=dict)
async def create_conversation(
    request: CreateConversationRequest,
    _: bool = Depends(verify_api_key)
):
    """
    Create a new conversation thread (ChatGPT-like)
    """
    if not mongodb_manager.is_connected():
        raise HTTPException(status_code=503, detail="MongoDB not available")
    try:
        conversation_id = await mongodb_manager.create_conversation_thread(
            session_id=request.session_id,
            title=(request.title or "New Conversation"),
            user_metadata=request.user_metadata or {}
        )
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "Conversation created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/conversations", response_model=dict)
async def list_conversations(
    session_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    _: bool = Depends(verify_api_key)
):
    """
    List conversation threads (optionally filter by session)
    """
    if not mongodb_manager.is_connected():
        raise HTTPException(status_code=503, detail="MongoDB not available")
    try:
        threads = await mongodb_manager.get_conversation_threads(
            session_id=session_id,
            limit=limit,
            skip=skip
        )
        # Clean technical fields
        clean = []
        for t in threads:
            clean.append({
                "conversation_id": t.get("conversation_id"),
                "session_id": t.get("session_id"),
                "title": t.get("title"),
                "message_count": t.get("message_count", 0),
                "created_at": t.get("created_at"),
                "last_activity": t.get("last_activity"),
                "is_active": t.get("is_active", True)
            })
        return {
            "success": True,
            "count": len(clean),
            "limit": limit,
            "skip": skip,
            "conversations": clean
        }
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get("/conversation/{conversation_id}/messages", response_model=dict)
async def list_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    skip: int = 0,
    _: bool = Depends(verify_api_key)
):
    """
    List messages for a conversation thread
    """
    if not mongodb_manager.is_connected():
        raise HTTPException(status_code=503, detail="MongoDB not available")
    try:
        messages = await mongodb_manager.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit,
            skip=skip
        )
        # Clean technical fields for end-user
        clean = []
        for m in messages:
            clean.append({
                "question": m.get("question"),
                "answer": m.get("answer"),
                "has_data": bool(m.get("data")),
                "has_chart": bool(m.get("chart")),
                "query_id": m.get("query_id"),
                "created_at": m.get("created_at")
            })
        return {
            "success": True,
            "count": len(clean),
            "limit": limit,
            "skip": skip,
            "messages": clean
        }
    except Exception as e:
        logger.error(f"Failed to list conversation messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list conversation messages: {str(e)}")

@router.get("/session/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    _: bool = Depends(verify_api_key)
):
    """
    Get session information including user data and statistics
    
    - **session_id**: Session ID from /session endpoint
    """
    if not mongodb_manager.is_connected():
        raise HTTPException(
            status_code=503,
            detail="MongoDB not available"
        )
    
    try:
        session = await mongodb_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        # Get conversation count for this session
        conversations = await mongodb_manager.get_history(
            session_id=session_id,
            limit=1000  # Get count
        )
        
        session["total_conversations"] = len(conversations)
        
        return {
            "success": True,
            "session": session
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


@router.get("/sessions", response_model=dict)
async def get_all_sessions(
    limit: int = 50,
    skip: int = 0,
    active_only: bool = False,
    _: bool = Depends(verify_api_key)
):
    """
    Get all sessions with pagination
    
    - **limit**: Maximum number of sessions (default: 50)
    - **skip**: Number to skip for pagination (default: 0)
    - **active_only**: Only return active sessions (default: false)
    """
    if not mongodb_manager.is_connected():
        raise HTTPException(
            status_code=503,
            detail="MongoDB not available"
        )
    
    try:
        sessions = await mongodb_manager.get_all_sessions(
            limit=limit,
            skip=skip,
            active_only=active_only
        )
        
        return {
            "success": True,
            "count": len(sessions),
            "limit": limit,
            "skip": skip,
            "active_only": active_only,
            "sessions": sessions
        }
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sessions: {str(e)}"
        )


@router.post("/session/{session_id}/end", response_model=dict)
async def end_session(
    session_id: str,
    _: bool = Depends(verify_api_key)
):
    """
    End (deactivate) a session
    
    - **session_id**: Session ID to end
    """
    if not mongodb_manager.is_connected():
        raise HTTPException(
            status_code=503,
            detail="MongoDB not available"
        )
    
    try:
        success = await mongodb_manager.end_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        return {
            "success": True,
            "message": "Session ended successfully",
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to end session: {str(e)}"
        )
