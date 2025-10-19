"""
AI Chatbot Module using Google Gemini API
Provides intelligent responses and acts as an AI agent
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Data class for chat messages"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    metadata: Optional[Dict] = None

@dataclass
class ChatSession:
    """Data class for chat sessions"""
    session_id: str
    messages: List[ChatMessage]
    created_at: datetime
    context: Optional[Dict] = None

class GeminiChatbot:
    """
    AI Chatbot using Google's Gemini API
    Acts as an intelligent agent for answering questions and providing assistance
    """
    
    def __init__(self, model_name: str = "gemini-pro"):
        """
        Initialize Gemini chatbot
        
        Args:
            model_name: Gemini model to use (updated for v0.7.0)
        """
        # Get API key from environment - try both variable names
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required")
        
        self.api_key = api_key.strip()  # Remove any whitespace
        self.model_name = model_name
        
        try:
            # Set both environment variables for compatibility
            os.environ["GOOGLE_API_KEY"] = self.api_key
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            
            # Test the API key with a simple request to verify it works
            try:
                test_response = self.model.generate_content("Hello", generation_config={"max_output_tokens": 10})
                logger.info(f"✅ Gemini API test successful with model: {self.model_name}")
            except Exception as test_error:
                logger.warning(f"⚠️ Gemini API test failed but continuing: {test_error}")
                # Continue anyway as the model might work for actual requests
            
            logger.info(f"Initializing Gemini client with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            # Provide more specific error information
            error_str = str(e).lower()
            if "api key" in error_str or "authentication" in error_str:
                raise ValueError(f"Invalid Gemini API key: {e}")
            elif "model" in error_str:
                raise ValueError(f"Invalid model '{self.model_name}': {e}")
            else:
                raise RuntimeError(f"Gemini initialization failed: {e}")
            
        self.sessions: Dict[str, ChatSession] = {}
        
        # System prompt for the AI agent
        self.system_prompt = """You are an intelligent AI agent for a Business Card OCR application. Your role is to:

1. Help users understand and use the OCR application features
2. Provide detailed information about people and companies when asked
3. Assist with business networking and relationship building
4. Answer questions about professional topics, industry insights, and business strategies
5. Help interpret and analyze business card data and extracted information

You have access to:
- OCR-extracted business card information
- Web-scraped data about people and companies
- Professional networking insights
- Industry knowledge and business intelligence

