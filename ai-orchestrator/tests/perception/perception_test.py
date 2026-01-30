import pytest
from unittest.mock import MagicMock
from src.shared.event_types import EventType
from src.perception.ingestion import TwitchIngestionService
from src.perception.router import Switchboard
from src.perception.pacer import SystemPacer


TEST_SESSION_ID = "018d9f9f-0000-7000-8000-000000000000"

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def mock_error_handler():
    return MagicMock()

@pytest.fixture
def perception_stack(mock_logger, mock_error_handler):
    """Initializes the full Layer 1 stack with mocks and Session IDs."""
    
    ingestor = TwitchIngestionService(session_id=TEST_SESSION_ID)
    pacer = SystemPacer(threshold=0.1, session_id=TEST_SESSION_ID)
    router = Switchboard(logger=mock_logger, error_handler=mock_error_handler)
    
    router._dispatch_reflex = MagicMock()
    router._dispatch_deliberation = MagicMock()
    
    return ingestor, pacer, router


def test_chat_routing_happy_path(perception_stack):
    """Test that a valid chat message preserves Session ID and goes to Slow Path."""
    ingestor, _, router = perception_stack
    
    raw_chat = {"type": "PRIVMSG", "id": "test_1", "message": "Hello AI"}
    event = ingestor.normalize_packet(raw_chat)
    
    router.route(event)
    
    # Assertions
    router._dispatch_deliberation.assert_called_once()
    assert event.type == EventType.CHAT
    assert event.session_id == TEST_SESSION_ID

def test_sub_routing_fast_path(perception_stack):
    """Test that a Subscription goes to Reflex (Fast Path)."""
    ingestor, _, router = perception_stack
    
    raw_sub = {"type": "USERNOTICE", "id": "test_2", "message": "Subscribed!"}
    event = ingestor.normalize_packet(raw_sub)
    
    router.route(event)
    
    # Assertions
    router._dispatch_reflex.assert_called_once()
    assert event.type == EventType.SUB
    assert event.session_id == TEST_SESSION_ID

def test_pacer_generates_dead_air(perception_stack):
    """Test that Pacer generates an event with correct ID structure after threshold."""
    import time
    _, pacer, _ = perception_stack
    
    assert pacer.check_pulse() is None
    time.sleep(0.15) 
    event = pacer.check_pulse()
    
    assert event is not None
    assert event.type == EventType.DEAD_AIR
    assert event.session_id == TEST_SESSION_ID # Check Session ID
    
    assert isinstance(event.id, str)
    assert len(event.id) > 10 

def test_malformed_packet_resilience(perception_stack):
    """Test that bad data raises an error (which the Medic would handle)."""
    ingestor, _, _ = perception_stack
    
    with pytest.raises(ValueError):
        ingestor.normalize_packet({"garbage": "data"})