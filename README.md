# test
test
Activities Service
===================

Run locally
-----------

1) Create venv and install deps

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Start the API

```
export DATABASE_URL="sqlite:///./activities.db"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3) Example requests

```
curl -X POST http://localhost:8000/activities \
  -H 'content-type: application/json' \
  -d '{"actor":"user_1","verb":"posted","object":"Hello world"}'

curl 'http://localhost:8000/activities?limit=10'
```

4) Run tests

```
pytest -q
```