"""
Natural Language Processing service for coordinator responses.
Handles intelligent pattern matching for human-like communication.
"""
import re
import logging
from typing import Dict, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ResponseType(Enum):
    """Types of coordinator responses."""
    APPROVAL = "approval"
    DECLINE = "decline"
    MODIFICATION = "modification"
    UNKNOWN = "unknown"


@dataclass
class ProcessedResponse:
    """Structured result of response processing."""
    response_type: ResponseType
    confidence: float
    appointment_id: Optional[int] = None
    modification_reason: Optional[str] = None
    raw_message: str = ""


class CoordinatorNLPService:
    """Service for processing natural language coordinator responses."""
    
    def __init__(self):
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Initialize pattern matching rules."""
        # Approval patterns with confidence scores
        self.approval_patterns = {
            # High confidence patterns
            'approve': 0.95, 'approved': 0.95, 'yes': 0.9, 'ok': 0.85, 'okay': 0.85,
            'confirm': 0.9, 'confirmed': 0.9, 'accept': 0.85, 'good': 0.8, 'fine': 0.8,
            # Medium confidence patterns (typos)
            'aprove': 0.8, 'aproved': 0.8, 'approv': 0.75, 'aproov': 0.7,
            'ye': 0.7, 'yea': 0.7, 'yeah': 0.7, 'yep': 0.75, 'yup': 0.75,
            'oke': 0.7, 'okey': 0.7, 'k': 0.6,
            # Contextual patterns
            'looks good': 0.85, 'sounds good': 0.85, 'perfect': 0.9, 'great': 0.8
        }
        
        # Decline patterns with confidence scores
        self.decline_patterns = {
            # High confidence patterns
            'decline': 0.95, 'declined': 0.95, 'no': 0.9, 'reject': 0.9, 'rejected': 0.9,
            'cancel': 0.9, 'cancelled': 0.9, 'deny': 0.85, 'denied': 0.85,
            'refuse': 0.85, 'refused': 0.85, 'not': 0.8,
            # Medium confidence patterns (typos/variations)
            'declin': 0.8, 'declne': 0.75, 'nope': 0.85, 'nah': 0.7, 'n': 0.6
        }
        
        # Modification patterns
        self.modification_patterns = {
            'change': 0.9, 'modify': 0.95, 'different': 0.8, 'reschedule': 0.95,
            'move': 0.8, 'shift': 0.8, 'adjust': 0.85, 'update': 0.8,
            'alternative': 0.85, 'instead': 0.8
        }
    
    def process_response(self, message_text: str) -> ProcessedResponse:
        """
        Process a coordinator response and determine intent.
        
        Args:
            message_text: Raw message from coordinator
            
        Returns:
            ProcessedResponse with type, confidence, and extracted data
        """
        try:
            clean_message = message_text.lower().strip()
            
            # Extract appointment ID if present
            appointment_id = self._extract_appointment_id(message_text)
            
            # Analyze response type and confidence
            approval_score = self._calculate_pattern_score(clean_message, self.approval_patterns)
            decline_score = self._calculate_pattern_score(clean_message, self.decline_patterns)
            modification_score = self._calculate_pattern_score(clean_message, self.modification_patterns)
            
            # Determine primary intent
            max_score = max(approval_score, decline_score, modification_score)
            
            if max_score < 0.6:  # Low confidence threshold
                return ProcessedResponse(
                    response_type=ResponseType.UNKNOWN,
                    confidence=max_score,
                    raw_message=message_text
                )
            
            # Determine response type based on highest score
            if approval_score == max_score and decline_score < 0.7:  # Avoid conflicts
                return ProcessedResponse(
                    response_type=ResponseType.APPROVAL,
                    confidence=approval_score,
                    appointment_id=appointment_id,
                    raw_message=message_text
                )
            elif decline_score == max_score and approval_score < 0.7:  # Avoid conflicts
                return ProcessedResponse(
                    response_type=ResponseType.DECLINE,
                    confidence=decline_score,
                    appointment_id=appointment_id,
                    raw_message=message_text
                )
            elif modification_score == max_score:
                return ProcessedResponse(
                    response_type=ResponseType.MODIFICATION,
                    confidence=modification_score,
                    appointment_id=appointment_id,
                    modification_reason=message_text.strip(),
                    raw_message=message_text
                )
            else:
                # Ambiguous response
                return ProcessedResponse(
                    response_type=ResponseType.UNKNOWN,
                    confidence=max_score,
                    raw_message=message_text
                )
                
        except Exception as e:
            logger.error(f"Error processing coordinator response: {e}")
            return ProcessedResponse(
                response_type=ResponseType.UNKNOWN,
                confidence=0.0,
                raw_message=message_text
            )
    
    def _calculate_pattern_score(self, message: str, patterns: Dict[str, float]) -> float:
        """Calculate confidence score for pattern matching."""
        max_score = 0.0
        total_score = 0.0
        matches = 0
        
        for pattern, base_score in patterns.items():
            if pattern in message:
                # Boost score for exact word matches
                if f" {pattern} " in f" {message} " or message == pattern:
                    score = base_score
                else:
                    score = base_score * 0.8  # Partial match penalty
                
                max_score = max(max_score, score)
                total_score += score
                matches += 1
        
        # Return weighted average with preference for highest individual match
        if matches == 0:
            return 0.0
        elif matches == 1:
            return max_score
        else:
            # Multiple matches - blend max and average
            avg_score = total_score / matches
            return (max_score * 0.7) + (avg_score * 0.3)
    
    def _extract_appointment_id(self, message: str) -> Optional[int]:
        """Extract appointment ID from message if present."""
        # Look for numbers in the message
        numbers = re.findall(r'\b(\d+)\b', message)
        if numbers:
            try:
                # Return first reasonable appointment ID (1-10000 range)
                for num_str in numbers:
                    num = int(num_str)
                    if 1 <= num <= 10000:  # Reasonable appointment ID range
                        return num
            except ValueError:
                pass
        return None
    
    def get_confirmation_message(self, processed: ProcessedResponse) -> str:
        """Generate confirmation message for ambiguous responses."""
        if processed.confidence < 0.6:
            return (
                f"I'm not sure I understand your response: '{processed.raw_message}'\n\n"
                "Please respond with:\n"
                "✅ 'APPROVE' or 'YES' to confirm\n"
                "❌ 'DECLINE' or 'NO' to cancel\n"
                "📝 'CHANGE [reason]' to modify"
            )
        elif processed.response_type == ResponseType.UNKNOWN:
            return (
                f"Your response '{processed.raw_message}' is ambiguous.\n\n"
                "Please be more specific:\n"
                "✅ 'APPROVE' - Confirm appointment\n"
                "❌ 'DECLINE' - Cancel appointment\n"
                "📝 'MODIFY [reason]' - Request changes"
            )
        else:
            return f"✅ Understood: {processed.response_type.value} (confidence: {processed.confidence:.1%})"


# Global instance
coordinator_nlp_service = CoordinatorNLPService()