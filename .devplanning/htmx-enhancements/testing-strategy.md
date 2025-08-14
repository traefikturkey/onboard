# HTMX Enhancement Testing Strategy

This document outlines the comprehensive testing approach for the HTMX 2.0 enhancements to ensure reliability, performance, and user experience improvements.

## Testing Philosophy

- **Progressive Enhancement**: Each feature should gracefully degrade
- **Zero Regression**: Existing functionality must remain intact
- **Performance First**: Improvements should measurably enhance performance
- **User-Centric**: Focus on actual user experience improvements

## Test Categories

### 1. Unit Tests

#### 1.1 Server-side Route Tests
```python
# tests/app/test_htmx_routes.py
import pytest
from app.app import app

class TestHTMXRoutes:
    def test_tab_route_returns_partial_for_htmx(self):
        """Test that tab routes return partial content for HTMX requests"""
        with app.test_client() as client:
            response = client.get('/tab/home', 
                                headers={'HX-Request': 'true'})
            assert response.status_code == 200
            # Should not contain full HTML structure
            assert '<html>' not in response.data.decode()
            assert '<body>' not in response.data.decode()
            # Should contain content
            assert 'class="row"' in response.data.decode()

    def test_tab_route_returns_full_page_for_normal_request(self):
        """Test that tab routes return full page for normal requests"""
        with app.test_client() as client:
            response = client.get('/tab/home')
            assert response.status_code == 200
            # Should contain full HTML structure
            assert '<html>' in response.data.decode()
            assert '<body>' in response.data.decode()

    def test_tab_content_includes_head_tags(self):
        """Test that partial tab content includes head tags for head-support"""
        with app.test_client() as client:
            response = client.get('/tab/home', 
                                headers={'HX-Request': 'true'})
            content = response.data.decode()
            assert '<title>' in content
            assert 'home' in content.lower()
```

#### 1.2 Template Rendering Tests
```python
# tests/app/test_htmx_templates.py
def test_widget_template_has_preload_attributes():
    """Test that widget templates include preload extension"""
    # Mock widget data
    widget = MockWidget(type='feed', hx_get='/feed/123')
    
    rendered = render_template('widget.html', widget=widget)
    
    assert 'hx-ext="preload' in rendered
    assert 'preload="mouseenter"' in rendered

def test_tab_navigation_has_htmx_attributes():
    """Test that tab navigation includes HTMX attributes"""
    layout = MockLayout(tabs=[MockTab('home'), MockTab('work')])
    
    rendered = render_template('index.html', layout=layout)
    
    assert 'hx-get="/tab/' in rendered
    assert 'hx-target="#main-content"' in rendered
    assert 'hx-swap="innerHTML transition:true"' in rendered
```

### 2. Integration Tests

#### 2.1 HTMX Extension Loading Tests
```python
# tests/integration/test_htmx_extensions.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestHTMXExtensions:
    @pytest.fixture
    def driver(self):
        driver = webdriver.Chrome()
        yield driver
        driver.quit()

    def test_preload_extension_loads(self, driver):
        """Test that preload extension is loaded and functional"""
        driver.get('http://localhost:5000')
        
        # Check that htmx and preload extension are loaded
        script_result = driver.execute_script("""
            return window.htmx && 
                   window.htmx.config && 
                   htmx.config.extensions && 
                   htmx.config.extensions.includes('preload');
        """)
        assert script_result is True

    def test_widget_preloads_on_hover(self, driver):
        """Test that widgets preload content on hover"""
        driver.get('http://localhost:5000')
        
        # Find a widget with loading state
        widget = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.box[hx-get]'))
        )
        
        # Track network requests
        driver.execute_script("""
            window.preloadRequests = [];
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                window.preloadRequests.push(args[0]);
                return originalFetch.apply(this, args);
            };
        """)
        
        # Hover over widget
        webdriver.ActionChains(driver).move_to_element(widget).perform()
        
        # Wait a moment for preload
        time.sleep(0.5)
        
        # Check if preload request was made
        requests = driver.execute_script("return window.preloadRequests;")
        assert len(requests) > 0

    def test_view_transitions_work(self, driver):
        """Test that view transitions work between tabs"""
        # Skip if view transitions not supported
        supports_transitions = driver.execute_script("""
            return 'startViewTransition' in document;
        """)
        
        if not supports_transitions:
            pytest.skip("Browser doesn't support View Transitions")
        
        driver.get('http://localhost:5000')
        
        # Find tab links
        tabs = driver.find_elements(By.CSS_SELECTOR, '.tab-bar a[hx-get]')
        assert len(tabs) > 1
        
        # Click on a different tab
        original_content = driver.find_element(By.ID, 'main-content').text
        tabs[1].click()
        
        # Wait for transition to complete
        WebDriverWait(driver, 5).until(
            lambda d: d.find_element(By.ID, 'main-content').text != original_content
        )
        
        # Verify content changed
        new_content = driver.find_element(By.ID, 'main-content').text
        assert new_content != original_content
```

