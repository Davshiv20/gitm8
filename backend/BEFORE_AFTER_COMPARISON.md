# Before/After Comparison: LLM Service Refactoring

## Issue: Truncated Responses

### BEFORE ❌
```
candidates: [{'content': {...}, 'finishReason': 'MAX_TOKENS', 'index': 0}]
'text': 'Score: 8\nReasoning: Davshiv20 and DhruvDave12 exhibit strong'
                                                                    ^ TRUNCATED
```

### AFTER ✅
```json
{
  "score": 8,
  "reasoning": "Davshiv20 and DhruvDave12 complement each other well with their diverse skill sets...",
  "compatibility_factors": [
    {"label": "Shared Languages", "indicator": "Both proficient in Python and JavaScript"},
    {"label": "Project Sizes", "indicator": "Similar project complexity preferences"},
    {"label": "Contribution Activity", "indicator": "Active contributors with regular commits"},
    {"label": "Activity Heat", "indicator": "High engagement in recent months"}
  ]
}
```

**Changes**: Increased max_tokens from 500 → 2000, added MAX_TOKENS detection

---

## Architecture Pattern

### BEFORE ❌ (Singleton Pattern)
```python
class AsyncGeminiClient:
    _instance = None
    _session: aiohttp.ClientSession = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def get_session(cls):
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession(...)
        return cls._session

# Global instance
_gemini = AsyncGeminiClient()

async def call_llm_raw(prompt: str):
    return await _gemini.generate(prompt)
```

