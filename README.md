# microsave

## Project Structure

```
microsave/
├── app/
│   ├── main.py       # app factory, lifespan, exception handlers
│   ├── api/          # endpoints
│   ├── services/     # Ochestration
│   ├── models/       # request/response models
│   └── core/         # Settings via env / .env file, app logics
├── tests/
├── pyproject.toml
└── .env
```

## How to Request Data
This microsave service utilizes RESTful API. To request data operations (saving, loading, or deleting), execute HTTP requests to the target endpoints.

Available Endpoints:
``` 
Save State: POST /save
Requires a JSON body containing: client_app_id, user_id, save_slot, schema_version, and the actual payload data.

Load State: GET /load/{client_app_id}/{user_id}/{save_slot}
Retrieves a previously saved state based on the provided URL path parameters.

Delete State: DELETE /delete/{client_app_id}/{user_id}/{save_slot}
Removes a specific save slot for a given user.
```

Example Calls:
``` python
import requests

BASE_URL = "http://127.0.0.1:8000"

# Example: Requesting to SAVE data
save_payload = {
    "client_app_id": "scavenger",
    "user_id": "user_123",
    "save_slot": "slot 1",
    "schema_version": 1,
    "payload": {
        "data": "level_4_complete",
        "health": 85
    }
}
requests.post(f"{BASE_URL}/save", json=save_payload)

# Example: Requesting to LOAD data
requests.get(f"{BASE_URL}/load/scavenger/user_123/slot 1")
```

## How to Receive Data
This microservice synchronously responds to requests using standard HTTP status codes and JSON payloads. Successful HTTP status codes are: 200 OK for loads and saves, 204 No Content for deletes. If the requested save does not exist, the service will return a 404 Not Found status.

Example Receive and Process:
``` python
import requests

BASE_URL = "http://127.0.0.1:8000"

# 1. Execute the load request
response = requests.get(f"{BASE_URL}/load/scavenger/user_123/slot 1")

# 2. Receive and process the data based on status code
if response.status_code == 200:
    save_data = response.json()
    
    # Extract the custom payload
    custom_data = save_data.get("payload", {})
    last_updated = save_data.get("updated_at")
    
    print(f"Successfully loaded! Last saved at: {last_updated}")
    print(f"Game State: {custom_data}")

elif response.status_code == 404:
    print("No save file found in this slot.")
    
else:
    print(f"An error occurred: {response.status_code} - {response.text}")
```


## Public API

