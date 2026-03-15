# LocalRAG v0.9.0

LocalRAG is a local-first multilingual RAG application for private document question answering on your own machine.

## Highlights

- Multilingual web UI in English, Russian, Dutch, Chinese, and Hebrew
- Local Ollama-based answer generation with `qwen3.5:9b` as the default release model
- Persistent FAISS retrieval with source provenance, page references, and line ranges
- Built-in answer roles plus shared custom roles with prompt, language, model, style, and artwork
- In-app Ollama model manager and configurable embedding model
- Extended 30-question eval set with a release quality gate
- Release-first startup scripts for Windows and Linux/WSL

## Default Release Runtime

- Version: `0.9.0`
- Answer model: `qwen3.5:9b`
- Embedding model: `intfloat/multilingual-e5-large`
- Default Windows documents path: `C:\Temp\PDF`
- App URL: `http://localhost:7860`

## Verification

- `pytest -q`
- `python scripts/release_check.py --base-url http://localhost:7860 --expected-model qwen3.5:9b`
- `python scripts/model_eval.py --base-url http://localhost:7860 --seed-file eval/rag_eval_extended.json --models qwen3.5:9b --output temp/extended_eval.json`
- `python scripts/assert_eval_gate.py --report temp/extended_eval.json --model qwen3.5:9b --min-strict 1.0 --min-loose 1.0 --min-hit-ratio 1.0`

## Startup Options

```powershell
.\start_localrag.bat
```

```bash
./start_localrag.sh
```

Development mode is explicit:

```powershell
.\start_localrag.bat dev
```

```bash
./start_localrag.sh dev
```
