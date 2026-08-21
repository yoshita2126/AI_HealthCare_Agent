# Healthcare Patient Journey Coordination Agent

A multi-agent orchestration framework for coordinating patient care journeys, tracking investigations, detecting overdue follow-ups, escalating critical events to a Clinician Human-In-The-Loop (HITL) review queue, and generating evidence-grounded summaries citing FHIR resource identifiers.

## Project Structure

```
patient-journey-agent/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   └── state.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── audit.py
│   │   └── security.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   ├── intake_agent.py
│   │   ├── diagnostics_agent.py
│   │   ├── referral_agent.py
│   │   ├── escalation_agent.py
│   │   └── summarizer_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── fhir_tools.py
│   └── hitl/
│       ├── __init__.py
│       └── review_queue.py
├── requirements.txt
└── README.md
```

## How to Run

### 1. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Start the API server:
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Execute a coordination run:
```bash
curl -X POST "http://localhost:8000/journey/coordinate/PATIENT_101"
```

### 4. Inspect the Clinician HITL queue:
```bash
curl -X GET "http://localhost:8000/hitl/reviews?patient_id=PATIENT_101"
```
