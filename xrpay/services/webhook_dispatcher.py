import aiohttp, hmac, hashlib, asyncio
from typing import Optional

class WebhookJob:
    def __init__(self, id: str, url: str, secret: str, payload_json: str):
        self.id = id
        self.url = url
        self.secret = secret
        self.payload_json = payload_json

class WebhookRepo:
    """Example interface stub"""
    async def next_pending(self) -> Optional[WebhookJob]: ...
    async def mark_delivered(self, job_id: str): ...
    async def requeue(self, job_id: str): ...

class WebhookDispatcher:
    def __init__(self, repo: WebhookRepo):
        self.repo = repo

    async def run(self):
        while True:
            job = await self.repo.next_pending()
            if not job:
                await asyncio.sleep(0.5)
                continue
            await self._deliver(job)

    async def _deliver(self, job: WebhookJob):
        sig = hmac.new(job.secret.encode(), job.payload_json.encode(), hashlib.sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-XRPay-Hook-Signature": sig
        }
        async with aiohttp.ClientSession() as s:
            r = await s.post(job.url, data=job.payload_json, headers=headers)
            if 200 <= r.status < 300:
                await self.repo.mark_delivered(job.id)
            else:
                await self.repo.requeue(job.id)