#### 2.2 Alpine.js State Preservation Tests
```python
def test_alpine_state_preserved_with_morphing(self, driver):
    """Test that Alpine.js state is preserved during HTMX swaps"""
    driver.get('http://localhost:5000')
    
    # Find widget with Alpine state
    widget_item = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'li[x-data]'))
    )
    
    # Click to open summary
    widget_item.click()
    
    # Verify summary is open
    summary = driver.find_element(By.CSS_SELECTOR, '.summary[x-show]')
    assert summary.is_displayed()
    
    # Trigger a widget refresh (simulate)
    driver.execute_script("""
        htmx.trigger(arguments[0], 'refresh');
    """, widget_item.find_element(By.XPATH, './parent::*'))
    
    # Wait for refresh to complete
    time.sleep(1)
    
    # Verify summary is still open (state preserved)
    summary = driver.find_element(By.CSS_SELECTOR, '.summary[x-show]')
    assert summary.is_displayed()
```

### 3. Performance Tests

#### 3.1 Loading Performance Tests
```python
# tests/performance/test_loading_performance.py
import time
from selenium.webdriver.support.ui import WebDriverWait

class TestLoadingPerformance:
    def test_perceived_loading_time_improvement(self, driver):
        """Test that perceived loading time is improved with preloading"""
        driver.get('http://localhost:5000')
        
        # Measure time without preload (disable preload first)
        driver.execute_script("""
            // Disable preload for baseline measurement
            document.querySelectorAll('[preload]').forEach(el => {
                el.removeAttribute('preload');
            });
        """)
        
        widget = driver.find_element(By.CSS_SELECTOR, '.box[hx-get]')
        
        # Measure direct click time
        start_time = time.time()
        widget.click()
        WebDriverWait(driver, 10).until(
            lambda d: 'Loading...' not in widget.text
        )
        direct_load_time = time.time() - start_time
        
        # Refresh page to test with preload
        driver.refresh()
        widget = driver.find_element(By.CSS_SELECTOR, '.box[hx-get]')
        
        # Hover to trigger preload
        webdriver.ActionChains(driver).move_to_element(widget).perform()
        time.sleep(0.2)  # Allow preload to complete
        
        # Measure preloaded click time
        start_time = time.time()
        widget.click()
        WebDriverWait(driver, 10).until(
            lambda d: 'Loading...' not in widget.text
        )
        preload_time = time.time() - start_time
        
        # Preloaded should be significantly faster
        improvement = (direct_load_time - preload_time) / direct_load_time
        assert improvement > 0.5  # At least 50% improvement

    def test_transition_smoothness(self, driver):
        """Test that transitions maintain 60fps"""
        if not driver.execute_script("return 'startViewTransition' in document;"):
            pytest.skip("View Transitions not supported")
        
        driver.get('http://localhost:5000')
        
        # Enable performance monitoring
        driver.execute_script("""
            window.frameDrops = 0;
            window.frameCount = 0;
            let lastTime = performance.now();
            
            function countFrames() {
                const now = performance.now();
                const delta = now - lastTime;
                lastTime = now;
                
                window.frameCount++;
                if (delta > 16.67) { // More than 16.67ms = dropped frame
                    window.frameDrops++;
                }
                
                requestAnimationFrame(countFrames);
            }
            countFrames();
        """)
        
        # Trigger transition
        tab = driver.find_element(By.CSS_SELECTOR, '.tab-bar a[hx-get]:nth-child(2)')
        tab.click()
        
        # Wait for transition to complete
        time.sleep(1)
        
        # Check frame performance
        frame_data = driver.execute_script("""
            return {
                frameCount: window.frameCount,
                frameDrops: window.frameDrops
            };
        """)
        
        # Should maintain good frame rate (less than 10% drops)
        frame_drop_rate = frame_data['frameDrops'] / frame_data['frameCount']
        assert frame_drop_rate < 0.1
```

