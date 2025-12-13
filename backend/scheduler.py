import asyncio
import os
from typing import Optional

# ✅ REQUIRED IMPORTS (per hackathon rules)
try:
    from database import get_all_farmers
    from agent import generate_morning_brief, send_text_via_bridge
except ImportError:
    from backend.database import get_all_farmers
    from backend.agent import generate_morning_brief, send_text_via_bridge


async def morning_briefing_job() -> int:
    """Send a proactive morning brief to every farmer in the DB.

    Returns number of messages attempted.
    """
    farmers = get_all_farmers() or []
    print(f"🌅 Morning Briefing Job: {len(farmers)} farmers")

    attempted = 0
    for farmer in farmers:
        try:
            phone = farmer.get("phone")
            if not phone:
                continue

            # Prefer the stored sender_jid (opt-in / established session)
            recipient = farmer.get("sender_jid") or farmer.get("last_sender_jid") or farmer.get("whatsapp_jid")
            if not recipient:
                # Without an established signal session, proactive sends may fail.
                # User can opt-in by sending one WhatsApp message to the bot first.
                continue

            msg = await generate_morning_brief(farmer)
            await send_text_via_bridge(recipient, msg)
            attempted += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"❌ Morning brief error for {farmer.get('phone')}: {e}")
    return attempted


async def scheduler_loop() -> None:
    """Runs once immediately (demo), then sleeps.

    You can override sleep with env var MORNING_BRIEF_SLEEP_SECONDS.
    """
    sleep_seconds: Optional[int]
    try:
        sleep_seconds = int(os.getenv("MORNING_BRIEF_SLEEP_SECONDS", "86400"))
    except ValueError:
        sleep_seconds = 86400

    print("⏰ Scheduler started")
    print("🚀 Running morning briefing immediately (startup demo)")
    await morning_briefing_job()

    while True:
        print(f"😴 Scheduler sleeping for {sleep_seconds}s")
        await asyncio.sleep(sleep_seconds)
        await morning_briefing_job()