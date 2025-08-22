# Chat API

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

- `GET /health`: returns `{ "status": "ok" }`
- `POST /chat`: body:
```json
{
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "model": null,
  "stream": false
}
```
Response:
```json
{ "content": "You said: Hello" }
```

## Optional: OpenAI integration
Set `OPENAI_API_KEY` in your environment. Integration is stubbed and can be implemented in `app/main.py`.
