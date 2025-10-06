# Failing Tests

## Current Status
Test framework initialized. Schema unit tests created but not yet executed.

## Critical Failures (Will Track Here)

### Unit Test Failures
| Test Suite | Test Name | Failure Reason | Priority | Issue # |
|------------|-----------|----------------|----------|----------|
| test_schemas.py | All tests | Not executed yet - awaiting user confirmation | High | - |
| test_storage.py | All tests | Not executed yet - includes concurrent access tests | High | - |
| test_participants.py | All tests | Not executed yet - includes NLWeb integration mocks | High | - |

### Integration Test Failures  
| Test Suite | Test Name | Failure Reason | Priority | Issue # |
|------------|-----------|----------------|----------|----------|
| test_rest_api.py | All tests | Not executed yet - requires running API server | High | - |
| test_websocket.py | All tests | Not executed yet - uses mock WebSocket client | High | - |

### Performance Test Failures
| Test Suite | Test Name | Expected | Actual | Priority | Issue # |
|------------|-----------|----------|--------|----------|----------|
| test_latency.py | All latency tests | Not executed yet - awaiting test run | TBD | High | - |
| test_load.py | All load/stress tests | Not executed yet - awaiting test run | TBD | High | - |

### Security Test Failures
| Test Suite | Test Name | Vulnerability | Severity | Issue # |
|------------|-----------|---------------|----------|----------|
| test_auth.py | All auth tests | Not executed yet - awaiting test run | High | - |
| test_validation.py | All validation tests | Not executed yet - awaiting test run | High | - |

### Reliability Test Failures
| Test Suite | Test Name | Failure Scenario | Impact | Issue # |
|------------|-----------|------------------|---------|----------|
| test_recovery.py | All reliability tests | Not executed yet - awaiting test run | High | - |

### End-to-End Test Failures
| Test Suite | Test Name | Failure Scenario | Impact | Issue # |
|------------|-----------|------------------|---------|----------|
| test_multi_participant.py | All E2E tests | Not executed yet - awaiting test run | High | - |

## Missing API Endpoints (Critical)

### Required for Multi-Participant Support
| Endpoint | Purpose | Status | Priority |
|----------|---------|--------|----------|
| POST /chat/{id}/join | Join existing conversation | **IMPLEMENTED** | Critical |
| DELETE /chat/{id}/leave | Leave conversation | **IMPLEMENTED** | Critical |
| GET /chat/conversations/{id} | Get specific conversation | **IMPLEMENTED** | Critical |

### Implementation Progress
- ✅ `/chat/{id}/join` - Implemented with full functionality including:
  - Duplicate participant checking (409 response)
  - Capacity limit enforcement (429 response)
  - WebSocket broadcast of join events
  - Full conversation object in response
  
- ✅ `/chat/{id}/leave` - Implemented with:
  - Participant verification
  - WebSocket connection cleanup
  - Broadcast of leave events
  - Last participant handling
  
- ✅ `/chat/conversations/{id}` - Implemented with:
  - Participant authorization check
  - Full conversation details with messages
  - Online status for participants
  - Matches test response format

### WebSocket Enhancements
- ✅ Participant verification before connection
- ✅ Real-time participant join/leave broadcasts
- ✅ Participant list sent on connection
- ✅ Connection cleanup on leave
- ✅ 403 Forbidden for non-participants
- ✅ 404 for non-existent conversations

## Known Issues to Address

### High Priority
1. **WebSocket Reconnection** - Must handle disconnects gracefully
   - Status: Not tested
   - Expected: Automatic reconnection with exponential backoff
   - Risk: Message loss during disconnection

2. **Message Ordering** - Sequence IDs must be sequential
   - Status: Not tested  
   - Expected: Strict ordering even under concurrent sends
   - Risk: Out-of-order message display

3. **Queue Overflow** - 429 responses when queue full
   - Status: Not tested
   - Expected: Graceful handling with retry guidance
   - Risk: Message loss or system crash

### Medium Priority
4. **XSS Prevention** - DOMPurify must sanitize all user content
   - Status: Not tested
   - Expected: All malicious content neutralized
   - Risk: Security vulnerability

5. **State Persistence** - localStorage save/load must work
   - Status: Not tested
   - Expected: Conversations persist across sessions
   - Risk: Data loss on refresh

6. **Concurrent Messages** - Multiple users sending simultaneously
   - Status: Not tested
   - Expected: All messages delivered in order
   - Risk: Race conditions

### Low Priority  
7. **Large Message Volumes** - Performance with 1000+ messages
   - Status: Not tested
   - Expected: <200ms delivery time maintained
   - Risk: Performance degradation

8. **Identity Loss** - Handle cleared localStorage
   - Status: Not tested
   - Expected: Graceful re-authentication
   - Risk: User locked out

## Flaky Tests (Will Track Here)
| Test Name | Flakiness Rate | Root Cause | Mitigation |
|-----------|----------------|------------|-------------|
| - | - | - | - |

## Test Environment Issues
- ✅ Test configuration file created (config_test.yaml)
- ✅ Test fixtures updated to use config_test.yaml
- ✅ Storage cleanup between tests implemented
- ✅ External dependencies mocked (OAuth, NLWeb, Azure, OpenAI)