"""title: FastAPI Tracking Pipeline
version: 0.1
author: you
description:  Sync chat turns with a FastAPI logging service.
requirements: requests
"""

import os, uuid, requests
from typing import Optional, List
from pydantic import BaseModel

class Pipeline:
    # --- editable values from WebUI (“Valves”) ---------------------------
    class Valves(BaseModel):
        backend_url: str = "https://aiapi.cybernautics.net"
        inject_history: bool = True
        history_prefix: str = "### Previous context"

    # --------------------------------------------------------------------
    def __init__(self):
        self.type  = "filter"              # runs before & after every call
        self.name  = "FastAPI Tracker"
        self.valves = self.Valves(
            **{
                "backend_url": os.getenv("FASTAPI_BACKEND_URL", "https://aiapi.cybernautics.net"),
            }
        )
        self.session = requests.Session()

    # ------- inlet: runs BEFORE the prompt hits the model ---------------
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        # 1) Identify chat
        chat_id = body.setdefault("metadata", {}).setdefault("chat_id", str(uuid.uuid4()))

        # 2) Push the user’s most-recent message to FastAPI
        last_user_msg = body["messages"][-1]
        self._post({"chat_id": chat_id, **last_user_msg})

        # 3) Pull existing history and inject (optional)
        if self.valves.inject_history:
            history = self._get(chat_id)
            if history:
                formatted = "\n".join(f'{m["role"]}: {m["content"]}' for m in history[-20:])
                body["messages"].insert(0, {
                    "role": "system",
                    "content": f"{self.valves.history_prefix}\n{formatted}"
                })

        return body

    # ------- outlet: runs AFTER the model finishes ----------------------
    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        chat_id = body.get("chat_id") or body.get("metadata", {}).get("chat_id")
        assistant_msg = body["messages"][-1]
        self._post({"chat_id": chat_id, **assistant_msg})
        return body

    # --------------------- helpers --------------------------------------
    def _post(self, payload: dict):
        try:
            self.session.post(f"{self.valves.backend_url}/api/log", json=payload, timeout=5)
        except Exception as e:
            print("[FastAPI-pipeline] POST failed:", e)

    def _get(self, chat_id: str) -> List[dict]:
        try:
            r = self.session.get(f"{self.valves.backend_url}/api/log/{chat_id}", timeout=5)
            return r.json() if r.ok else []
        except Exception as e:
            print("[FastAPI-pipeline] GET failed:", e)
            return []
