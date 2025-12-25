"""
Agent Runtime Guardrails.
Protects against runaway agents, cost explosions, and infinite loops.
"""
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from contextlib import contextmanager
from enum import Enum

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Types of agent actions."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NAVIGATE = "navigate"
    UNKNOWN = "unknown"


class GuardViolation(Exception):
    """Raised when agent violates guardrails."""
    
    def __init__(self, violation_type: str, message: str, session_id: str):
        self.violation_type = violation_type
        self.message = message
        self.session_id = session_id
        super().__init__(f"[{violation_type}] {message}")


@dataclass
class AgentStep:
    """Record of a single agent step."""
    step_id: int
    action_type: ActionType
    action_name: str
    timestamp: float
    duration_ms: float = 0.0
    success: bool = True
    metadata: dict = field(default_factory=dict)


@dataclass
class SessionStats:
    """Statistics for an agent session."""
    session_id: str
    start_time: float
    total_steps: int = 0
    read_actions: int = 0
    write_actions: int = 0
    execute_actions: int = 0
    failed_steps: int = 0
    retries: int = 0
    repeated_actions: dict = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        return time.time() - self.start_time


class AgentGuard:
    """
    Runtime protection for AI agents.
    
    Monitors agent behavior and stops runaway agents.
    
    Usage:
        guard = AgentGuard(max_steps=50, max_retries=3)
        
        with guard.session() as session:
            for step in agent.run():
                session.record_step(
                    action_type="read",
                    action_name="fetch_page",
                )
    """
    
    def __init__(
        self,
        max_steps: int = 100,
        max_retries: int = 5,
        max_repeated_action: int = 3,
        timeout_seconds: float = 300.0,
        require_approval_for_writes: bool = True,
    ):
        """
        Initialize agent guardrails.
        
        Args:
            max_steps: Maximum total steps allowed
            max_retries: Maximum consecutive retries
            max_repeated_action: Max times same action can repeat
            timeout_seconds: Session timeout
            require_approval_for_writes: Require approval for write actions
        """
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.max_repeated_action = max_repeated_action
        self.timeout_seconds = timeout_seconds
        self.require_approval_for_writes = require_approval_for_writes
        
        # Approval callback (override for custom approval flow)
        self.approval_callback: Callable[[str, dict], bool] | None = None
        
        # Active sessions
        self._sessions: dict[str, "GuardSession"] = {}
    
    @contextmanager
    def session(self, session_id: str | None = None):
        """
        Create a guarded agent session.
        
        Usage:
            with guard.session() as session:
                session.record_step(...)
        """
        import uuid
        session_id = session_id or str(uuid.uuid4())
        
        session = GuardSession(
            guard=self,
            session_id=session_id,
        )
        
        self._sessions[session_id] = session
        
        try:
            yield session
        finally:
            del self._sessions[session_id]
    
    def get_session(self, session_id: str) -> "GuardSession | None":
        """Get an active session by ID."""
        return self._sessions.get(session_id)