## UML Diagram
```mermaid
sequenceDiagram
    autonumber
    actor Client as Client App<br/>(e.g. scavenger)
    participant API as FastAPI<br/>(client_router)
    participant Env as SaveEnvelope<br/>(Pydantic)
    participant Reg as PAYLOAD_MODELS<br/>registry
    participant Helper as build_save_document
    participant Svc as services.mongo
    participant DB as MongoDB<br/>(saves collection)
    participant Test as pytest +<br/>httpx.AsyncClient

    %% ---------------- App startup ----------------
    Note over API,DB: Startup (lifespan)
    API->>DB: create_mongo_client(mongodb_uri)
    API->>DB: create_indexes(db)<br/>unique (client_app_id, user_id, save_slot)

    %% ---------------- POST /save ----------------
    Client->>API: POST /save<br/>{client_app_id, user_id, save_slot,<br/>schema_version, payload}
    API->>Env: SaveEnvelope(**body)
    Env->>Reg: PAYLOAD_MODELS.get(client_app_id)
    alt client_app_id not registered
        Reg-->>Env: None
        Env-->>API: ValueError "Unsupported client app id"
        API-->>Client: 422 Unprocessable Entity
    else registered (e.g. "scavenger")
        Reg-->>Env: ScavengerPayload class
        Env->>Env: ScavengerPayload.model_validate(payload)
        Env-->>API: validated SaveEnvelope
        API->>Helper: build_save_document(se)
        Helper-->>API: SaveDocument(+created_at, updated_at)
        API->>Svc: upsert_save(sd, db)
        Svc->>DB: saves.update_one(<br/>{client_app_id, user_id, save_slot},<br/>{$set: doc, $setOnInsert: {created_at}},<br/>upsert=True)
        DB-->>Svc: UpdateResult
        Svc-->>API: ok
        API-->>Client: 200 OK<br/>SaveResponse(updated_at, payload, ...)
    end

    %% ---------------- GET /load ----------------
    Client->>API: GET /load/{client_app_id}/{user_id}/{save_slot}
    API->>Svc: get_save(client_app_id, user_id, save_slot, db)
    Svc->>DB: saves.find_one({client_app_id, user_id, save_slot})
    alt not found
        DB-->>Svc: None
        Svc-->>API: None
        API-->>Client: 404 "Save not found"
    else found
        DB-->>Svc: save document
        Svc-->>API: dict
        API-->>Client: 200 OK SaveResponse(**sd)
    end

    %% ---------------- DELETE /delete ----------------
    Client->>API: DELETE /delete/{client_app_id}/{user_id}/{save_slot}
    API->>Svc: delete_save(client_app_id, user_id, save_slot, db)
    Svc->>DB: saves.delete_one({client_app_id, user_id, save_slot})
    DB-->>Svc: DeleteResult(deleted_count)
    alt deleted_count == 1
        Svc-->>API: result
        API-->>Client: 204 No Content
    else not found
        API-->>Client: 404 "Save not found"
    end

    %% ---------------- Unit test path ----------------
    Note over Test,DB: Unit tests
    Test->>API: AsyncClient.post("/save", json=fixture)
    Note right of Test: Override Depends(get_db)<br/>with test AsyncDatabase<br/>(mongomock-motor or<br/>testcontainers Mongo)
    API->>Svc: upsert_save(sd, test_db)
    Svc->>DB: update_one(...) on test DB
    DB-->>API: result
    API-->>Test: 200 + SaveResponse
    Test->>Test: assert response.status_code == 200<br/>assert payload round-trips
```

## MongoDB

### Write Cache

Implements a coalescing write-buffer (`io.BufferedWrite` / `collections.deque`):
- Every publish call stores only the most recent `(x, y)` per player in a dict; intermediate ticks are discarded.
- A background asyncio.Task flushes the buffer to MongoDB every 3 seconds.
- If a client's `POSITION_CACHE_MAX_PENDING` count is hit, the bufffer force-flushes that client immediately as a safety net.
- On shutdown, call `flush_all()` to drain the buffer before the connection is closed.
- If a flush fails, the entry is re-buffered so the next cycle can try again.

The free tier allows up to 100 operations per second. That's shared across all reads and writes hitting the cluster. With 5 clients polling at `20 fps tick rate = 100 writes/sec`, we're sitting right at the ceiling before a single read happens. With the 3-second write cache, that drops to roughly `5 clients ÷ 3 seconds = ~2 writes/sec`, plus poll calls. At 5 clients polling a few times a second, we're looking at maybe 15–20 ops/sec total, well within budget.


### Development Environment
Create and populate `.env.mongodb` environment file in the local project root. The environment file requires the following variables to be defined:

```
MONGODB_URI=<Replace with MongoDB Connection String>
MONGODB_DB_NAME=<Replace with Database Name>
```

> [!CAUTION]
> Do not commit `.env.mongodb` to git

## Git Workflow

#### Sync main before branching
1. `git checkout main`
2. `git pull --rebase origin main`

#### Create branch
1. `git checkout -b feature/task`

#### Write Code/Commit locally
1. `git add .`
2. `git commit -m "message"`

#### To squash a small commit into a bigger one
1. `git rebase -i HEAD~n`

#### Update branch before pushing
1. `git fetch origin` (or git pull)
2. `git rebase origin/main`

#### Push for PR
1. `git push -u origin feature/task`

