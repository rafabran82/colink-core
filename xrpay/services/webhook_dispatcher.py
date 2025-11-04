import hmac, hashlib, asyncio
import httpx
from xrpay.repos import next_pending_outbox, mark_delivered, requeue

class WebhookDispatcher:
    async def run(self):
        while True:
            job = next_pending_outbox()
            if not job:
                await asyncio.sleep(0.5)
                continue
            await self._deliver(job)

    async def _deliver(self, job):
        # No webhook registered -> drain
        if not job.webhook or not job.webhook.url:
            mark_delivered(job.id)
            return

        headers = {"Content-Type": "application/json"}
        if job.webhook.secret:
            sig = hmac.new(job.webhook.secret.encode(), job.payload_json.encode(), hashlib.sha256).hexdigest()
            headers["X-XRPay-Hook-Signature"] = sig

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(job.webhook.url, content=job.payload_json, headers=headers)
            if 200 <= r.status_code < 300:
                mark_delivered(job.id)
            else:
                requeue(job.id)
        except Exception:
            requeue(job.id)