#### 3.2 Memory Leak Tests
```python
def test_no_memory_leaks_with_extended_usage(self, driver):
    """Test that extended usage doesn't cause memory leaks"""
    driver.get('http://localhost:5000')
    
    # Measure initial memory
    initial_memory = driver.execute_script("""
        return performance.memory ? performance.memory.usedJSHeapSize : 0;
    """)
    
    # Simulate heavy usage - navigate between tabs many times
    tabs = driver.find_elements(By.CSS_SELECTOR, '.tab-bar a[hx-get]')
    
    for i in range(50):  # 50 tab switches
        tab_index = i % len(tabs)
        tabs[tab_index].click()
        time.sleep(0.1)  # Brief pause
    
    # Force garbage collection if available
    driver.execute_script("""
        if (window.gc) {
            window.gc();
        }
    """)
    
    # Measure final memory
    final_memory = driver.execute_script("""
        return performance.memory ? performance.memory.usedJSHeapSize : 0;
    """)
    
    # Memory growth should be reasonable (less than 50% increase)
    if initial_memory > 0:
        memory_growth = (final_memory - initial_memory) / initial_memory
        assert memory_growth < 0.5
```

### 4. Cross-browser Tests

#### 4.1 Feature Detection Tests
```python
# tests/cross_browser/test_feature_support.py
@pytest.mark.parametrize("browser", ["chrome", "firefox", "safari"])
def test_graceful_degradation(browser, driver_factory):
    """Test graceful degradation across browsers"""
    driver = driver_factory(browser)
    driver.get('http://localhost:5000')
    
    # Test basic functionality works regardless of feature support
    tabs = driver.find_elements(By.CSS_SELECTOR, '.tab-bar a')
    assert len(tabs) > 0
    
    # Click should work even without view transitions
    tabs[1].click()
    
    # Content should update
    WebDriverWait(driver, 10).until(
        lambda d: d.current_url.endswith(tabs[1].get_attribute('href').split('/')[-1])
    )

def test_progressive_enhancement(driver):
    """Test that features work even when JavaScript is disabled"""
    # Disable JavaScript
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-javascript')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('http://localhost:5000')
    
    # Basic navigation should still work
    tabs = driver.find_elements(By.CSS_SELECTOR, '.tab-bar a')
    tabs[1].click()
    
    # Should navigate to new page (traditional page load)
    assert tabs[1].get_attribute('href') in driver.current_url
    
    driver.quit()
```

### 5. Accessibility Tests

#### 5.1 Screen Reader Tests
```python
# tests/accessibility/test_accessibility.py
def test_loading_states_have_aria_labels(driver):
    """Test that loading states are accessible to screen readers"""
    driver.get('http://localhost:5000')
    
    widget = driver.find_element(By.CSS_SELECTOR, '.box[hx-get]')
    
    # Trigger loading state
    driver.execute_script("""
        arguments[0].classList.add('widget-loading');
        arguments[0].setAttribute('aria-busy', 'true');
        arguments[0].setAttribute('aria-live', 'polite');
    """, widget)
    
    # Check ARIA attributes
    assert widget.get_attribute('aria-busy') == 'true'
    assert widget.get_attribute('aria-live') == 'polite'

def test_focus_management_during_transitions(driver):
    """Test that focus is properly managed during view transitions"""
    driver.get('http://localhost:5000')
    
    # Focus on a tab
    tab = driver.find_element(By.CSS_SELECTOR, '.tab-bar a[hx-get]')
    tab.click()
    
    # Focus should be maintained or logically transferred
    active_element = driver.switch_to.active_element
    assert active_element is not None
    
    # Focus should be on a focusable element
    tag_name = active_element.tag_name.lower()
    assert tag_name in ['a', 'button', 'input', 'textarea', 'select']
```

### 6. Error Handling Tests

#### 6.1 Network Error Tests
```python
def test_handles_network_errors_gracefully(driver):
    """Test that network errors are handled gracefully"""
    driver.get('http://localhost:5000')
    
    # Simulate network error
    driver.execute_script("""
        // Mock fetch to fail
        window.originalFetch = window.fetch;
        window.fetch = function() {
            return Promise.reject(new Error('Network error'));
        };
    """)
    
    # Try to trigger a request
    widget = driver.find_element(By.CSS_SELECTOR, '.box[hx-get]')
    widget.click()
    
    # Should handle error gracefully (no console errors, fallback content)
    WebDriverWait(driver, 5).until(
        lambda d: 'error' in d.find_element(By.CSS_SELECTOR, '.box').text.lower() or
                  'loading' not in d.find_element(By.CSS_SELECTOR, '.box').text.lower()
    )

def test_server_error_handling(driver):
    """Test handling of server errors (404, 500, etc.)"""
    driver.get('http://localhost:5000')
    
    # Create widget with invalid URL
    driver.execute_script("""
        const widget = document.querySelector('.box[hx-get]');
        if (widget) {
            widget.setAttribute('hx-get', '/nonexistent-endpoint');
        }
    """)
    
    widget = driver.find_element(By.CSS_SELECTOR, '.box[hx-get]')
    widget.click()
    
    # Should handle 404 gracefully
    time.sleep(2)
    
    # Check that error is handled (widget should show error state or remain unchanged)
    widget_text = widget.text.lower()
    assert 'loading' not in widget_text  # Loading should stop
```

