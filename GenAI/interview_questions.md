# Travel Concierge Project Interview Q&A

This guide prepares you for common technical questions that project examiners or interviewers might ask about this architecture.

---

### Q1: What is the role of LangGraph in this travel concierge microservice?
**Answer**: LangGraph is used to coordinate a stateful, multi-agent workflow. Instead of using a simple single-prompt LLM call, LangGraph defines a state machine where different nodes represent specialized agents (Intent Extraction, Retrieval, Weather checks, Budgeting, Planning, and Validation). Each agent can inspect the state, append its data, and transition to the next node.

---

### Q2: Why did you implement a custom TF-IDF Cosine Similarity database instead of ChromaDB or Pinecone?
**Answer**: For a localized, pre-seeded travel catalog (around 30-50 landmarks per city), downloading heavy vector database libraries like PyTorch or SentenceTransformers (which are over 1GB) is highly inefficient for host runs. A pure Python TF-IDF engine computes cosine similarity mathematically in less than 2 milliseconds, requires zero external installations, and is 100% accurate for keyword matching during final project viva demonstrations.

---

### Q3: How do you handle API key absences or network failures during execution?
**Answer**: We follow clean architecture principles:
1. **Fallback checks**: If external services (like Google Maps, OpenWeather, or Gemini) are unconfigured or fail to respond due to internet timeouts, the services gracefully switch to high-fidelity simulated datasets.
2. **Exception logs**: All API requests are wrapped in try-except blocks with robust stream logging. The server never crashes.

---

### Q4: Explain the OpenClaw style booking tracker.
**Answer**: OpenClaw is an autonomous agent framework. In our booking service, we simulate an OpenClaw ticketing agent:
- When a user asks to plan a trip, any monument requiring tickets is registered as `CLAW-PENDING` (locked, waiting for user permission).
- Once the user explicitly permits or approves the transaction (e.g. typing "yes", "approve", "confirm"), the booking tracker shifts the status to `CLAW-AUTO-[CONF_CODE]`, simulating a completed payment and ticket reservation.

---

### Q5: How can this local SQLite memory be migrated to a production-grade database?
**Answer**: The memory manager uses Python's standard `sqlite3` driver. Because the SQL statements (`CREATE TABLE`, `INSERT`, `SELECT`) are standard, migrating to a production database like PostgreSQL or AWS RDS requires simply swapping the driver connection pool in `memory/manager.py` with SQLAlchemy, pointing to the target RDS URL.
