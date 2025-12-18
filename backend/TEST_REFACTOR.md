# Testing the LLM Service Refactoring

## Quick Verification

### 1. Server Startup
```bash
cd /Users/shivam/Desktop/gitm8/backend
python gitm8/main.py
```

**Expected logs**:
```
✅ Settings validation completed successfully
✅ Database connection successful
✅ GitHub HTTP client session initialized successfully
✅ LLM client initialized
✅ All services initialized successfully
```

### 2. Health Check
```bash
curl http://localhost:8180/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "github_session": "active",
  "llm_session": "active"
}
```

### 3. Compatibility Analysis (The Real Test!)
```bash
curl -X POST http://localhost:8180/api/quick-compatibility \
  -H "Content-Type: application/json" \
  -d '{"usernames": ["davshiv20", "dhruvdave12"]}'
```

**Expected response structure**:
```json
{
  "success": true,
  "users": [...],
  "compatibility_score": 8,
  "compatibility_reasoning": "Davshiv20 and DhruvDave12 complement each other well...",
  "compatibility_factors": [
    {
      "label": "Shared Languages",
      "indicator": "Both proficient in Python and JavaScript"
    },
    {
      "label": "Project Sizes",
      "indicator": "Similar project complexity preferences"
    },
    {
      "label": "Contribution Activity",
      "indicator": "Active contributors with regular commits"
    },
    {
      "label": "Activity Heat",
      "indicator": "High engagement in recent months"
    }
  ],
  "radar_chart_data": {...},
  "comparison_data": {...}
}
```

## Validation Checklist

### ✅ No More Truncation
- [ ] Response contains full reasoning (not cut off mid-sentence)
- [ ] All 4 compatibility factors are present
- [ ] No `MAX_TOKENS` warnings in logs

### ✅ JSON Parsing Works
- [ ] Response is valid JSON
- [ ] No parsing errors in logs
- [ ] All required fields present

### ✅ Error Messages Are Branded
Try with invalid usernames:
```bash
curl -X POST http://localhost:8180/api/quick-compatibility \
  -H "Content-Type: application/json" \
  -d '{"usernames": ["nonexistent123456"]}'
```

- [ ] Error message mentions "GitM8" (not generic errors)
- [ ] Message is user-friendly

### ✅ Retry Logic
Temporarily break the API (set invalid API key) and watch logs:
- [ ] Logs show retry attempts
- [ ] Exponential backoff delays visible
- [ ] Final error message is user-friendly

### ✅ Dependency Injection
Check that the client is injected properly:
- [ ] No import errors
- [ ] Route receives `llm_client` parameter
- [ ] Client works in route handler

## Common Issues

### Issue: "LLM client not initialized"
**Solution**: Server didn't start properly. Check startup logs for errors.

### Issue: "MAX_TOKENS" still appearing
**Solution**: Response is very large. Check prompt template, ensure it's not requesting too much detail.

### Issue: JSON parsing fails
**Solution**: LLM returned markdown-wrapped JSON. The regex should handle this, but if not, check `parse_compatibility_response()` logic.

### Issue: Retries happening on every request
**Solution**: API key is invalid or rate limit exceeded. Check API quota and credentials.

## Performance Testing

### Single Request Latency
```bash
time curl -X POST http://localhost:8180/api/quick-compatibility \
  -H "Content-Type: application/json" \
  -d '{"usernames": ["davshiv20", "dhruvdave12"]}'
```

**Expected**: 2-5 seconds (normal), up to 15 seconds (with retries)

### Concurrent Requests
```bash
# Install Apache Bench
brew install apache-bench

# Test 10 concurrent requests
ab -n 10 -c 5 -p request.json -T application/json \
  http://localhost:8180/api/quick-compatibility
```

**Monitor**: Check logs for any errors, session issues, or rate limits.

## Debugging Tips

### Enable Debug Logging
In `gitm8/main.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Check LLM Raw Response
Add temporary logging in `routes.py`:
```python
raw_llm_response = await llm_client.generate(quick_prompt)
logger.info(f"Raw LLM response: {raw_llm_response}")  # ADD THIS
compatibility_result = parse_compatibility_response(raw_llm_response)
```

### Test JSON Parsing Separately
```python
# In Python REPL
from services.llm_service import parse_compatibility_response
import json

test_response = '''
{
  "score": 8,
  "reasoning": "Test reasoning",
  "compatibility_factors": [
    {"label": "Shared Languages", "indicator": "Test indicator 1"},
    {"label": "Project Sizes", "indicator": "Test indicator 2"},
    {"label": "Contribution Activity", "indicator": "Test indicator 3"},
    {"label": "Activity Heat", "indicator": "Test indicator 4"}
  ]
}
'''

result = parse_compatibility_response(test_response)
print(result)
```

## Integration Testing

### Test with Frontend
1. Start backend: `python gitm8/main.py`
2. Start frontend: `cd ../frontend && npm run dev`
3. Navigate to `http://localhost:5173`
4. Enter two GitHub usernames
5. Click "Analyze Compatibility"
6. Verify:
   - [ ] Score displays correctly
   - [ ] Reasoning is complete (not truncated)
   - [ ] All 4 factors show up
   - [ ] Charts render properly

## Rollback Plan

If issues arise, revert to previous version:

```bash
git log --oneline  # Find commit before refactor
git revert <commit-hash>
```

Or manually restore:
1. Restore `services/llm_service.py` to singleton pattern
2. Restore `routes/routes.py` to use `call_llm_raw()`
3. Restore `gitm8/main.py` to remove LLM client init
4. Set `max_tokens` back to 500 (accept truncation)

## Success Criteria

✅ All tests pass
✅ No truncated responses
✅ Error messages are user-friendly
✅ Retry logic works on transient failures
✅ Health check shows LLM session as "active"
✅ Frontend integration works smoothly
✅ No increase in error rate
✅ Response latency is acceptable (<5s typical)

## Next Steps After Validation

1. **Add Response Caching**
   - Cache compatibility results by username pair
   - Reduces LLM calls and cost
   - Example: Redis or in-memory cache

2. **Add Metrics**
   - Track LLM response time
   - Track retry rate
   - Track parse success rate
   - Example: Prometheus + Grafana

3. **Add Rate Limiting**
   - Limit requests per user/IP
   - Prevent abuse and control costs
   - Example: slowapi or custom middleware

4. **Write Unit Tests**
   ```python
   # tests/test_llm_service.py
   import pytest
   from services.llm_service import parse_compatibility_response
   
   def test_parse_valid_json():
       response = '{"score": 8, "reasoning": "...", "compatibility_factors": [...]}'
       result = parse_compatibility_response(response)
       assert result.score == 8
       assert len(result.compatibility_factors) == 4
   
   def test_parse_markdown_wrapped_json():
       response = '```json\n{"score": 8, ...}\n```'
       result = parse_compatibility_response(response)
       assert result.score == 8
   ```

5. **Add Monitoring**
   - Set up error alerting
   - Monitor LLM API quota usage
   - Track cost per day/week/month

## Questions?

Check the following docs:
- `REFACTOR_SUMMARY.md` - Detailed changes
- `BEFORE_AFTER_COMPARISON.md` - Visual comparisons
- `services/llm_service.py` - Implementation
- `routes/routes.py` - Usage example

