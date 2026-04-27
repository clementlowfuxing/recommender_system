# Copilot 365 Integration — Setup Guide

## Overview

This guide walks you through deploying the CDWC Talent Recommendation Engine
as a Microsoft 365 Copilot plugin. After setup, users can ask Copilot in
Teams/Word/etc. to find talent, and Copilot will call your `/recommend` API
and present the results conversationally.

```
User (Teams/Copilot) → Copilot LLM (parses NL) → Your API (/recommend)
                                                  → Engine (filter/score/rank)
                                                  → Copilot LLM (formats response)
                                                  → User sees ranked candidates
```

---

## Prerequisites

- Microsoft 365 tenant with Copilot licenses
- Azure subscription (for hosting the API)
- Azure AD app registration (for OAuth)
- Teams Toolkit for VS Code (optional, simplifies deployment)
- Admin access to Microsoft 365 admin center

---

## Step 1: Deploy the FastAPI Server to Azure

### Option A: Azure App Service (simplest)

```bash
# From the cdwc_recommendation_system directory

# Login to Azure
az login

# Create resource group
az group create --name cdwc-rg --location southeastasia

# Create App Service plan
az appservice plan create \
  --name cdwc-plan \
  --resource-group cdwc-rg \
  --sku B1 \
  --is-linux

# Create the web app
az webapp create \
  --name cdwc-talent-api \
  --resource-group cdwc-rg \
  --plan cdwc-plan \
  --runtime "PYTHON:3.11"

# Deploy your code
az webapp up \
  --name cdwc-talent-api \
  --resource-group cdwc-rg \
  --runtime "PYTHON:3.11"
```

Add a startup command in Azure Portal → App Service → Configuration:
```
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Add `gunicorn` to requirements.txt for production deployment.

Verify: `https://cdwc-talent-api.azurewebsites.net/health` should return `{"status": "ok"}`.

### Option B: Azure API Management (if API already hosted elsewhere)

If your API is already running somewhere (on-prem, another cloud), put Azure
API Management in front of it to handle auth and expose it to Copilot.

---

## Step 2: Register Azure AD App (OAuth 2.0)

Copilot plugins require OAuth authentication. Register an app in Azure AD:

1. Go to Azure Portal → Azure Active Directory → App registrations → New registration
2. Settings:
   - Name: `CDWC Talent API`
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect`
3. After creation, note down:
   - Application (client) ID
   - Directory (tenant) ID
4. Go to Certificates & secrets → New client secret → copy the value
5. Go to API permissions → Add permission → Microsoft Graph → `User.Read` (delegated)
6. Go to Expose an API:
   - Set Application ID URI: `api://cdwc-talent-api.azurewebsites.net/{client-id}`
   - Add a scope: `access_as_user`

---

## Step 3: Add Auth to Your FastAPI Server

Add a middleware or dependency that validates the Azure AD JWT token.
Install the dependency:

```bash
pip install python-jose[cryptography]
```

Add to your `main.py` (or a separate `auth.py`):

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx

