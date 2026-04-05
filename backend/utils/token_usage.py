from pathlib import Path
import sys
import time
from flask import g

sys.path.insert(0, str(Path(__file__).parent))

from logger import setup_logging

logger = setup_logging(current_file=Path(__file__).stem)

_session_storage = {}

def get_token_usage(result):
    """Parse and return token usage from API response."""
    usage = result.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)
    token_usage=f"""
        Prompt: {prompt_tokens},
        Completion: {completion_tokens},
        Total: {total_tokens}
        """
    return token_usage, total_tokens

def get_session_id():
    """Get or create session ID from Flask request context."""
    if not hasattr(g, 'token_session_id'):
        import uuid
        g.token_session_id = str(uuid.uuid4())
        logger.info(f"Generated new session ID: {g.token_session_id}")
    return g.token_session_id

class TokenUsageTracker:
    def __init__(self):
        pass

    def start_session(self, session_id: str = None):
        """Start a NEW multi-endpoint session with a unique ID."""
        if session_id is None:
            session_id = get_session_id()

        session_state = {
            "session_id": session_id,
            "total_token_usage": 0,
            "start_time": time.time(),
            "operations": [],
            "endpoints": []
        }
        _session_storage[session_id] = session_state
        g.token_session_id = session_id
        logger.info(f"[SESSION {session_id}] New session started")
        return session_id

    def start_session_tracking(self, session_id: str = None):
        """Continue or start a session for a single endpoint call."""
        if session_id is None:
            session_id = get_session_id()

        # If session_id provided, use the server-side storage (multi-endpoint)
        if session_id in _session_storage:
            g.token_session_id = session_id
            logger.info(f"[SESSION {session_id}] Continuing existing session")
            return
        
        # Otherwise create new session
        self.start_session(session_id)

    def start_tracking(self):
        """Initialize a NEW context-local tracking (single endpoint)."""
        self.start_session()

    def add_usage(self, token_usage, context: str = "", endpoint: str = ""):
        session_id = get_session_id()

        if session_id not in _session_storage:
            logger.warning(f"[SESSION {session_id}] Session not found, creating new one")
            self.start_session(session_id)

        logger.info(f"[SESSION {session_id}] Token usage added: {token_usage} ({context})")

        tracker_state = _session_storage[session_id]
        tracker_state["total_token_usage"] += token_usage
        tracker_state['operations'].append({
            'context': context,
            'tokens': token_usage,
            'timestamp': time.asctime(time.localtime(time.time())),
            'endpoint': endpoint
        })
        logger.info(f"[SESSION {session_id}] Updated tracker state: {tracker_state['operations'][-1]}")

    def end_tracking(self, session_id: str = None):
        if session_id is None:
            session_id = get_session_id()

        if session_id not in _session_storage:
            logger.warning(f"[SESSION {session_id}] Session not found")
            return
        
        tracker_state = _session_storage[session_id]
        end_time = time.time()
        total_tokens = tracker_state['total_token_usage']
        elapsed_time = end_time - tracker_state['start_time']
        
        logger.info("=" * 60)
        logger.info("TOKEN USAGE SUMMARY")
        logger.info("=" * 60)

        for op in tracker_state['operations']:
            endpoint = op.get('endpoint', 'unknown')
            logger.info(f"  [{endpoint}] {op['context']}: {op['tokens']} tokens")
        
        logger.info(f"TOTAL: {total_tokens} tokens")
        logger.info(f"TIME: {elapsed_time:.2f}s")
        logger.info("=" * 60)
        
        # Clean up session storage
        if session_id in _session_storage:
            del _session_storage[session_id]
    
    def get_current_usage(self, session_id: str = None):
        """Get current accumulated token usage without ending session."""
        if session_id is None:
            session_id = get_session_id()
        
        if session_id not in _session_storage:
            return 0
        
        return _session_storage[session_id]['total_token_usage']

token_tracker = TokenUsageTracker()