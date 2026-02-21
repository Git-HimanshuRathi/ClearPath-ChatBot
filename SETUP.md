# Setup Guide

## Prerequisites

- **Python 3.11+** (tested with 3.13)
- **Node.js 18+**
- **Groq API Key** — Free at [console.groq.com](https://console.groq.com/)

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/Git-HimanshuRathi/ClearPath-ChatBot.git
cd ClearPath-ChatBot
```

## Step 2 — Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows

# Install dependencies
pip install -r backend/requirements.txt
```

## Step 3 — Set Groq API Key

```bash
echo "GROQ_API_KEY=your_key_here" > .env
```

Get your key from [console.groq.com/keys](https://console.groq.com/keys).

## Step 4 — Start Backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

On **first startup**, the server will automatically:

1. Read all 30 PDFs from `docs/`
2. Chunk text into 500-token windows (100-token overlap)
3. Generate embeddings using `all-MiniLM-L6-v2`
4. Build FAISS index and save to `data/`

Subsequent starts load the cached index instantly.

Wait for:

```
✓ Ready! Index contains 49 vectors
```

## Step 5 — Frontend Setup

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

## Step 6 — Open the App

Go to **http://localhost:5173** in your browser.

---

## Environment Variables

| Variable       | Required | Description  |
| -------------- | -------- | ------------ |
| `GROQ_API_KEY` | Yes      | Groq API key |

---

## Troubleshooting

| Problem                  | Fix                                                    |
| ------------------------ | ------------------------------------------------------ |
| `GROQ_API_KEY not set`   | Add your key to `.env` in the project root             |
| `Address already in use` | Kill the old process: `lsof -ti:8000 \| xargs kill -9` |
| `proxies` TypeError      | Run `pip install --upgrade groq`                       |
| Slow first startup       | Normal — building FAISS index from 30 PDFs takes ~30s  |
