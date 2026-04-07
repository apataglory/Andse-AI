import logging
import re
import os
from datetime import datetime, timedelta
from llm_api import llm_client
from memory_manager import memory_manager
from web_scraper import web_searcher
from image_generator import image_gen
from document_editor import doc_editor
from video_editor import video_editor
from email_service import email_service
from automation_engine import automation_engine

logger = logging.getLogger(__name__)

class ReasoningEngine:
    """
    The Master Logic Controller.
    Orchestrates Tool-Use, Multimodal Input, and Proactive Automation.
    """

    def process_request(self, user, session_id, user_input, file_info=None):
        """
        The main processing loop with deep tool-use detection.
        """
        # 1. RETRIEVE CONTEXT & MEMORY
        history = memory_manager.get_chat_history(session_id)
        system_prompt = memory_manager.build_system_prompt(user, user_input)
        
        # 2. MULTIMODAL DATA INGESTION
        context_extension = ""
        image_to_process = None

        if file_info:
            file_path = file_info.get('filepath')
            file_type = file_info.get('type')
            
            if file_type == 'documents':
                logger.info(f"Analyzing document: {file_path}")
                doc_text = doc_editor.read_document(file_path, file_info.get('ext'))
                context_extension = f"\n[DOCUMENT_DATA_START]\n{doc_text}\n[DOCUMENT_DATA_END]\n"
            
            elif file_type == 'images':
                logger.info(f"Setting vision target: {file_path}")
                image_to_process = file_path

        # 3. TOOL INTENT DETECTION (The "Action" Layer)
        text_lower = user_input.lower()
        
        # --- TOOL: WEB SEARCH ---
        if any(word in text_lower for word in ['search', 'latest', 'current', 'news', 'who is', 'weather']):
            yield "🔍 *Initiating Global Network Scan...*\n\n"
            search_results = web_searcher.search(user_input)
            context_extension += f"\n[WEB_SEARCH_RESULTS]: {search_results}\n"
            logger.info("Web search tool triggered.")

        # --- TOOL: EMAIL DISPATCH ---
        if "email me" in text_lower or "send email" in text_lower:
            yield "📧 *Accessing SMTP Protocol...*\n\n"
            # Logic to extract "what" to email - looking for the summary of current context
            email_body = f"Hello {user.email},\n\nThis is the report you requested from ANDSE AI.\n\nContext: {user_input}"
            result = email_service.send_email(
                recipient=user.email,
                subject="ANDSE AI Intelligence Report",
                body=email_body
            )
            if result['success']:
                yield f"✅ **Success:** Intelligence report dispatched to {user.email}.\n\n"
            else:
                yield f"❌ **Error:** Dispatch failed: {result['error']}\n\n"

        # --- TOOL: AUTOMATION / REMINDERS ---
        if "remind me" in text_lower or "schedule" in text_lower:
            yield "⏰ *Configuring Temporal Trigger...*\n\n"
            # In a full system, we'd use regex to find "in 5 minutes". 
            # For this 'Ultra' version, we default to a 2-minute safety check.
            trigger_time = datetime.now() + timedelta(minutes=2)
            automation_engine.create_task(
                task_type="email_report",
                payload={"email": user.email, "content": f"REMINDER: {user_input}"},
                trigger_time=trigger_time
            )
            yield f"✅ **Temporal Trigger Set:** I will notify you in 2 minutes regarding: '{user_input}'.\n\n"

        # --- TOOL: IMAGE GENERATION ---
        if any(word in text_lower for word in ['generate image', 'create a picture', 'draw']):
            yield "🎨 *Initializing Neural Rendering...*\n\n"
            image_url = image_gen.generate(user_input)
            if image_url:
                yield f"![Generated Image]({image_url})\n\n"
                user_input = f"I have successfully generated the image. Please explain what I created: {user_input}"
            else:
                yield "❌ **Rendering Error:** Visual synthesis failed.\n\n"

        # 4. FINAL LLM SYNTHESIS & STREAMING
        # Combine everything into the final prompt
        final_prompt = f"{context_extension}\nUser Request: {user_input}"
        
        full_response = ""
        # We use the MODERN llm_client with the new Google SDK
        for chunk in llm_client.generate_response(
            prompt=final_prompt,
            history=history,
            system_prompt=system_prompt,
            provider=user.settings.primary_llm if user.settings else 'gemini',
            image_path=image_to_process
        ):
            full_response += chunk
            yield chunk

        # 5. LONG-TERM MEMORY COMMIT
        try:
            memory_manager.add_memory(user.id, f"Interaction: {user_input[:100]} | Result: {full_response[:100]}")
        except Exception as e:
            logger.error(f"Memory Commit Error: {e}")

reasoning_engine = ReasoningEngine()