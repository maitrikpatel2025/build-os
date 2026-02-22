# Build OS: Build Backend API for Section

You are the Build OS API builder. Your job is to generate FastAPI routes, Pydantic models, and CRUD operations for one section's backend.

**Argument**: `$ARGUMENTS` (the section-id, e.g., `dashboard`, `agents`, `activity`)

## Prerequisites Check

1. Load the most recent build state from `agents/*/build_state.json`
2. Extract the section-id from `$ARGUMENTS`
3. Find the milestone for this section
4. Verify milestone status is `frontend_done` (frontend must be built first)
5. If check fails, report the issue and stop

## Steps

### 1. Read Data Specifications
Read these files from the product plan:
- `product-plan/sections/{section-id}/types.ts` — entity shapes and TypeScript interfaces
- `product-plan/sections/{section-id}/sample-data.json` — sample data for field types and structure
- `product-plan/data-shapes/overview.ts` — global entity definitions (if exists)

### 2. Generate Pydantic Models
Create `app/server/models/{section_id}_models.py`:

For each entity/interface found in `types.ts`:
- Convert TypeScript interfaces to Pydantic BaseModel classes
- Map TypeScript types to Python types:
  - `string` → `str`
  - `number` → `int` or `float` (check sample data)
  - `boolean` → `bool`
  - `string[]` → `List[str]`
  - `Date` or `string` (ISO format) → `str` (keep as string)
  - Optional fields (`?:`) → `Optional[type] = None`
  - Enum-like unions (`"active" | "idle"`) → `Literal["active", "idle"]`
- Create both request models (for create/update) and response models
- Add a list response model with pagination

### 3. Generate API Routes
Create `app/server/routes/{section_id}_routes.py`:

Generate standard CRUD endpoints:
- `GET /api/{section-id}` — List all items (with optional filters)
- `GET /api/{section-id}/{id}` — Get single item by ID
- `POST /api/{section-id}` — Create new item
- `PUT /api/{section-id}/{id}` — Update item
- `DELETE /api/{section-id}/{id}` — Delete item

Implementation approach:
- Use in-memory storage (list/dict) with sample data pre-loaded
- Import sample data from a generated fixtures file
- Return proper HTTP status codes (200, 201, 404)
- Use Pydantic models for request/response validation

### 4. Generate Fixtures
Create `app/server/routes/{section_id}_fixtures.py`:
- Load and export the sample data from the product plan
- Convert to Python dicts matching the Pydantic model structure

### 5. Register Routes
In `app/server/server.py`:
- Add import for the new route module
- Register the router with appropriate prefix: `app.include_router({section_id}_router, prefix="/api")`

### 6. Generate Tests
Create `app/server/tests/test_{section_id}.py`:
- Test GET list endpoint returns data
- Test GET single item returns correct item
- Test POST creates new item
- Test PUT updates item
- Test DELETE removes item
- Test GET non-existent ID returns 404

### 7. Validate
```bash
cd output/{product-slug}/app/server
uv sync
uv run pytest tests/test_{section_id}.py -v
```
- If tests fail, fix issues and retry
- All tests must pass

### 8. Commit and Update State
- Commit changes: `build-os: implement {section-id} API routes and models`
- Update milestone status to `backend_done`
- Save build state

## Output
- Pydantic models at `app/server/models/{section_id}_models.py`
- API routes at `app/server/routes/{section_id}_routes.py`
- Tests at `app/server/tests/test_{section_id}.py`
- Milestone status: `backend_done`

## Next Step
Tell the user: "Run `/build-os/wire-data {section-id}` to connect frontend to backend."

## Important Rules
- Auto-proceed through all steps without approval
- TypeScript → Python type conversion must be accurate
- Use sample-data.json as the data source for fixtures
- All generated tests must pass before committing
- Keep routes RESTful and consistent across sections
- Use in-memory storage (not database) for initial implementation
