import asyncio
from datetime import datetime

# Database
from database import get_all_farmers

# AI Agent
from agent import generate_morning_brief, send_text_via_bridge

async def morning_briefing_job():
    """
    Runs one full batch of proactive morning briefings
    for all farmers in the database.
    """
    print("🌅 Starting Morning Briefing Job...")

    farmers = get_all_farmers()
    print(f"📋 Found {len(farmers)} farmers in DB")

    for farmer in farmers:
        try:
            phone = farmer.get("phone")
            lat = farmer.get("lat")
            lon = farmer.get("lon")

            # Fallback if location is nested
            if not lat or not lon:
                location = farmer.get("location", {})
                lat = location.get("lat")
                lon = location.get("lon")

            if not lat or not lon or not phone:
                print(f"⚠️ Skipping farmer {farmer.get('name', 'Unknown')} (missing phone/location)")
                continue

            print(f"🔄 Generating briefing for {phone}")

            # 🔥 Generate the advisory text
            message = await generate_morning_brief(farmer)

            # 📲 Send WhatsApp message via the existing bridge function in agent.py
            await send_text_via_bridge(phone, message)

            # Rate limiting to be safe
            await asyncio.sleep(1.2)

        except Exception as e:
            print(f"❌ Error sending briefing to {farmer.get('phone')}: {e}")

    print("✅ Morning Briefing Job Completed")


async def scheduler_loop():
    """
    Background scheduler loop.
    Triggers the morning briefing every day at 6:00 AM.
    """
    print("⏰ Scheduler loop started")

    while True:
        now = datetime.now()

        # Run at 6:00 AM
        if now.hour == 6 and now.minute == 0:
            print("⏳ Triggering scheduled morning briefing")
            await morning_briefing_job()

            # Sleep 60 seconds to avoid duplicate execution
            await asyncio.sleep(60)

        # Check every 20 seconds
        await asyncio.sleep(20)