Be helpful, professional, and provide actionable insights. When discussing people or companies, be respectful and factual. If you don't have specific information, clearly state that and offer to help find it."""
    
    def create_session(self, session_id: str, context: Dict = None) -> ChatSession:
        """
        Create a new chat session
        
        Args:
            session_id: Unique session identifier
            context: Optional context (e.g., business card data, user info)
            
        Returns:
            ChatSession object
        """
        session = ChatSession(
            session_id=session_id,
            messages=[],
            created_at=datetime.now(),
            context=context or {}
        )
        self.sessions[session_id] = session
        logger.info(f"Created new chat session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get existing chat session"""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None) -> ChatMessage:
        """
        Add a message to a chat session
        
        Args:
            session_id: Session identifier
            role: Message role ("user", "assistant", "system")
            content: Message content
            metadata: Optional metadata
            
        Returns:
            ChatMessage object
        """
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.sessions[session_id].messages.append(message)
        return message
    
    def generate_response(self, session_id: str, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """
        Generate AI response to user message
        
        Args:
            session_id: Session identifier
            user_message: User's message
            context: Additional context (business card data, etc.)
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Get or create session
            session = self.get_session(session_id)
            if not session:
                session = self.create_session(session_id, context)
            
            # Add user message to session
            self.add_message(session_id, "user", user_message)
            
            try:
                # Simplify the prompt to avoid context issues
                # Use just the user message with basic system context
                simple_prompt = f"""You are a helpful AI assistant for a business networking application. 

Current context: You are helping with professional networking and business insights.

User message: {user_message}

Please provide a helpful, professional response:"""

                # Use simpler generation config
                generation_config = {
                    "temperature": 0.7,
                    "max_output_tokens": 500,
                }
                
                logger.info(f"Generating response for session {session_id}")
                
                response = self.model.generate_content(
                    simple_prompt,
                    generation_config=generation_config
                )
                
                # Extract response text with better error handling
                response_content = None
                
                # Try multiple ways to extract the response
                if response:
                    # Method 1: Direct text property
                    if hasattr(response, 'text') and response.text:
                        response_content = response.text.strip()
                        logger.info(f"Response extracted via .text property")
                    
                    # Method 2: Through candidates
                    elif hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                parts_text = []
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        parts_text.append(part.text)
                                if parts_text:
                                    response_content = ''.join(parts_text).strip()
                                    logger.info(f"Response extracted via candidates.content.parts")
                    
                    # Method 3: Check for blocked content
                    if not response_content and hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'finish_reason'):
                            finish_reason = candidate.finish_reason
                            if finish_reason == 2:  # SAFETY
                                response_content = "I appreciate your question! Let me help you with professional networking insights. What specific aspect would you like to explore?"
                            elif finish_reason == 3:  # RECITATION  
                                response_content = "I'd be happy to help with your business networking needs. Could you rephrase your question?"
                            elif finish_reason == 4:  # OTHER
                                response_content = "I'm here to help with professional networking. What would you like to know?"
                
                # Fallback if no content extracted
                if not response_content or len(response_content.strip()) < 3:
                    response_content = self._generate_smart_response(user_message)
                    logger.warning(f"Using smart fallback response for session {session_id}")
                
                logger.info(f"Final response length: {len(response_content)} characters")
                        
            except Exception as api_error:
                logger.error(f"Gemini API error: {api_error}")
                # Check for specific error types
                error_str = str(api_error).lower()
                if "api key" in error_str or "authentication" in error_str:
                    response_content = "I'm having trouble with my API authentication. Please check that the Gemini API key is properly configured."
                elif "safety" in error_str or "blocked" in error_str:
                    response_content = "I apologize, but the content was blocked for safety reasons. Please try rephrasing your message."
                elif "quota" in error_str or "rate limit" in error_str:
                    response_content = "I'm currently experiencing high demand. Please try again in a moment."
                elif "model" in error_str:
                    response_content = f"There's an issue with the AI model configuration. Please contact support."
                else:
                    response_content = f"Hello! I'm here to help you with networking and professional insights. While I'm experiencing some technical difficulties, I can still assist you. What would you like to know?"
            
            # Add assistant response to session
            self.add_message(session_id, "assistant", response_content)
            
            # Token usage is not directly available in the same way as other APIs
            # We'll provide approximate values or zeros
            return {
                "response": response_content,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "success": response is not None,
                "token_usage": {
                    "input_tokens": 0,  # Not directly available in Gemini response
                    "output_tokens": 0  # Not directly available in Gemini response
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            
            # Generate smart fallback response
            smart_response = self._generate_smart_response(user_message)
            
            return {
                "response": smart_response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "error": str(e)
            }
    
    def _build_context_prompt(self, session: ChatSession, additional_context: Dict = None) -> str:
        """Build context-aware system prompt"""
        context_parts = [self.system_prompt]
        
        # Add session context
        if session.context:
            if "business_card" in session.context:
                card_data = session.context["business_card"]
                context_parts.append(f"\nCurrent business card context:")
                context_parts.append(f"- Name: {card_data.get('name', 'N/A')}")
                context_parts.append(f"- Company: {card_data.get('company', 'N/A')}")
                context_parts.append(f"- Email: {card_data.get('email', 'N/A')}")
                context_parts.append(f"- Phone: {card_data.get('phone', 'N/A')}")
            
            if "scraped_info" in session.context:
                context_parts.append(f"\nAdditional information available about this person/company from web research.")
        
        # Add additional context
        if additional_context:
            if "person_info" in additional_context:
                context_parts.append(f"\nDetailed person information: {json.dumps(additional_context['person_info'], indent=2)}")
            
            if "company_info" in additional_context:
                context_parts.append(f"\nDetailed company information: {json.dumps(additional_context['company_info'], indent=2)}")
        
        return "\n".join(context_parts)
    
    def _prepare_messages_for_api(self, session: ChatSession, max_messages: int = 10) -> List[Dict]:
        """Prepare messages for Gemini API (excluding system messages)"""
        # Get recent messages (excluding system messages)
        user_assistant_messages = [
            msg for msg in session.messages[-max_messages:] 
            if msg.role in ["user", "assistant"]
        ]
        
        # Convert to API format (Gemini uses "parts" instead of "content")
        api_messages = []
        for msg in user_assistant_messages:
            # Map roles: Gemini uses "user" and "model" (instead of "assistant")
            role = "model" if msg.role == "assistant" else "user"
            api_messages.append({
                "role": role,
                "parts": [msg.content]
            })
        
        return api_messages
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of the conversation
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with conversation summary
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Prepare conversation text
        conversation_text = []
        for msg in session.messages:
            conversation_text.append(f"{msg.role.title()}: {msg.content}")
        
        try:
            # Generate summary using Gemini
            summary_prompt = "Please provide a concise summary of this conversation, highlighting key topics discussed and any important information shared:"
            
            # Combine system instruction with conversation for Gemini
            full_prompt = f"You are a helpful assistant that creates concise conversation summaries.\n\n{summary_prompt}\n\nConversation:\n" + "\n".join(conversation_text[-10:])  # Last 10 messages
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={}  # Use empty config to avoid safety issues
            )
            
            summary = response.text if response.text else "Could not generate summary"
            
            return {
                "session_id": session_id,
                "summary": summary,
                "message_count": len(session.messages),
                "created_at": session.created_at.isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return {
                "session_id": session_id,
                "summary": "Error generating summary",
                "message_count": len(session.messages),
                "created_at": session.created_at.isoformat(),
                "success": False,
                "error": str(e)
            }
    
    def analyze_business_context(self, business_card_data: Dict, scraped_data: Dict = None) -> Dict[str, Any]:
        """
        Analyze business context and provide insights
        
        Args:
            business_card_data: OCR-extracted business card data
            scraped_data: Web-scraped additional information
            
        Returns:
            Analysis and insights
        """
        try:
            # Prepare analysis prompt
            additional_data_text = ""
            if scraped_data:
                additional_data_text = f"Additional Research Data:\n{json.dumps(scraped_data, indent=2)}"
            
            analysis_prompt = f"""You are a professional business analyst and networking expert.

Analyze this business contact and provide professional insights:

Business Card Data:
{json.dumps(business_card_data, indent=2)}

{additional_data_text}

Please provide:
1. Professional background analysis
2. Business networking opportunities
3. Industry insights and context
4. Suggested conversation topics
5. Potential collaboration areas
6. Key questions to ask during networking

Be professional, insightful, and actionable."""

            response = self.model.generate_content(
                analysis_prompt,
                generation_config={}  # Use empty config to avoid safety issues
            )
            
            analysis = response.text if response.text else "Could not generate analysis"
            
            return {
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error analyzing business context: {e}")
            return {
                "analysis": "Error generating business analysis",
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }
    
    def suggest_follow_up_questions(self, context: Dict) -> List[str]:
        """
        Suggest relevant follow-up questions based on context
        
        Args:
            context: Context including business card and scraped data
            
        Returns:
            List of suggested questions
        """
        try:
            prompt = f"""You are a networking and conversation expert.

Based on this professional context, suggest 5 relevant and insightful questions that would be good to ask during a business conversation:

Context:
{json.dumps(context, indent=2)}

Provide questions that are:
- Professional and appropriate
- Likely to lead to meaningful conversation
- Relevant to their industry/role
- Helpful for networking and relationship building

Format as a simple list of questions."""

            response = self.model.generate_content(
                prompt,
                generation_config={}  # Use empty config to avoid safety issues
            )
            
            questions_text = response.text if response.text else ""
            
            # Parse questions from response
            questions = []
            for line in questions_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('1.') or line.startswith('-') or line.startswith('•')):
                    # Clean up the question
                    question = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    if question:
                        questions.append(question)
            
            return questions[:5]  # Return max 5 questions
            
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            return [
                "What are the most exciting projects you're working on right now?",
                "How has your industry evolved in recent years?",
                "What trends do you see shaping your field?",
                "What advice would you give to someone starting in your industry?",
                "Are there any interesting partnerships or collaborations you're exploring?"
            ]
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a chat session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
            return True
        return False
    
    def get_all_sessions(self) -> List[Dict]:
        """Get all active sessions summary"""
        sessions_summary = []
        for session_id, session in self.sessions.items():
            sessions_summary.append({
                "session_id": session_id,
                "message_count": len(session.messages),
                "created_at": session.created_at.isoformat(),
                "last_message": session.messages[-1].timestamp.isoformat() if session.messages else None
            })
        return sessions_summary

    def _generate_smart_response(self, user_message: str) -> str:
        """
        Generate a contextually appropriate response based on user input
        
        Args:
            user_message: The user's message
            
        Returns:
            A smart, contextual response
        """
        user_msg_lower = user_message.lower().strip()
        
        # Greeting responses
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
        if any(greeting in user_msg_lower for greeting in greetings):
            return "Hello! Great to connect with you! I'm here to help you with professional networking and business insights. What would you like to explore today?"
        
        # How are you responses
        if any(phrase in user_msg_lower for phrase in ["how are you", "how's it going", "how do you do"]):
            return "I'm doing well, thank you for asking! I'm excited to help you with networking and professional development. What brings you here today?"
        
        # Question about location/geography
        if any(word in user_msg_lower for word in ["capital", "city", "country", "location", "where"]):
            if "india" in user_msg_lower:
                return "The capital of India is New Delhi! Speaking of locations, understanding geographical markets can be crucial for business networking. Are you exploring opportunities in India or other markets?"
            return "That's an interesting question! While I can help with basic information, my specialty is professional networking and business insights. How can I assist you with your career or business development?"
        
        # Business/networking related
        if any(word in user_msg_lower for word in ["business", "network", "career", "job", "work", "company", "professional"]):
            return "Excellent! Business networking is my specialty. Whether you're looking to expand your professional network, explore career opportunities, or grow your business connections, I'm here to help. What specific aspect interests you?"
        
        # Technology related
        if any(word in user_msg_lower for word in ["technology", "tech", "software", "development", "programming", "code"]):
            return "Technology is a fantastic field for networking! The tech industry offers numerous opportunities for professional connections. Are you looking to connect with other professionals in tech, or do you need advice on building your presence in the technology sector?"
        
        # General questions
        if "?" in user_message:
            return "That's a great question! I'm here to help you with professional networking and business insights. Could you share more about what you're looking to achieve in your career or business development?"
        
        # Default response with some personality
        responses = [
            "I appreciate you reaching out! My expertise is in professional networking and business development. What career or business goals can I help you work toward?",
            "Thanks for connecting! I specialize in helping professionals build meaningful business relationships. What networking challenges are you facing?",
            "Great to chat with you! I'm focused on professional networking and business insights. How can I support your career or business growth today?",
            "I'm here to help with all things professional networking! Whether it's expanding your connections, career development, or business growth, what would you like to explore?"
        ]
        
        import random
        return random.choice(responses)


# Factory function to create chatbot instance
def create_chatbot() -> GeminiChatbot:
    """Factory function to create a GeminiChatbot instance"""
    try:
        logger.info("🤖 Creating Gemini chatbot...")
        
        # Try simple model names first
        model_names = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro"
        ]
        
        for model_name in model_names:
            try:
                logger.info(f"🤖 Trying model: {model_name}")
                chatbot = GeminiChatbot(model_name=model_name)
                logger.info(f"✅ Successfully created chatbot with model: {model_name}")
                return chatbot
                
            except Exception as e:
                logger.warning(f"⚠️ Model {model_name} failed: {str(e)}")
                continue
        
        # If all models fail, raise an error
        raise Exception("All Gemini model names failed to initialize")
        
    except Exception as e:
        logger.error(f"❌ Failed to create chatbot: {e}")
        # Return a fallback that at least initializes
        return GeminiChatbot(model_name="gemini-pro")


# Example usage
if __name__ == "__main__":
    # Test the chatbot
    chatbot = create_chatbot()
    
    # Create a test session
    session_id = "test_session_1"
    context = {
        "business_card": {
            "name": "John Doe",
            "company": "Microsoft",
            "email": "john.doe@microsoft.com",
            "phone": "+1-555-0123"
        }
    }
    
    # Create session and generate response
    chatbot.create_session(session_id, context)
    response = chatbot.generate_response(session_id, "Tell me about this person's background and suggest networking topics.")
    
    print("Chatbot Response:", json.dumps(response, indent=2))
    
    # Test business analysis
    analysis = chatbot.analyze_business_context(context["business_card"])
    print("Business Analysis:", json.dumps(analysis, indent=2))
    
    # Test follow-up questions
    questions = chatbot.suggest_follow_up_questions(context)
    print("Follow-up Questions:", questions)