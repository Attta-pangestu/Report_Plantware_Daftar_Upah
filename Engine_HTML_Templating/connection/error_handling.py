#!/usr/bin/env python3
"""
Error Handling and Logging Utilities for Database Operations
Comprehensive error handling, logging, and monitoring for database operations
"""

import logging
import sys
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
import functools
import json
from pathlib import Path


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    CONNECTION = "connection"
    QUERY = "query"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    TIMEOUT = "timeout"
    PERMISSION = "permission"
    DATA_INTEGRITY = "data_integrity"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Error context information"""
    timestamp: datetime = field(default_factory=datetime.now)
    error_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN
    component: str = ""
    operation: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatabaseError:
    """Comprehensive database error information"""
    error_type: str
    message: str
    original_exception: Optional[Exception] = None
    context: Optional[ErrorContext] = None
    query: Optional[str] = None
    parameters: Optional[List[Any]] = None
    stack_trace: Optional[str] = None
    retry_count: int = 0
    is_recoverable: bool = True
    suggested_action: Optional[str] = None


class DatabaseLogger:
    """Enhanced logger for database operations"""

    def __init__(self, name: str = "database", log_level: int = logging.INFO,
                 log_file: Optional[Path] = None, enable_console: bool = True):
        """
        Initialize database logger

        Args:
            name: Logger name
            log_level: Logging level
            log_file: Optional log file path
            enable_console: Enable console logging
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.handlers.clear()  # Clear existing handlers

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Add console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Add file handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Error statistics
        self.error_counts = {}
        self.performance_log = []

    def log_query(self, query: str, params: Optional[List[Any]] = None,
                  execution_time: float = 0, success: bool = True,
                  error: Optional[Exception] = None):
        """Log query execution"""
        query_info = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'params': params,
            'execution_time': execution_time,
            'success': success
        }

        if error:
            query_info['error'] = str(error)
            self.logger.error(f"Query failed: {query[:100]}... Error: {error}")
        else:
            self.logger.info(f"Query executed in {execution_time:.3f}s: {query[:100]}...")

        # Update performance log
        self.performance_log.append(query_info)

        # Keep only last 1000 entries
        if len(self.performance_log) > 1000:
            self.performance_log = self.performance_log[-1000:]

    def log_error(self, db_error: DatabaseError):
        """Log database error"""
        self.error_counts[db_error.error_type] = self.error_counts.get(db_error.error_type, 0) + 1

        log_message = (
            f"[{db_error.severity.value.upper()}] "
            f"{db_error.error_type}: {db_error.message}"
        )

        if db_error.context:
            log_message += f" (Component: {db_error.context.component}, Operation: {db_error.context.operation})"

        if db_error.query:
            log_message += f" | Query: {db_error.query[:100]}..."

        # Log with appropriate level
        if db_error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif db_error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif db_error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        # Log stack trace if available
        if db_error.stack_trace:
            self.logger.debug(f"Stack trace:\n{db_error.stack_trace}")

    def log_performance_summary(self):
        """Log performance summary"""
        if not self.performance_log:
            self.logger.info("No performance data available")
            return

        total_queries = len(self.performance_log)
        successful_queries = sum(1 for q in self.performance_log if q['success'])
        failed_queries = total_queries - successful_queries
        total_time = sum(q['execution_time'] for q in self.performance_log)
        avg_time = total_time / total_queries if total_queries > 0 else 0

        slow_queries = [q for q in self.performance_log if q['execution_time'] > 1.0]

        self.logger.info(
            f"Performance Summary: {total_queries} queries, "
            f"{successful_queries} successful, {failed_queries} failed, "
            f"avg time: {avg_time:.3f}s, slow queries: {len(slow_queries)}"
        )

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics"""
        return {
            'error_counts': self.error_counts.copy(),
            'total_errors': sum(self.error_counts.values()),
            'most_common_error': max(self.error_counts.items(), key=lambda x: x[1])[0] if self.error_counts else None
        }


class ErrorHandler:
    """Comprehensive error handler for database operations"""

    def __init__(self, logger: Optional[DatabaseLogger] = None):
        """
        Initialize error handler

        Args:
            logger: Database logger instance
        """
        self.logger = logger or DatabaseLogger()
        self.error_handlers: Dict[str, Callable] = {}
        self.retry_policies: Dict[str, Dict] = {}
        self.error_history: List[DatabaseError] = []

        # Register default error handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default error handlers for common database errors"""
        self.register_handler("connection", self._handle_connection_error)
        self.register_handler("timeout", self._handle_timeout_error)
        self.register_handler("permission", self._handle_permission_error)
        self.register_handler("validation", self._handle_validation_error)
        self.register_handler("query", self._handle_query_error)

    def register_handler(self, error_type: str, handler: Callable[[DatabaseError], bool]):
        """
        Register error handler for specific error type

        Args:
            error_type: Type of error
            handler: Handler function that returns True if error was handled
        """
        self.error_handlers[error_type] = handler

    def set_retry_policy(self, error_type: str, max_attempts: int = 3,
                         base_delay: float = 1.0, max_delay: float = 60.0,
                         backoff_factor: float = 2.0):
        """
        Set retry policy for error type

        Args:
            error_type: Type of error
            max_attempts: Maximum retry attempts
            base_delay: Base delay between retries
            max_delay: Maximum delay
            backoff_factor: Backoff multiplication factor
        """
        self.retry_policies[error_type] = {
            'max_attempts': max_attempts,
            'base_delay': base_delay,
            'max_delay': max_delay,
            'backoff_factor': backoff_factor
        }

    def handle_error(self, error: Exception, context: Optional[ErrorContext] = None,
                     query: Optional[str] = None, params: Optional[List[Any]] = None) -> DatabaseError:
        """
        Handle database error

        Args:
            error: Original exception
            context: Error context
            query: SQL query that caused the error
            params: Query parameters

        Returns:
            DatabaseError: Processed error information
        """
        # Create database error
        db_error = self._create_database_error(error, context, query, params)

        # Log error
        self.logger.log_error(db_error)

        # Add to history
        self.error_history.append(db_error)

        # Keep only last 100 errors in history
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]

        # Apply error handler
        error_type = db_error.error_type.lower()
        if error_type in self.error_handlers:
            try:
                handled = self.error_handlers[error_type](db_error)
                if handled:
                    self.logger.info(f"Error handled by custom handler: {error_type}")
            except Exception as handler_error:
                self.logger.error(f"Error handler failed: {handler_error}")

        return db_error

    def _create_database_error(self, error: Exception, context: Optional[ErrorContext],
                             query: Optional[str], params: Optional[List[Any]]) -> DatabaseError:
        """Create DatabaseError from exception"""
        error_type = self._classify_error(error)
        severity = self._determine_severity(error, error_type)
        category = self._determine_category(error, error_type)
        is_recoverable = self._is_recoverable(error, error_type)
        suggested_action = self._suggest_action(error, error_type)

        # Extract stack trace
        stack_trace = traceback.format_exc() if isinstance(error, Exception) else None

        db_error = DatabaseError(
            error_type=error_type,
            message=str(error),
            original_exception=error,
            context=context,
            query=query,
            parameters=params,
            stack_trace=stack_trace,
            is_recoverable=is_recoverable,
            suggested_action=suggested_action
        )

        if context:
            db_error.context.severity = severity
            db_error.context.category = category

        return db_error

    def _classify_error(self, error: Exception) -> str:
        """Classify error type"""
        error_str = str(error).lower()

        if "connection" in error_str or "login failed" in error_str:
            return "connection"
        elif "timeout" in error_str or "time out" in error_str:
            return "timeout"
        elif "permission" in error_str or "access denied" in error_str or "login failed" in error_str:
            return "permission"
        elif "syntax" in error_str or "invalid" in error_str:
            return "query"
        elif "constraint" in error_str or "duplicate" in error_str:
            return "data_integrity"
        elif "driver" in error_str or "provider" in error_str:
            return "configuration"
        else:
            return "unknown"

    def _determine_severity(self, error: Exception, error_type: str) -> ErrorSeverity:
        """Determine error severity"""
        critical_types = ["connection", "permission", "system"]
        high_types = ["timeout", "data_integrity"]

        if error_type in critical_types:
            return ErrorSeverity.CRITICAL
        elif error_type in high_types:
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.MEDIUM

    def _determine_category(self, error: Exception, error_type: str) -> ErrorCategory:
        """Determine error category"""
        category_mapping = {
            "connection": ErrorCategory.CONNECTION,
            "timeout": ErrorCategory.TIMEOUT,
            "permission": ErrorCategory.PERMISSION,
            "query": ErrorCategory.QUERY,
            "data_integrity": ErrorCategory.DATA_INTEGRITY,
            "configuration": ErrorCategory.CONFIGURATION
        }

        return category_mapping.get(error_type, ErrorCategory.UNKNOWN)

    def _is_recoverable(self, error: Exception, error_type: str) -> bool:
        """Determine if error is recoverable"""
        recoverable_types = ["timeout", "connection", "system"]
        return error_type in recoverable_types

    def _suggest_action(self, error: Exception, error_type: str) -> Optional[str]:
        """Suggest action for error recovery"""
        suggestions = {
            "connection": "Check database server status and network connectivity",
            "timeout": "Optimize query or increase timeout settings",
            "permission": "Verify user has required database permissions",
            "query": "Check SQL syntax and table/column names",
            "data_integrity": "Review data constraints and business rules",
            "configuration": "Verify database connection string and driver installation"
        }

        return suggestions.get(error_type)

    def _handle_connection_error(self, db_error: DatabaseError) -> bool:
        """Handle connection errors"""
        self.logger.warning("Connection error detected - check database server availability")
        return True

    def _handle_timeout_error(self, db_error: DatabaseError) -> bool:
        """Handle timeout errors"""
        self.logger.warning("Timeout error detected - consider query optimization")
        return True

    def _handle_permission_error(self, db_error: DatabaseError) -> bool:
        """Handle permission errors"""
        self.logger.error("Permission error detected - check user database access rights")
        return True

    def _handle_validation_error(self, db_error: DatabaseError) -> bool:
        """Handle validation errors"""
        self.logger.warning("Validation error detected - check data constraints")
        return True

    def _handle_query_error(self, db_error: DatabaseError) -> bool:
        """Handle query errors"""
        self.logger.error("Query error detected - check SQL syntax")
        return True

    def get_retry_delay(self, error_type: str, attempt: int) -> float:
        """Calculate retry delay based on policy"""
        if error_type not in self.retry_policies:
            return 1.0

        policy = self.retry_policies[error_type]
        delay = policy['base_delay'] * (policy['backoff_factor'] ** (attempt - 1))
        return min(delay, policy['max_delay'])

    def should_retry(self, error_type: str, attempt: int) -> bool:
        """Determine if operation should be retried"""
        if error_type not in self.retry_policies:
            return False

        return attempt < self.retry_policies[error_type]['max_attempts']

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        error_counts = {}
        severity_counts = {}

        for error in self.error_history:
            error_counts[error.error_type] = error_counts.get(error.error_type, 0) + 1
            if error.context:
                severity = error.context.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            'total_errors': len(self.error_history),
            'error_counts': error_counts,
            'severity_counts': severity_counts,
            'most_common_error': max(error_counts.items(), key=lambda x: x[1])[0] if error_counts else None
        }


