# HTMX 2.0.6 Upgrade Plan

## Current State Analysis
- **Current Version**: HTMX 1.9.12 (loaded via CDN from unpkg.com)
- **Target Version**: HTMX 2.0.6 (latest stable release as of August 14, 2025)
- **Usage Pattern**: Basic HTMX functionality with `hx-get`, `hx-trigger="load"`, and `hx-swap="outerHTML"`

## Key Changes in HTMX 2.0

### Breaking Changes
1. **IE Support Dropped**: HTMX 2.0 no longer supports Internet Explorer
2. **New CDN URLs**: Updated CDN paths and version references
3. **ES Module Support**: HTMX 2.0 provides better ES module support
4. **Configuration Changes**: Some default configuration values changed
5. **Enhanced Security**: Better CSP (Content Security Policy) support

### New Features in 2.0
- Shadow DOM support
- Template element support for OOB swaps
- Improved extension registration
- Enhanced TypeScript definitions
- Better form handling with FormData
- New swap styles including `textContent`

## Current Project HTMX Usage

### Files Using HTMX
1. **app/templates/index.html**: Main template with HTMX script inclusion
2. **app/templates/widget.html**: Uses `hx-get`, `hx-trigger`, `hx-swap`
3. **app/templates/docker_containers.html**: Uses similar HTMX attributes
4. **app/app.py**: References `skip_htmx` parameter for conditional loading

### HTMX Attributes Used
- `hx-get`: For AJAX GET requests
- `hx-trigger="load"`: Triggers request on element load
- `hx-swap="outerHTML"`: Replaces entire element with response

## Step-by-Step Upgrade Plan

### Phase 1: Pre-Upgrade Preparation
- [ ] **Step 1**: Document current HTMX behavior
  - Create test cases for existing HTMX interactions
  - Validate current widget loading functionality
  - Test docker container template behavior

- [ ] **Step 2**: Backup current implementation
  - Create branch: `htmx-1.9.12-backup`
  - Commit current working state

- [ ] **Step 3**: Browser compatibility assessment
  - Verify target browser support (IE no longer supported)
  - Update browser support documentation if needed

### Phase 2: Core Upgrade
- [ ] **Step 4**: Update HTMX CDN reference
  - Change `app/templates/index.html` line 18:
    ```html
    <!-- FROM -->
    <script defer src="https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js"></script>
    
    <!-- TO -->
    <script defer src="https://unpkg.com/htmx.org@2.0.6/dist/htmx.min.js"></script>
    ```

- [ ] **Step 5**: Test basic functionality
  - Load application and verify no console errors
  - Test widget loading behavior
  - Verify docker container template functionality

- [ ] **Step 6**: Update integrity hash (optional but recommended)
  - Add Subresource Integrity (SRI) hash for security:
    ```html
    <script defer 
            src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js" 
            integrity="sha384-..." 
            crossorigin="anonymous"></script>
    ```

### Phase 3: Testing and Validation
- [ ] **Step 7**: Run existing test suite
  - Execute `make test` to ensure no regressions
  - Fix any test failures related to HTMX behavior changes

- [ ] **Step 8**: Manual testing
  - Test widget refresh functionality
  - Verify AJAX loading indicators work correctly
  - Test any error handling scenarios

- [ ] **Step 9**: Performance testing
  - Compare load times between 1.9.12 and 2.0.6
  - Verify no degradation in user experience

### Phase 4: Optimization and Enhancement
- [ ] **Step 10**: Leverage new HTMX 2.0 features (optional)
  - Consider using enhanced form handling
  - Evaluate template element support for better organization
  - Review new swap styles for improved UX

- [ ] **Step 11**: Update documentation
  - Update any HTMX-related documentation
  - Note browser compatibility changes
  - Document any new features utilized

- [ ] **Step 12**: Security enhancements
  - Add CSP headers if not already present
  - Implement SRI hashes for CDN resources
  - Review HTMX security best practices

### Phase 5: Deployment and Monitoring
- [ ] **Step 13**: Staging deployment
  - Deploy to staging environment
  - Comprehensive testing with real data
  - Monitor for any edge cases

- [ ] **Step 14**: Production deployment
  - Deploy during low-traffic period
  - Monitor application performance
  - Have rollback plan ready

- [ ] **Step 15**: Post-deployment monitoring
  - Monitor error logs for HTMX-related issues
  - Track user experience metrics
  - Gather feedback from users

## Risk Assessment

### Low Risk
- Basic HTMX attributes (`hx-get`, `hx-trigger`, `hx-swap`) remain unchanged
- No custom HTMX extensions currently in use
- Simple CDN-based loading pattern

### Medium Risk
- IE users will no longer be supported (minimal impact in 2025)
- Potential changes in default behavior
- Alpine.js compatibility needs verification

### Mitigation Strategies
1. **Fallback Plan**: Keep 1.9.12 branch for quick rollback
2. **Progressive Testing**: Test in isolated environments first
3. **User Communication**: Inform users of IE support removal
4. **Monitoring**: Implement enhanced error tracking during transition

## Timeline Estimate
- **Phase 1**: 2-4 hours
- **Phase 2**: 1-2 hours  
- **Phase 3**: 4-6 hours
- **Phase 4**: 2-4 hours (optional)
- **Phase 5**: 2-4 hours

**Total Estimated Time**: 11-20 hours

## Success Criteria
- [ ] All existing HTMX functionality works as expected
- [ ] No console errors related to HTMX
- [ ] Performance remains same or improves
- [ ] All tests pass
- [ ] No user-reported issues after deployment

## Additional Considerations
1. **Alpine.js Compatibility**: Verify Alpine.js continues to work with HTMX 2.0
2. **Font Awesome Loading**: Ensure dynamic script loading still works correctly
3. **CSS Framework**: Verify any CSS frameworks remain compatible
4. **Server-Side Changes**: No changes required to Flask backend

## Resources
- [HTMX 2.0 Release Notes](https://github.com/bigskysoftware/htmx/releases/tag/v2.0.0)
- [HTMX Migration Guide](https://v1.htmx.org/migration-guide/)
- [HTMX 2.0 Documentation](https://htmx.org/docs/)
- [CDN Integrity Hash Generator](https://www.srihash.org/)
