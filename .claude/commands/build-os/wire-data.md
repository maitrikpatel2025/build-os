# Build OS: Wire Frontend to Backend

You are the Build OS data wiring specialist. Your job is to replace mock/sample data with real API calls, connecting the frontend to the backend for one section.

**Argument**: `$ARGUMENTS` (the section-id, e.g., `dashboard`, `agents`, `activity`)

## Prerequisites Check

1. Load the most recent build state from `agents/*/build_state.json`
2. Extract the section-id from `$ARGUMENTS`
3. Find the milestone for this section
4. Verify milestone status is `backend_done` (both frontend and backend must be done)
5. If check fails, report the issue and stop

## Steps

### 1. Review Existing Code
Read the current state of both frontend and backend for this section:
- Frontend components: `app/client/src/sections/{section-id}/*.jsx`
- Frontend data file: `app/client/src/sections/{section-id}/data.js`
- Backend routes: `app/server/routes/{section_id}_routes.py`
- Backend models: `app/server/models/{section_id}_models.py`

Understand:
- What API endpoints are available
- What data shape the frontend expects
- What mock data is currently being used

### 2. Create API Service
Create `app/client/src/api/{section_id}.js`:

```javascript
const API_BASE = '/api/{section-id}';

export async function fetchAll() {
  const res = await fetch(API_BASE);
  if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
  return res.json();
}

export async function fetchById(id) {
  const res = await fetch(`${API_BASE}/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
  return res.json();
}

export async function create(data) {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to create: ${res.status}`);
  return res.json();
}

export async function update(id, data) {
  const res = await fetch(`${API_BASE}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to update: ${res.status}`);
  return res.json();
}

export async function remove(id) {
  const res = await fetch(`${API_BASE}/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Failed to delete: ${res.status}`);
  return res.json();
}
```

### 3. Update Section Page Component
Modify `{SectionName}Page.jsx` to use real API calls instead of mock data:

a. **Add state management**:
   ```javascript
   const [data, setData] = useState([]);
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState(null);
   ```

b. **Add data fetching**:
   ```javascript
   useEffect(() => {
     fetchAll()
       .then(setData)
       .catch(setError)
       .finally(() => setLoading(false));
   }, []);
   ```

c. **Wire callback props to API mutations**:
   - `onCreate` → call `create()`, then refetch or optimistically update
   - `onUpdate` → call `update()`, then refetch or optimistically update
   - `onDelete` → call `remove()`, then refetch or optimistically update

d. **Add loading state**:
   - Show a loading spinner or skeleton while data is loading
   - Show error message if API call fails

e. **Remove mock data imports**:
   - Remove import of `data.js`
   - Delete or keep `data.js` as fallback reference

### 4. Handle Edge Cases
- Empty state: Show appropriate empty state component when no data
- Loading state: Show spinner or skeleton
- Error state: Show error message with retry button
- Optimistic updates: Update UI immediately, rollback on error

### 5. Validate End-to-End
Run both frontend and backend and verify the connection:
```bash
# In the output project directory
cd output/{product-slug}

# Start backend
cd app/server && uv run uvicorn server:app --port 8000 &

# Verify API
curl http://localhost:8000/api/{section-id}

# Build frontend (validates compilation)
cd app/client && npm run build
```

- Frontend must build without errors
- API endpoint must return data

### 6. Commit and Update State
- Commit changes: `build-os: wire {section-id} frontend to backend API`
- Update milestone status to `wired`
- Save build state

## Output
- API service at `app/client/src/api/{section_id}.js`
- Updated page component with real API calls
- Loading/error states implemented
- Milestone status: `wired`

## Next Step
Tell the user: "Run `/build-os/validate {section-id}` to run tests and visual validation."

## Important Rules
- Auto-proceed through all steps without approval
- Replace ALL mock data with API calls — no hard-coded data should remain
- Use `fetch` (not axios) for API calls to minimize dependencies
- All API calls go through the Vite proxy (`/api/` prefix)
- Handle all three states: loading, error, success
- Keep the UI structure identical — only change the data source