def with_error_handling(error_handler: Optional[ErrorHandler] = None,
                       component: str = "", operation: str = "",
                       user_id: Optional[str] = None):
    """
    Decorator for automatic error handling

    Args:
        error_handler: Error handler instance
        component: Component name
        operation: Operation name
        user_id: User ID
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handler = error_handler or ErrorHandler()
            logger = handler.logger

            # Create error context
            context = ErrorContext(
                component=component,
                operation=operation or func.__name__,
                user_id=user_id
            )

            try:
                # Log operation start
                logger.info(f"Starting operation: {operation or func.__name__}")

                # Execute function
                result = func(*args, **kwargs)

                # Log success
                logger.info(f"Operation completed successfully: {operation or func.__name__}")
                return result

            except Exception as e:
                # Handle error
                db_error = handler.handle_error(e, context)
                raise e

        return wrapper
    return decorator


def with_retry(error_handler: Optional[ErrorHandler] = None,
               error_types: Optional[List[str]] = None,
               component: str = "", operation: str = ""):
    """
    Decorator for automatic retry logic

    Args:
        error_handler: Error handler instance
        error_types: Error types that should trigger retry
        component: Component name
        operation: Operation name
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handler = error_handler or ErrorHandler()
            logger = handler.logger

            retry_types = error_types or ["connection", "timeout", "system"]
            attempt = 0

            while True:
                try:
                    attempt += 1
                    logger.info(f"Attempting operation: {operation or func.__name__} (attempt {attempt})")

                    result = func(*args, **kwargs)

                    if attempt > 1:
                        logger.info(f"Operation succeeded on attempt {attempt}: {operation or func.__name__}")

                    return result

                except Exception as e:
                    # Classify error
                    error_type = handler._classify_error(e)

                    # Check if error type is retryable
                    if error_type not in retry_types:
                        logger.error(f"Non-retryable error ({error_type}) in operation: {operation or func.__name__}")
                        raise e

                    # Check retry policy
                    if not handler.should_retry(error_type, attempt):
                        logger.error(f"Max retry attempts exceeded for operation: {operation or func.__name__}")
                        raise e

                    # Calculate delay
                    delay = handler.get_retry_delay(error_type, attempt)
                    logger.warning(f"Retry in {delay:.2f}s for operation: {operation or func.__name__} (error: {error_type})")

                    import time
                    time.sleep(delay)

        return wrapper
    return decorator


