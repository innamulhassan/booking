"""
Centralized error handling service for the therapy booking system.
Provides structured error handling, logging, and recovery mechanisms.
"""
import logging
import traceback
from typing import Dict, Optional, Any, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import asyncio


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors."""
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    WEBHOOK = "webhook"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    NETWORK = "network"
    AUTHENTICATION = "authentication"


@dataclass
class ErrorContext:
    """Context information for an error."""
    user_phone: Optional[str] = None
    appointment_id: Optional[int] = None
    endpoint: Optional[str] = None
    request_data: Optional[Dict] = None
    session_id: Optional[str] = None
    user_action: Optional[str] = None


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""
    id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    traceback: Optional[str] = None
    context: Optional[ErrorContext] = None
    timestamp: datetime = None
    resolved: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ErrorHandler:
    """Centralized error handling service."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._error_history: List[ErrorRecord] = []
        self._error_patterns = {}
        self._recovery_strategies = self._setup_recovery_strategies()
    
    def _setup_recovery_strategies(self) -> Dict:
        """Setup automatic recovery strategies for common errors."""
        return {
            ErrorCategory.DATABASE: {
                'retry_count': 3,
                'retry_delay': 1.0,
                'fallback_action': self._database_fallback
            },
            ErrorCategory.EXTERNAL_API: {
                'retry_count': 2,
                'retry_delay': 2.0,
                'fallback_action': self._api_fallback
            },
            ErrorCategory.NETWORK: {
                'retry_count': 3,
                'retry_delay': 0.5,
                'fallback_action': self._network_fallback
            }
        }
    
    async def handle_error(
        self, 
        error: Exception, 
        category: ErrorCategory, 
        severity: ErrorSeverity,
        context: Optional[ErrorContext] = None,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle an error with automatic recovery attempts.
        
        Args:
            error: The exception that occurred
            category: Category of the error
            severity: Severity level
            context: Additional context information
            user_message: Custom user-friendly message
            
        Returns:
            Dict with handling results and suggested actions
        """
        try:
            # Generate error ID
            error_id = f"{category.value}_{int(datetime.now().timestamp())}"
            
            # Create error record
            error_record = ErrorRecord(
                id=error_id,
                category=category,
                severity=severity,
                message=str(error),
                details=self._extract_error_details(error),
                traceback=traceback.format_exc() if error else None,
                context=context
            )
            
            # Log error
            self._log_error(error_record)
            
            # Store in history
            self._error_history.append(error_record)
            
            # Attempt recovery
            recovery_result = await self._attempt_recovery(error_record)
            
            # Generate user response
            user_response = self._generate_user_response(error_record, user_message, recovery_result)
            
            # Send notifications if critical
            if severity == ErrorSeverity.CRITICAL:
                await self._notify_administrators(error_record)
            
            return {
                'error_id': error_id,
                'handled': True,
                'severity': severity.value,
                'category': category.value,
                'user_message': user_response,
                'recovery_attempted': recovery_result['attempted'],
                'recovery_successful': recovery_result['successful'],
                'suggested_actions': recovery_result['suggested_actions']
            }
            
        except Exception as handling_error:
            # Fallback error handling
            self.logger.critical(f"Error in error handler: {handling_error}")
            return {
                'error_id': 'system_error',
                'handled': False,
                'user_message': "I encountered a technical issue. Please try again in a moment.",
                'recovery_attempted': False,
                'recovery_successful': False
            }
    
    def _extract_error_details(self, error: Exception) -> str:
        """Extract detailed information from an exception."""
        details = []
        
        # Error type and message
        details.append(f"Type: {type(error).__name__}")
        details.append(f"Message: {str(error)}")
        
        # Additional attributes
        if hasattr(error, 'code'):
            details.append(f"Code: {error.code}")
        if hasattr(error, 'status_code'):
            details.append(f"Status: {error.status_code}")
        
        return "\n".join(details)
    
    def _log_error(self, error_record: ErrorRecord):
        """Log error with appropriate level."""
        log_message = f"[{error_record.id}] {error_record.category.value}: {error_record.message}"
        
        if error_record.context:
            if error_record.context.user_phone:
                log_message += f" | User: {error_record.context.user_phone}"
            if error_record.context.appointment_id:
                log_message += f" | Appointment: {error_record.context.appointment_id}"
        
        if error_record.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_record.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_record.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Log full traceback for debugging
        if error_record.traceback:
            self.logger.debug(f"Traceback for {error_record.id}:\n{error_record.traceback}")
    
    async def _attempt_recovery(self, error_record: ErrorRecord) -> Dict:
        """Attempt automatic recovery based on error type."""
        strategy = self._recovery_strategies.get(error_record.category)
        
        if not strategy:
            return {
                'attempted': False,
                'successful': False,
                'suggested_actions': ['Manual intervention required']
            }
        
        # Attempt recovery with retries
        for attempt in range(strategy['retry_count']):
            try:
                await asyncio.sleep(strategy['retry_delay'])
                
                # Call recovery function
                recovery_successful = await strategy['fallback_action'](error_record)
                
                if recovery_successful:
                    error_record.resolved = True
                    self.logger.info(f"Recovery successful for {error_record.id} on attempt {attempt + 1}")
                    return {
                        'attempted': True,
                        'successful': True,
                        'suggested_actions': ['Issue automatically resolved']
                    }
                    
            except Exception as recovery_error:
                self.logger.warning(f"Recovery attempt {attempt + 1} failed for {error_record.id}: {recovery_error}")
        
        # All recovery attempts failed
        return {
            'attempted': True,
            'successful': False,
            'suggested_actions': self._get_manual_recovery_steps(error_record.category)
        }
    
    async def _database_fallback(self, error_record: ErrorRecord) -> bool:
        """Attempt database recovery."""
        try:
            # Test database connection
            from app.core.database import get_db_connection
            
            async with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
                
        except Exception:
            return False
    
    async def _api_fallback(self, error_record: ErrorRecord) -> bool:
        """Attempt API recovery."""
        # For now, just return False - could implement API health checks
        return False
    
    async def _network_fallback(self, error_record: ErrorRecord) -> bool:
        """Attempt network recovery."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('https://www.google.com', timeout=5) as response:
                    return response.status == 200
        except Exception:
            return False
    
    def _get_manual_recovery_steps(self, category: ErrorCategory) -> List[str]:
        """Get manual recovery steps for different error categories."""
        steps = {
            ErrorCategory.DATABASE: [
                "Check database connection",
                "Verify database credentials",
                "Restart database service if needed"
            ],
            ErrorCategory.EXTERNAL_API: [
                "Check API endpoint status",
                "Verify API credentials",
                "Contact API provider if issues persist"
            ],
            ErrorCategory.WEBHOOK: [
                "Check webhook endpoint configuration",
                "Verify webhook secret/authentication",
                "Test webhook endpoint manually"
            ],
            ErrorCategory.VALIDATION: [
                "Review input data format",
                "Check validation rules",
                "Update validation logic if needed"
            ]
        }
        return steps.get(category, ["Contact system administrator"])
    
    def _generate_user_response(self, error_record: ErrorRecord, custom_message: str, recovery_result: Dict) -> str:
        """Generate user-friendly error message."""
        if custom_message:
            return custom_message
        
        if recovery_result['successful']:
            return "I encountered a small hiccup but everything is working perfectly now! Please try your request again."
        
        # Default messages by severity
        messages = {
            ErrorSeverity.LOW: "I'm experiencing a minor technical issue. Please try again in a moment.",
            ErrorSeverity.MEDIUM: "I'm having some technical difficulties right now. Let me try to help you in a different way.",
            ErrorSeverity.HIGH: "I'm experiencing technical problems that are preventing me from completing your request. Please try again shortly.",
            ErrorSeverity.CRITICAL: "I'm currently experiencing significant technical issues. Our team has been notified and will resolve this quickly. Please try again in a few minutes."
        }
        
        return messages.get(error_record.severity, "I encountered an unexpected issue. Please try again.")
    
    async def _notify_administrators(self, error_record: ErrorRecord):
        """Notify administrators of critical errors."""
        try:
            # Could send emails, Slack messages, etc.
            self.logger.critical(f"CRITICAL ERROR ALERT: {error_record.id}")
            # Implementation depends on notification preferences
            
        except Exception as notify_error:
            self.logger.error(f"Failed to notify administrators: {notify_error}")
    
    def get_error_summary(self, hours: int = 24) -> Dict:
        """Get error summary for the specified time period."""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        recent_errors = [
            error for error in self._error_history 
            if error.timestamp.timestamp() > cutoff_time
        ]
        
        # Group by category and severity
        summary = {}
        for error in recent_errors:
            category = error.category.value
            severity = error.severity.value
            
            if category not in summary:
                summary[category] = {}
            if severity not in summary[category]:
                summary[category][severity] = 0
            
            summary[category][severity] += 1
        
        return {
            'total_errors': len(recent_errors),
            'by_category': summary,
            'resolved_count': len([e for e in recent_errors if e.resolved])
        }
    
    def clear_old_errors(self, days: int = 7):
        """Clear error history older than specified days."""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        self._error_history = [
            error for error in self._error_history
            if error.timestamp.timestamp() > cutoff_time
        ]


# Convenience functions for common error scenarios
async def handle_database_error(error: Exception, context: Optional[ErrorContext] = None) -> Dict:
    """Handle database-related errors."""
    return await error_handler.handle_error(
        error, 
        ErrorCategory.DATABASE, 
        ErrorSeverity.HIGH, 
        context,
        "I'm having trouble accessing the booking system right now. Let me try that again for you."
    )

async def handle_api_error(error: Exception, context: Optional[ErrorContext] = None) -> Dict:
    """Handle external API errors."""
    return await error_handler.handle_error(
        error, 
        ErrorCategory.EXTERNAL_API, 
        ErrorSeverity.MEDIUM, 
        context,
        "I'm experiencing a temporary issue with one of our services. Please give me a moment to resolve this."
    )

async def handle_webhook_error(error: Exception, context: Optional[ErrorContext] = None) -> Dict:
    """Handle webhook processing errors."""
    return await error_handler.handle_error(
        error, 
        ErrorCategory.WEBHOOK, 
        ErrorSeverity.MEDIUM, 
        context
    )

async def handle_validation_error(error: Exception, context: Optional[ErrorContext] = None) -> Dict:
    """Handle validation errors."""
    return await error_handler.handle_error(
        error, 
        ErrorCategory.VALIDATION, 
        ErrorSeverity.LOW, 
        context,
        "I need a bit more information to help you with that. Could you please provide the details in a different format?"
    )

# Global instance
error_handler = ErrorHandler()