TENANT_ID = "your-tenant-id"
CLIENT_ID = "your-client-id"
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    token = credentials.credentials
    try:
        # Fetch Microsoft's public keys
        async with httpx.AsyncClient() as client:
            resp = await client.get(JWKS_URL)
            jwks = resp.json()
        payload = jwt.decode(
            token, jwks, algorithms=["RS256"],
            audience=CLIENT_ID, issuer=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

Then protect your endpoints:

```python
@app.post("/recommend")
def post_recommend(req: ProjectRequirement, user=Depends(verify_token)):
    ...
```

---

## Step 4: Update the Plugin Files

In the `copilot-plugin/` folder, replace all `{your-app}` placeholders:

1. `openapi.yaml` → update the `servers.url` to your deployed URL
2. `ai-plugin.json` → update `logo_url`, `contact_email`, `legal_info_url`, `privacy_url`
3. `manifest.json` → update `websiteUrl`, `privacyUrl`, `termsOfUseUrl`, `validDomains`
4. `manifest.json` → replace `{{TEAMS_APP_ID}}` with a new GUID (generate one at https://www.guidgenerator.com)

---

## Step 5: Configure OAuth in Teams Developer Portal

1. Go to https://dev.teams.microsoft.com → Tools → OAuth client registration
2. Create a new registration:
   - Registration name: `cdwc-oauth`  (must match `reference_id` in ai-plugin.json)
   - Client ID: your Azure AD app client ID
   - Client secret: your Azure AD app secret
   - Authorization endpoint: `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize`
   - Token endpoint: `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token`
   - Scope: `api://cdwc-talent-api.azurewebsites.net/{client-id}/access_as_user`

---

## Step 6: Package and Upload the Plugin

### Option A: Teams Toolkit (recommended)

If using Teams Toolkit in VS Code:
1. Open the `copilot-plugin/` folder
2. Teams Toolkit auto-detects the manifest
3. Click "Provision" then "Deploy"

### Option B: Manual upload

1. Create icon files: `color.png` (192x192) and `outline.png` (32x32)
2. Zip the contents of `copilot-plugin/`:
   ```
   manifest.json
   declarativeAgent.json
   ai-plugin.json
   openapi.yaml
   color.png
   outline.png
   ```
3. Go to https://dev.teams.microsoft.com → Apps → Import app → upload the zip
4. Go to the app → Publish → Publish to your org

---

## Step 7: Admin Approval

1. Microsoft 365 admin center → Settings → Integrated apps
2. Find "CDWC Talent Search" → Approve for your organization
3. Enable the Copilot plugin: Admin center → Copilot → Manage agents → Enable "CDWC Talent Advisor"

---

## Step 8: Test in Copilot

1. Open Microsoft Teams → Copilot chat
2. Click the plugin icon or type `@CDWC Talent Search`
3. Try: "Find me a senior Python developer with ML experience, 5+ years"
4. Copilot should call your `/recommend` API and present the ranked candidates

---

## File Inventory

```
copilot-plugin/
├── manifest.json            # Teams app manifest (points to declarative agent)
├── declarativeAgent.json    # Agent instructions, conversation starters, actions
├── ai-plugin.json           # Plugin definition (functions, auth, OpenAPI ref)
├── openapi.yaml             # Full OpenAPI 3.0 spec for your API
├── color.png                # App icon 192x192 (you need to create this)
├── outline.png              # App icon 32x32 (you need to create this)
└── SETUP_GUIDE.md           # This file
```

---

## Architecture After Integration

```
┌──────────────────────────────────────────────────────────────┐
│                    Microsoft 365 Copilot                      │
│                                                              │
│  User: "Find a senior Python dev with ML, 5+ years"         │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────┐                   │
│  │  Copilot LLM (replaces your parser)  │                   │
│  │  Extracts: skills, competency,       │                   │
│  │  experience, role, availability      │                   │
│  └──────────────────┬───────────────────┘                   │
│                     │ structured JSON                        │
└─────────────────────┼────────────────────────────────────────┘
                      │ HTTPS + OAuth 2.0
                      ▼
┌──────────────────────────────────────────────────────────────┐
│              Your FastAPI Server (Azure App Service)          │
│                                                              │
│  POST /recommend ──→ Hard Filter ──→ Score ──→ Rank          │
│                                                              │
│  Returns: ranked candidates + score breakdowns               │
└──────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│                    Microsoft 365 Copilot                      │
│                                                              │
│  ┌──────────────────────────────────────┐                   │
│  │  Copilot LLM (replaces your formatter)│                   │
│  │  Formats API response into natural    │                   │
│  │  language for the user                │                   │
│  └──────────────────────────────────────┘                   │
│                                                              │
│  "Here are the top matches: Grace Okafor scored 0.99..."    │
└──────────────────────────────────────────────────────────────┘
```

## What Changed vs. Current Architecture

| Component | Before (Streamlit/CLI) | After (Copilot 365) |
|---|---|---|
| NL Parser | Your `chat/parser.py` | Copilot's built-in LLM |
| Orchestrator | Your `chat/orchestrator.py` | Copilot's plugin runtime |
| Response Formatter | Your `chat/formatter.py` | Copilot's built-in LLM |
| Recommendation Engine | `app/recommender.py` | **Unchanged** |
| API Layer | `app/main.py` | **Unchanged** (+ OAuth added) |
| Data Layer | `data/employees.json` | **Unchanged** |
| UI | Streamlit / CLI | Teams / Word / Copilot chat |

The engine, API, and data layer are completely untouched. Only the chat
interface layer is swapped from Streamlit to Copilot.
