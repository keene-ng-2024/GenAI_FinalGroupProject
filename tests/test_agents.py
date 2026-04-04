"""Tests for agent roles using mock LLM responses."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import MagicMock, patch
from agents.personas import AgentRole, BaseAgent


def test_agent_role_enum():
    assert AgentRole.READER.value == "reader"
    assert AgentRole.CRITIC.value == "critic"
    assert AgentRole.AUDITOR.value == "auditor"
    assert AgentRole.SUMMARIZER.value == "summarizer"


def test_agent_role_all_values():
    roles = {r.value for r in AgentRole}
    assert roles == {"reader", "critic", "auditor", "summarizer"}


def test_base_agent_creation():
    agent = BaseAgent(
        name="TestAgent",
        role=AgentRole.CRITIC,
        system_prompt="You are a critic.",
        model="gpt-4o",
    )
    assert agent.name == "TestAgent"
    assert agent.role == AgentRole.CRITIC


def test_base_agent_has_role_field():
    agent = BaseAgent(
        name="Reader",
        role=AgentRole.READER,
        system_prompt="You are a reader.",
        model="gpt-4o",
    )
    assert hasattr(agent, "role")
    assert agent.role == AgentRole.READER


def test_mock_vertex_agent_chat():
    """Test VertexAgent.chat() with a mocked client."""
    from agents.vertex_orchestrator import VertexAgent

    mock_client = MagicMock()
    mock_client.generate_content.return_value = {
        "text": "This is a mock response.",
        "input_tokens": 10,
        "output_tokens": 5,
    }

    with patch("agents.vertex_orchestrator.get_vertex_ai_client", return_value=mock_client):
        agent = VertexAgent(
            name="Critic",
            role=AgentRole.CRITIC,
            system_prompt="You are a critic.",
            model="gemini-2.5-flash",
            config={"vertex_ai": {"project": "test", "location": "us-central1"}},
        )
        agent.client = mock_client
        response = agent.chat("Critique this paper.")

    assert response == "This is a mock response."
    assert agent.total_input_tokens == 10
    assert agent.total_output_tokens == 5


def test_mock_vertex_agent_reset():
    from agents.vertex_orchestrator import VertexAgent

    mock_client = MagicMock()
    mock_client.generate_content.return_value = {"text": "ok", "input_tokens": 5, "output_tokens": 3}

    agent = VertexAgent(
        name="Auditor",
        role=AgentRole.AUDITOR,
        system_prompt="You are an auditor.",
        model="gemini-2.5-flash-lite",
        config={"vertex_ai": {}},
    )
    agent.client = mock_client
    agent.chat("Hello")
    assert len(agent.history) == 2  # user + model

    agent.reset()
    assert len(agent.history) == 0
