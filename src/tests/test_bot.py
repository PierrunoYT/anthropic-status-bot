import pytest
from datetime import datetime
import sys
import os
from discord import Embed

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.embed_utils import create_status_embed, format_name, format_status, get_status_dot

def test_create_status_embed():
    """Test creation of status embed with all systems operational"""
    status_data = {
        "overall": {
            "level": "operational",
            "description": "All systems operational"
        },
        "components": {
            "Claude.ai": {
                "status": "operational"
            },
            "Console.anthropic.com": {
                "status": "operational"
            },
            "Api.anthropic.com": {
                "status": "operational"
            },
            "Api.anthropic.com - Beta Features": {
                "status": "operational"
            },
            "Anthropic.com": {
                "status": "operational"
            }
        },
        "incidents": []
    }
    
    embed = create_status_embed(status_data)
    
    # Verify embed structure
    assert isinstance(embed, Embed)
    assert embed.title == "☀️ Anthropic Status"
    assert embed.description.lower() == "○ all systems operational"
    
    # Verify components are properly formatted
    field = next((f for f in embed.fields if f.name == "components"), None)
    assert field is not None
    assert "claude.ai" in field.value.lower()
    assert "└─ operational" in field.value
    
    # Verify footer format
    assert "Last Updated" in embed.footer.text
    assert "─────────────" in embed.footer.text

def test_create_status_embed_with_incidents():
    """Test creation of status embed with active incidents"""
    status_data = {
        "overall": {
            "level": "degraded",
            "description": "Partial system outage"
        },
        "components": {
            "Claude.ai": {
                "status": "degraded"
            },
            "Console.anthropic.com": {
                "status": "operational"
            }
        },
        "incidents": [
            {
                "status": "investigating",
                "name": "API Performance Issues",
                "impact": "minor"
            }
        ]
    }
    
    embed = create_status_embed(status_data)
    
    # Verify degraded status
    assert embed.description.lower() == "○ partial system outage"
    
    # Verify incident field exists
    incident_field = next((f for f in embed.fields if f.name == "active incidents"), None)
    assert incident_field is not None
    assert "api performance issues" in incident_field.value.lower()
    assert "status: investigating" in incident_field.value.lower()

def test_formatting_functions():
    """Test helper formatting functions"""
    # Test name formatting
    assert format_name("Api.anthropic.com - Beta Features") == "api.anthropic.com (beta)"
    assert format_name("Claude.ai") == "claude.ai"
    
    # Test status formatting
    assert format_status("Operational") == "operational"
    assert format_status("Degraded Performance") == "degraded performance"
    
    # Test status dot
    assert get_status_dot("operational") == "●"
    assert get_status_dot("degraded") == "○"
    assert get_status_dot("maintenance") == "●"

def test_empty_components():
    """Test embed creation with no components"""
    status_data = {
        "overall": {
            "level": "operational",
            "description": "All systems operational"
        },
        "components": {},
        "incidents": []
    }
    
    embed = create_status_embed(status_data)
    assert isinstance(embed, Embed)
    assert embed.description.lower() == "○ all systems operational"
    
    # Verify no components field when empty
    component_field = next((f for f in embed.fields if f.name == "components"), None)
    assert component_field is None