## Test Automation

### Continuous Integration
```yaml
# .github/workflows/htmx-tests.yml
name: HTMX Enhancement Tests

on:
  push:
    branches: [ main, htmx-enhancements ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      selenium:
        image: selenium/standalone-chrome:latest
        ports:
          - 4444:4444

    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.12
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install selenium pytest pytest-cov
    
    - name: Start application
      run: |
        python run.py &
        sleep 10  # Wait for app to start
    
    - name: Run unit tests
      run: pytest tests/app/test_htmx_*.py -v
    
    - name: Run integration tests
      run: pytest tests/integration/test_htmx_*.py -v
    
    - name: Run performance tests
      run: pytest tests/performance/ -v
    
    - name: Run accessibility tests
      run: pytest tests/accessibility/ -v
```

### Performance Monitoring
```python
# scripts/performance_monitor.py
"""Script to monitor performance metrics after HTMX enhancements"""

import time
import statistics
from selenium import webdriver
from selenium.webdriver.common.by import By

def measure_loading_performance():
    """Measure and report loading performance metrics"""
    driver = webdriver.Chrome()
    results = {
        'widget_load_times': [],
        'tab_switch_times': [],
        'preload_effectiveness': []
    }
    
    try:
        driver.get('http://localhost:5000')
        
        # Measure widget loading
        for i in range(10):
            widget = driver.find_element(By.CSS_SELECTOR, '.box[hx-get]')
            
            start_time = time.time()
            widget.click()
            # Wait for content to load
            end_time = time.time()
            
            results['widget_load_times'].append(end_time - start_time)
            
            # Reset for next test
            driver.refresh()
            time.sleep(1)
        
        # Report results
        print(f"Average widget load time: {statistics.mean(results['widget_load_times']):.3f}s")
        print(f"Median widget load time: {statistics.median(results['widget_load_times']):.3f}s")
        
    finally:
        driver.quit()
    
    return results

if __name__ == '__main__':
    measure_loading_performance()
```

## Test Data and Fixtures

### Mock Data for Tests
```python
# tests/fixtures/htmx_fixtures.py
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_widget():
    """Mock widget for testing templates"""
    widget = Mock()
    widget.type = 'feed'
    widget.hx_get = '/feed/test123'
    widget.name = 'Test Feed'
    widget.display_header = True
    widget.display_items = [
        Mock(id='item1', name='Test Article', summary='Test summary', link='http://example.com')
    ]
    return widget

@pytest.fixture
def mock_layout():
    """Mock layout for testing navigation"""
    layout = Mock()
    layout.tabs = [
        Mock(name='home'),
        Mock(name='work'),
        Mock(name='news')
    ]
    layout.headers = [
        Mock(name='GitHub', link='https://github.com')
    ]
    return layout
```

## Success Metrics

### Performance Metrics
- Widget loading time: < 100ms (with preload)
- Tab transition time: < 200ms
- Frame rate during transitions: > 55fps
- Memory growth over 1 hour: < 20%

### User Experience Metrics
- Time to interactive: Improve by 30%
- Cumulative Layout Shift: Reduce by 50%
- User engagement: Monitor via analytics

### Technical Metrics
- Test coverage: > 90% for HTMX-related code
- Cross-browser compatibility: Chrome, Firefox, Safari
- Accessibility compliance: WCAG 2.1 AA
- Error rate: < 0.1% for HTMX requests

## Reporting

Generate comprehensive test reports:

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html --cov-report=term tests/

# Generate performance report
python scripts/performance_monitor.py > performance_report.txt

# Generate accessibility report
pa11y http://localhost:5000 --reporter json > accessibility_report.json
```

This testing strategy ensures that all HTMX enhancements are thoroughly validated for functionality, performance, accessibility, and cross-browser compatibility before deployment.
