import aiohttp, hmac, hashlib, asyncio, json
from .repos import next_pending_outbox, mark_delivered, requeue

class WebhookDispatcher:
    async def run(self):
        while True:
            job = next_pending_outbox()
            if not job:
                await asyncio.sleep(0.5)
                continue
            await self._deliver(job)

    async def _deliver(self, job):
        # If job has a webhook with secret, sign; else send raw
        headers = {"Content-Type": "application/json"}
        secret = None
        if job.webhook and job.webhook.secret:
            secret = job.webhook.secret
            sig = hmac.new(secret.encode(), job.payload_json.encode(), hashlib.sha256).hexdigest()
            headers["X-XRPay-Hook-Signature"] = sig

        async with aiohttp.ClientSession() as s:
            r = await s.post(job.webhook.url if job.webhook else "", data=job.payload_json, headers=headers)
            if 200 <= r.status < 300:
                mark_delivered(job.id)
            else:
                requeue(job.id)
