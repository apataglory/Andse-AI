import logging
from extensions import db
from database.models import Message, ChatSession

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    The Cognitive Reservoir.
    Synthesizes past interactions to maintain state and personality.
    """
    
    def build_system_prompt(self, user, user_input):
        """
        Dynamically constructs the 'Master Directive' for the LLM.
        """
        base_prompt = (
            "You are ANDSE AI, an Ultra Massive Multimodal Intelligence System. "
            "Your output must be sophisticated, technically accurate, and contextually aware. "
            "You have access to web searching, email dispatch, and visual synthesis tools. "
            f"You are currently assisting user: {user.email}. "
            "Maintain a professional, helpful, and high-energy persona."
        )
        
        # Inject dynamic personality tweaks based on input
        if "analyze" in user_input.lower():
            base_prompt += " Prioritize deep structural analysis and data-driven insights."
        
        return base_prompt

    def get_chat_history(self, session_id, limit=10):
        """
        Retrieves the last N messages to maintain conversational flow.
        """
        try:
            messages = Message.query.filter_by(session_id=session_id)\
                                    .order_by(Message.timestamp.desc())\
                                    .limit(limit)\
                                    .all()
            # Return in chronological order
            return sorted(messages, key=lambda x: x.timestamp)
        except Exception as e:
            logger.error(f"Memory Retrieval Error: {e}")
            return []

    def add_memory(self, user_id, observation):
        """
        Could be expanded to vector-based memory. 
        Currently logs core user facts to the log for future retrieval.
        """
        logger.info(f"Cognitive Update for User {user_id}: {observation}")

# Global Singleton
memory_manager = MemoryManager()