class AlertManager:
    """Alert manager for critical errors"""

    def __init__(self, logger: Optional[DatabaseLogger] = None):
        self.logger = logger or DatabaseLogger()
        self.alert_rules: List[Dict] = []
        self.alert_history: List[Dict] = []

    def add_alert_rule(self, name: str, condition: Callable[[DatabaseError], bool],
                      severity: ErrorSeverity, action: Callable[[DatabaseError], None]):
        """
        Add alert rule

        Args:
            name: Alert rule name
            condition: Condition function that returns True if alert should trigger
            severity: Minimum severity to trigger alert
            action: Action to take when alert triggers
        """
        self.alert_rules.append({
            'name': name,
            'condition': condition,
            'severity': severity,
            'action': action
        })

    def check_alerts(self, db_error: DatabaseError):
        """Check if any alert rules should trigger"""
        for rule in self.alert_rules:
            try:
                if (db_error.context and
                    db_error.context.severity.value >= rule['severity'].value and
                    rule['condition'](db_error)):

                    alert_info = {
                        'timestamp': datetime.now(),
                        'rule_name': rule['name'],
                        'error_type': db_error.error_type,
                        'severity': db_error.context.severity.value,
                        'message': db_error.message
                    }

                    self.alert_history.append(alert_info)
                    self.logger.error(f"ALERT TRIGGERED: {rule['name']} - {db_error.message}")

                    # Execute alert action
                    rule['action'](db_error)

            except Exception as e:
                self.logger.error(f"Alert rule failed: {rule['name']} - {e}")

    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """Get alert history"""
        return self.alert_history[-limit:]


