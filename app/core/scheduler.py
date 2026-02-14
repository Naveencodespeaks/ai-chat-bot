from apscheduler.schedulers.background import BackgroundScheduler
from app.actions.sla_monitor import check_sla_breach
from app.db.session import SessionLocal


def start_scheduler():

    scheduler = BackgroundScheduler()

    def job():
        db = SessionLocal()
        check_sla_breach(db)
        db.close()

    scheduler.add_job(job, "interval", minutes=5)
    scheduler.start()
