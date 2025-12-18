from app.xss_security import XSSDetector

def test_detect_script_tag():
    assert XSSDetector.detect_xss_patterns('<script>alert(1)</script>') is True

def test_detect_on_event():
    assert XSSDetector.detect_xss_patterns('<div onload="evil()">') is True

def test_detect_javascript_uri():
    assert XSSDetector.detect_xss_patterns('javascript:alert(1)') is True

def test_no_false_positive():
    assert XSSDetector.detect_xss_patterns('hello world') is False