def main():
    """Test error handling and logging"""
    print("=" * 60)
    print("ERROR HANDLING AND LOGGING TEST")
    print("=" * 60)

    try:
        # Initialize logger
        log_file = Path(__file__).parent / "test_database.log"
        logger = DatabaseLogger("test_db", log_file=log_file)
        error_handler = ErrorHandler(logger)

        print("[OK] Error handler and logger initialized")

        # Test error handling
        print("\n1. Testing error handling...")
        context = ErrorContext(component="test", operation="test_operation", user_id="test_user")

        try:
            # Simulate different types of errors
            raise ConnectionError("Database connection failed")
        except Exception as e:
            db_error = error_handler.handle_error(e, context)
            print(f"   Handled error: {db_error.error_type} - {db_error.message}")
            print(f"   Severity: {db_error.context.severity.value}")
            print(f"   Recoverable: {db_error.is_recoverable}")

        # Test alert manager
        print("\n2. Testing alert manager...")
        alert_manager = AlertManager(logger)

        def critical_error_alert(db_error: DatabaseError):
            print(f"   CRITICAL ALERT: {db_error.message}")

        alert_manager.add_alert_rule(
            "critical_connection",
            lambda e: e.error_type == "connection",
            ErrorSeverity.CRITICAL,
            critical_error_alert
        )

        # Trigger alert
        try:
            raise ConnectionError("Critical database connection lost")
        except Exception as e:
            db_error = error_handler.handle_error(e, context)
            alert_manager.check_alerts(db_error)

        # Test error statistics
        print("\n3. Error statistics:")
        stats = error_handler.get_error_statistics()
        print(f"   Total errors: {stats['total_errors']}")
        print(f"   Error counts: {stats['error_counts']}")
        print(f"   Most common error: {stats['most_common_error']}")

        # Test retry decorator
        print("\n4. Testing retry decorator...")
        attempt_count = 0

        @with_retry(error_handler, ["connection"], "test_component", "test_operation")
        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Simulated connection failure")
            return "Success after retries"

        try:
            result = failing_function()
            print(f"   Retry result: {result}")
        except Exception as e:
            print(f"   Retry failed: {e}")

        # Test performance logging
        print("\n5. Testing performance logging...")
        logger.log_query("SELECT * FROM test_table", [1, 2], 0.05, True)
        logger.log_query("SELECT * FROM slow_table", [1, 2], 1.5, False, Exception("Timeout"))
        logger.log_performance_summary()

        print("\n[OK] Error handling and logging test completed successfully")

    except Exception as e:
        print(f"\n[ERROR] Error handling test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()