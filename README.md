# HRM Backend

A FastAPI + MongoDB backend for the Human Rights Monitor (HRM) system.

## Features
- Case Management: CRUD, status tracking, attachments  
- Incident Reporting: secure submissions, media uploads, geotagging  
- Victim/Witness Database: encrypted records, risk assessment  
- Analytics Endpoints: violation counts, geodata, timelines

## Getting Started
### Prerequisites
- Python 3.9+  
- MongoDB Atlas (URI in `MONGODB_URI`)  

### Install & Run
```bash
git clone https://github.com/your-org/hrm-backend.git
cd hrm-backend
pip install -r requirements.txt
uvicorn hrm_backend.main:app --reload