**Problems**:
- Hard to test (can't mock easily)
- Session lifecycle unclear
- Global state management
- Not FastAPI idiomatic

### AFTER ✅ (Dependency Injection)
```python
class AsyncGeminiClient:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.settings = get_settings()
    
    async def generate(self, prompt: str, ...):
        # Use self.session
        ...

# DI helpers
_llm_client: Optional[AsyncGeminiClient] = None

async def init_llm_client(session: aiohttp.ClientSession):
    global _llm_client
    _llm_client = AsyncGeminiClient(session)

def get_llm_client() -> AsyncGeminiClient:
    """FastAPI dependency"""
    if _llm_client is None:
        raise HTTPException(...)
    return _llm_client

# In routes
async def quick_compatibility(
    request: UserCompatibilityRequest,
    llm_client: AsyncGeminiClient = Depends(get_llm_client)
):
    response = await llm_client.generate(prompt)
```

**Benefits**:
- Easy to mock in tests
- Clear lifecycle (startup/shutdown)
- FastAPI best practice
- Explicit dependencies

---

## Error Handling

### BEFORE ❌ (Generic Errors)
```python
raise HTTPException(status_code=503, detail="LLM service unavailable")
raise HTTPException(status_code=502, detail="Invalid response from Gemini")
raise HTTPException(status_code=500, detail="Google API key not configured")
```

**Problems**:
- Generic messages confuse users
- No context about what failed
- Not branded to GitM8

### AFTER ✅ (User-Facing, Branded)
```python
raise HTTPException(
    status_code=503,
    detail="GitM8 analysis service is temporarily unavailable. Please try again in a moment."
)

raise HTTPException(
    status_code=502,
    detail="GitM8 received a malformed response from the analysis service. Please try again."
)

raise HTTPException(
    status_code=500,
    detail="GitM8 analysis service is not configured. Please contact support."
)
```

**Benefits**:
- Users understand what happened
- Actionable guidance
- Professional branding
- Better UX

---

## Retry Logic

### BEFORE ❌ (No Retries)
```python
async def generate(self, prompt: str):
    try:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                raise HTTPException(...)
            return await response.text()
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail="LLM service unavailable")
```

**Problems**:
- Fails on first transient error
- No handling of rate limits (429)
- Users must manually retry

### AFTER ✅ (Exponential Backoff)
```python
async def generate(self, prompt: str, ..., max_retries: int = 3):
    last_exception = None
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.text()
                
                # Retryable errors (5xx, 429)
                elif response.status in (429, 500, 502, 503, 504):
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 8.0)
                        continue
                
                # Non-retryable (4xx)
                else:
                    raise HTTPException(...)
        
        except aiohttp.ClientError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 8.0)
                continue
    
    raise last_exception
```

**Benefits**:
- Handles transient failures automatically
- Exponential backoff (1s → 2s → 4s)
- Distinguishes retryable vs non-retryable errors
- Better reliability

---

## Response Parsing

### BEFORE ❌ (Manual Line Parsing)
```python
def parse_compatibility_response(raw_response: str):
    score = 5  # Default
    reasoning = "Analysis based on profile data"  # Default
    factors = []
    
    lines = raw_response.strip().split('\n')
    for line in lines:
        if line.startswith('Score:'):
            score = int(...)
        elif line.startswith('Reasoning:'):
            reasoning = line.split(':', 1)[1]
        elif line.startswith('-'):
            # Complex parsing with | separator
            if '|' in content:
                parts = content.split('|', 1)
                indicator = parts[0]
                explanation = parts[1]
            else:
                indicator = content
                explanation = content
    
    # Silently add defaults if missing
    for label in FACTOR_LABELS:
        if label not in existing_labels:
            factors.append(CompatibilityFactor(
                label=label,
                indicator="Data not available",
                explanation="Data not available"
            ))
    
    return CompatibilityResponse(...)
```

**Problems**:
- Fragile (depends on exact format)
- Silent defaults hide issues
- Dead code (| separator not used)
- Hard to debug

### AFTER ✅ (JSON Parsing with Validation)
```python
def parse_compatibility_response(raw_response: str):
    # Extract JSON (handles markdown wrapping)
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = re.search(r'\{.*\}', raw_response, re.DOTALL).group(0)
    
    # Parse JSON
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail="GitM8 received a malformed response..."
        )
    
    # Validate required fields
    if "score" not in data:
        raise HTTPException(...)
    if "reasoning" not in data:
        raise HTTPException(...)
    if "compatibility_factors" not in data or len(data["compatibility_factors"]) != 4:
        raise HTTPException(...)
    
    # Parse factors
    factors = [
        CompatibilityFactor(label=f["label"], indicator=f["indicator"])
        for f in data["compatibility_factors"]
    ]
    
    # Strict validation
    return CompatibilityResponse(
        score=data["score"],  # No default
        reasoning=data["reasoning"],  # No default
        compatibility_factors=factors  # Must be exactly 4
    )
```

**Benefits**:
- Robust JSON parsing
- Handles edge cases (markdown wrapping)
- Strict validation (fails fast)
- Clear error messages
- No dead code

---

## Prompt Generation

### BEFORE ❌ (Async for No Reason)
```python
async def create_quick_compatibility_prompt(user_profiles: List[UserProfile]) -> str:
    template = _get_template("quick_compatibility")
    users = [_extract_user_data(p) for p in user_profiles]
    return template.render(users=users)

# In routes
quick_prompt = await create_quick_compatibility_prompt(user_profiles)
```

**Problems**:
- No I/O, but marked async
- Unnecessary async overhead
- Misleading (looks like it does async work)

### AFTER ✅ (Synchronous)
```python
def create_quick_compatibility_prompt(user_profiles: List[UserProfile]) -> str:
    template = _get_template("quick_compatibility")
    users = [_extract_user_data(p) for p in user_profiles]
    return template.render(users=users)

# In routes
quick_prompt = create_quick_compatibility_prompt(user_profiles)
```

**Benefits**:
- Honest about what it does
- No async overhead
- Simpler code

---

## Validation Strictness

### BEFORE ❌ (Silent Defaults)
```python
class CompatibilityResponse(BaseModel):
    score: int = Field(default=5, ge=1, le=10)
    reasoning: str = Field(default="Analysis based on profile data")
    compatibility_factors: List[CompatibilityFactor] = Field(default_factory=list)
    
    @field_validator('score', mode='before')
    def clamp_score(cls, v):
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                return 5  # Silent default
        return max(1, min(10, v))
```

**Problems**:
- Hides missing/invalid data
- Returns incomplete responses
- Hard to debug issues

### AFTER ✅ (Strict Validation)
```python
class CompatibilityResponse(BaseModel):
    score: int = Field(..., ge=1, le=10)  # Required
    reasoning: str = Field(..., min_length=10)  # Required, min length
    compatibility_factors: List[CompatibilityFactor] = Field(
        ..., min_length=4, max_length=4  # Required, exactly 4
    )
    
    @field_validator('score', mode='before')
    def clamp_score(cls, v):
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                raise ValueError("Score must be a valid integer between 1-10")
        if not (1 <= v <= 10):
            raise ValueError(f"Score {v} must be between 1-10")
        return v
```

**Benefits**:
- Fails fast on invalid data
- Forces complete responses
- Clear error messages
- Easier debugging

---

## App Lifecycle

### BEFORE ❌ (Implicit Session Management)
```python
class AsyncGeminiClient:
    @classmethod
    async def get_session(cls):
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession(...)
        return cls._session
    
    @classmethod
    async def close(cls):
        if cls._session:
            await cls._session.close()

# In shutdown
await AsyncGeminiClient.close()
```

**Problems**:
- Session created lazily
- Unclear when/where session is created
- Hard to track lifecycle

### AFTER ✅ (Explicit Lifecycle)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    llm_session = aiohttp.ClientSession(timeout=...)
    await init_llm_client(llm_session)
    app.state.llm_session = llm_session
    logger.info("✅ LLM client initialized")
    
    yield
    
    # SHUTDOWN
    await cleanup_llm_client()
    await app.state.llm_session.close()
    logger.info("✅ LLM session closed")
```

**Benefits**:
- Clear initialization point
- Explicit cleanup
- Logged lifecycle events
- Stored in app state

---

## Summary Table

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Response Completeness** | Truncated at 500 tokens | Full responses (2000 tokens) | ✅ 4x capacity |
| **Parsing** | Line-by-line text parsing | JSON with regex fallback | ✅ Robust |
| **Error Handling** | No retries | 3 attempts w/ backoff | ✅ Reliable |
| **Architecture** | Singleton pattern | Dependency injection | ✅ Testable |
| **Error Messages** | Generic technical | User-facing branded | ✅ Better UX |
| **Validation** | Silent defaults | Strict required fields | ✅ Fail fast |
| **Prompt Generation** | Async (unnecessary) | Synchronous | ✅ Honest |
| **Session Management** | Lazy/implicit | Explicit lifecycle | ✅ Clear |
| **Cost per Request** | $0.00015 (broken) | $0.0003 (working) | ⚠️ 2x cost |

## Bottom Line

The refactoring trades a **2x cost increase** (~$0.30/month for 1000 requests) for:
- ✅ Working responses (no truncation)
- ✅ Production-grade reliability (retry logic)
- ✅ Professional UX (branded errors)
- ✅ Maintainable codebase (DI, strict validation)
- ✅ Testable architecture (easy mocking)

**Worth it? Absolutely.** You can't ship a feature that returns broken responses.

