from status_parser import StatusParser

def test_all_operational():
    text_content = """☀️ Anthropic Status
🟢 All systems operational
components
🟢 Claude.ai
└─ Operational
🟢 Console.anthropic.com
└─ Operational
🟢 Api.anthropic.com
└─ Operational
🟢 Api.anthropic.com - Beta Features
└─ Operational
🟢 Anthropic.com
└─ Operational
_____________________
Last Updated • heute um 20:26 Uhr"""

    parser = StatusParser()
    result = parser.parse_status_page(text_content, is_html=False)
    
    print("\nDebug - Overall status:")
    print(f"Description: {result['overall']['description']}")
    print(f"Level: {result['overall']['level']}")
    
    print("\nDebug - Components:")
    for name, component in result['components'].items():
        print(f"{name}: {component['status']}")
    
    assert result['overall']['description'] == '🟢 All systems operational'
    assert result['overall']['level'] == 'operational'
    
    for component in result['components'].values():
        assert component['status'] == 'operational'
    
    print("✅ All operational test passed!")

def test_partial_degraded():
    text_content = """☀️ Anthropic Status
🟡 Some systems experiencing degraded performance
components
🟡 Claude.ai
└─ Degraded Performance
🟢 Console.anthropic.com
└─ Operational
🟢 Api.anthropic.com
└─ Operational
🟡 Api.anthropic.com - Beta Features
└─ Degraded Performance
🟢 Anthropic.com
└─ Operational
_____________________
Last Updated • heute um 20:26 Uhr"""

    parser = StatusParser()
    result = parser.parse_status_page(text_content, is_html=False)
    
    print("\nDebug - Overall status:")
    print(f"Description: {result['overall']['description']}")
    print(f"Level: {result['overall']['level']}")
    
    print("\nDebug - Components:")
    for name, component in result['components'].items():
        print(f"{name}: {component['status']}")
    
    assert result['overall']['level'] == 'degraded'
    
    degraded_components = ['Claude.ai', 'Api.anthropic.com - Beta Features']
    operational_components = ['Console.anthropic.com', 'Api.anthropic.com', 'Anthropic.com']
    
    for name, component in result['components'].items():
        if name in degraded_components:
            assert component['status'] == 'degraded', f"Expected {name} to be degraded"
        elif name in operational_components:
            assert component['status'] == 'operational', f"Expected {name} to be operational"
    
    print("✅ Partial degraded test passed!")

def test_major_outage():
    text_content = """☀️ Anthropic Status
🔴 Major system outage
components
🔴 Claude.ai
└─ Major Outage
🔴 Console.anthropic.com
└─ Major Outage
🔴 Api.anthropic.com
└─ Major Outage
🟡 Api.anthropic.com - Beta Features
└─ Degraded Performance
🟢 Anthropic.com
└─ Operational
_____________________
Last Updated • heute um 20:26 Uhr"""

    parser = StatusParser()
    result = parser.parse_status_page(text_content, is_html=False)
    
    print("\nDebug - Overall status:")
    print(f"Description: {result['overall']['description']}")
    print(f"Level: {result['overall']['level']}")
    
    print("\nDebug - Components:")
    for name, component in result['components'].items():
        print(f"{name}: {component['status']}")
    
    assert result['overall']['level'] == 'major_outage'
    
    outage_components = ['Claude.ai', 'Console.anthropic.com', 'Api.anthropic.com']
    degraded_components = ['Api.anthropic.com - Beta Features']
    operational_components = ['Anthropic.com']
    
    for name, component in result['components'].items():
        if name in outage_components:
            assert component['status'] == 'outage', f"Expected {name} to be in outage"
        elif name in degraded_components:
            assert component['status'] == 'degraded', f"Expected {name} to be degraded"
        elif name in operational_components:
            assert component['status'] == 'operational', f"Expected {name} to be operational"
    
    print("✅ Major outage test passed!")

def run_all_tests():
    print("\nRunning all status tests...\n")
    test_all_operational()
    test_partial_degraded()
    test_major_outage()
    print("\n✨ All status tests passed successfully!")

if __name__ == '__main__':
    run_all_tests()