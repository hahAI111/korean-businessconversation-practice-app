# Tech Stack & Conventions
## Korean Biz Coach — Technical Standards

### Language & Runtime
- Python 3.14 (App Service), Python 3.12 fallback (Oryx build)
- FastAPI (async)
- Uvicorn (ASGI server)

### Azure Services (All Entra ID / No Keys)
| Service | Auth Method | Usage |
|---------|------------|-------|
| AI Foundry | DefaultAzureCredential → AzureOpenAI (Responses API) | GPT model + MCP tools |
| Speech Service | DefaultAzureCredential → Bearer token | STT, TTS, Pronunciation |
| PostgreSQL | Password in connection string (VNet private) | Relational data (users, lessons, progress) |
| Cosmos DB | DefaultAzureCredential (Entra ID) | Document data (conversations, drama, events) |
| Redis Cache | Access key in URL (VNet private, SSL) | Session/rate-limit cache |
| App Service | Managed Identity | Hosting |

### Code Conventions
- Chinese comments for documentation (target audience: Chinese developers)
- Type hints everywhere
- Async/await for all I/O operations
- Pydantic for all data validation
- SQLAlchemy 2.0 style (mapped_column, DeclarativeBase)
- azure-cosmos (async) for Cosmos DB document operations

### Frontend
- Vanilla JS (no framework)
- CSS custom properties for theming
- Dark theme with purple accents
- Responsive: desktop + mobile

### Project Structure
```
korean-biz-agent/
├── bmad-docs/          # BMAD Method documentation
├── app/                # FastAPI application
│   ├── core/           # Config, DB, Cosmos, Redis, Auth
│   ├── api/            # Route handlers
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   └── services/       # Business logic
├── mcp_server/         # Teaching tools
├── data/               # Content data (JSON)
├── static/             # Frontend files
├── alembic/            # Database migrations
└── tests/              # Test suite
```