class GuardSession:
    """
    A guarded agent session.
    
    Tracks steps and enforces limits.
    """
    
    def __init__(self, guard: AgentGuard, session_id: str):
        self.guard = guard
        self.session_id = session_id
        self.stats = SessionStats(
            session_id=session_id,
            start_time=time.time(),
        )
        self.steps: list[AgentStep] = []
        self._last_action: str | None = None
        self._consecutive_same_action: int = 0
        self._consecutive_failures: int = 0
        self._pending_approvals: list[dict] = []
        self._stopped: bool = False
        self._stop_reason: str | None = None
    
    @property
    def is_stopped(self) -> bool:
        return self._stopped
    
    @property
    def stop_reason(self) -> str | None:
        return self._stop_reason
    
    def _check_limits(self):
        """Check all guardrail limits."""
        # Check if already stopped
        if self._stopped:
            raise GuardViolation(
                "SESSION_STOPPED",
                f"Session was stopped: {self._stop_reason}",
                self.session_id,
            )
        
        # Check step limit
        if self.stats.total_steps >= self.guard.max_steps:
            self._stop("MAX_STEPS_EXCEEDED")
            raise GuardViolation(
                "MAX_STEPS",
                f"Exceeded max steps: {self.guard.max_steps}",
                self.session_id,
            )
        
        # Check timeout
        if self.stats.duration_seconds >= self.guard.timeout_seconds:
            self._stop("TIMEOUT")
            raise GuardViolation(
                "TIMEOUT",
                f"Session timeout: {self.guard.timeout_seconds}s",
                self.session_id,
            )
        
        # Check retry limit
        if self._consecutive_failures >= self.guard.max_retries:
            self._stop("MAX_RETRIES_EXCEEDED")
            raise GuardViolation(
                "MAX_RETRIES",
                f"Too many consecutive failures: {self._consecutive_failures}",
                self.session_id,
            )
        
        # Check repeated action loop
        if self._consecutive_same_action >= self.guard.max_repeated_action:
            self._stop("LOOP_DETECTED")
            raise GuardViolation(
                "LOOP_DETECTED",
                f"Same action repeated {self._consecutive_same_action} times: {self._last_action}",
                self.session_id,
            )
    
    def _stop(self, reason: str):
        """Stop the session."""
        self._stopped = True
        self._stop_reason = reason
        logger.warning(f"[{self.session_id}] Agent stopped: {reason}")
    
    def record_step(
        self,
        action_type: str | ActionType,
        action_name: str,
        success: bool = True,
        metadata: dict | None = None,
    ) -> AgentStep:
        """
        Record an agent step and check limits.
        
        Args:
            action_type: Type of action (read, write, execute)
            action_name: Name/identifier of the action
            success: Whether the step succeeded
            metadata: Additional step metadata
            
        Returns:
            The recorded step
            
        Raises:
            GuardViolation: If limits are exceeded
        """
        # Convert string to enum
        if isinstance(action_type, str):
            action_type = ActionType(action_type.lower())
        
        # Check limits first
        self._check_limits()
        
        # Check if write action needs approval
        if action_type == ActionType.WRITE and self.guard.require_approval_for_writes:
            if not self._check_approval(action_name, metadata or {}):
                raise GuardViolation(
                    "APPROVAL_REQUIRED",
                    f"Write action requires approval: {action_name}",
                    self.session_id,
                )
        
        # Create step record
        step = AgentStep(
            step_id=self.stats.total_steps + 1,
            action_type=action_type,
            action_name=action_name,
            timestamp=time.time(),
            success=success,
            metadata=metadata or {},
        )
        
        # Update stats
        self.stats.total_steps += 1
        
        if action_type == ActionType.READ:
            self.stats.read_actions += 1
        elif action_type == ActionType.WRITE:
            self.stats.write_actions += 1
        elif action_type == ActionType.EXECUTE:
            self.stats.execute_actions += 1
        
        if not success:
            self.stats.failed_steps += 1
            self._consecutive_failures += 1
        else:
            self._consecutive_failures = 0
        
        # Track repeated actions
        action_key = f"{action_type.value}:{action_name}"
        if action_key == self._last_action:
            self._consecutive_same_action += 1
        else:
            self._consecutive_same_action = 1
        self._last_action = action_key
        
        # Track action counts
        self.stats.repeated_actions[action_key] = (
            self.stats.repeated_actions.get(action_key, 0) + 1
        )
        
        self.steps.append(step)
        
        return step
    
    def _check_approval(self, action_name: str, metadata: dict) -> bool:
        """Check if action is approved."""
        if self.guard.approval_callback:
            return self.guard.approval_callback(action_name, metadata)
        
        # Default: auto-approve if no callback set
        return True
    
    def approve_action(self, action_name: str):
        """Pre-approve an action."""
        self._pending_approvals.append({"action": action_name})
    
    def get_summary(self) -> dict:
        """Get session summary."""
        return {
            "session_id": self.session_id,
            "duration_seconds": round(self.stats.duration_seconds, 2),
            "total_steps": self.stats.total_steps,
            "read_actions": self.stats.read_actions,
            "write_actions": self.stats.write_actions,
            "execute_actions": self.stats.execute_actions,
            "failed_steps": self.stats.failed_steps,
            "is_stopped": self._stopped,
            "stop_reason": self._stop_reason,
        }


# Global guard instance
_default_guard: AgentGuard | None = None


def get_default_guard() -> AgentGuard:
    """Get or create the default agent guard."""
    global _default_guard
    if _default_guard is None:
        _default_guard = AgentGuard()
    return _default_guard
