Lead Leak Prevention System
A FastAPI + PostgreSQL application designed to capture, manage, and prevent lead leakage across multiple channels (Slack, CRM, SMS/Email). The system integrates with external services, supports persistent storage, and uses Alembic migrations for schema evolution.

📂 Project Structure
Code
.
├── src/
│   ├── api/                 # FastAPI endpoints
│   ├── services/            # Business logic (CRM, notifications, messaging)
│   ├── core/                # Config, exceptions, database setup
│   └── models/              # Pydantic schemas + SQLAlchemy ORM models
├── tests/                   # Unit & integration tests
├── migrations/              # Alembic migration scripts
├── docker-compose.yml       # API + Postgres services
├── requirements.txt         # Dependencies
├── README.md                # Documentation
└── .env.example             # Environment variable template
⚙️ Setup
1. Clone the Repository
bash
git clone https://github.com/your-username/lead-leak-prevention-system.git
cd lead-leak-prevention-system
2. Environment Variables
Copy .env.example → .env and set values:

Code
DATABASE_URL=postgresql://user:password@db:5432/leadsdb
SLACK_WEBHOOK_URL=...
DISCORD_WEBHOOK_URL=...
SENDGRID_API_KEY=...
3. Run with Docker Compose
bash
docker-compose up --build -d
API available at:
👉 http://localhost:8000/docs

🗄️ Database & Migrations
We use Alembic for schema management.

Autogenerate migration

bash
docker-compose run alembic revision --autogenerate -m "init schema"
Apply migration

bash
docker-compose run alembic upgrade head
Tables:

Leads → capture contact info + campaign metadata

Clients → organizations hosting events

Events → scheduled activities linked to leads/clients

🌐 API Endpoints
/leads → create, read, update, delete leads

/clients → manage client records

/events → schedule and manage events

Swagger UI: http://localhost:8000/docs

💾 Persistence
Postgres data is stored in a persistent volume:

yaml
volumes:
  - ./pgdata:/var/lib/postgresql/data
This ensures data durability across container restarts.