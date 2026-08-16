from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text, UniqueConstraint
from datetime import datetime
from .database import Base
class Activity(Base):
    __tablename__='activities'; id=Column(Integer,primary_key=True); title=Column(String,nullable=False); start_time=Column(String,nullable=False); end_time=Column(String); category=Column(String,default='Personal'); recurring=Column(Boolean,default=True); reminder_enabled=Column(Boolean,default=False); reminder_offset=Column(Integer,default=0)
class ActivityLog(Base):
    __tablename__='activity_logs'; __table_args__=(UniqueConstraint('activity_id','log_date',name='uq_activity_date'),); id=Column(Integer,primary_key=True); activity_id=Column(Integer,nullable=False,index=True); log_date=Column(Date,nullable=False,index=True); completed=Column(Boolean,default=False)
class FocusSession(Base):
    __tablename__='focus_sessions'; id=Column(Integer,primary_key=True); session_date=Column(Date,nullable=False,index=True); name=Column(String,default='AI Study'); minutes=Column(Integer,default=25); created_at=Column(DateTime,default=datetime.utcnow)
class PushSubscription(Base):
    __tablename__='push_subscriptions'; id=Column(Integer,primary_key=True); endpoint=Column(Text,unique=True,nullable=False); p256dh=Column(Text,nullable=False); auth=Column(Text,nullable=False); created_at=Column(DateTime,default=datetime.utcnow)
class ReminderDelivery(Base):
    __tablename__='reminder_deliveries'; __table_args__=(UniqueConstraint('activity_id','delivery_date',name='uq_reminder_delivery'),); id=Column(Integer,primary_key=True); activity_id=Column(Integer,index=True,nullable=False); delivery_date=Column(Date,nullable=False,index=True); sent_at=Column(DateTime,default=datetime.utcnow)

class DailyHabitLog(Base):
    __tablename__='daily_habit_logs'
    __table_args__=(UniqueConstraint('habit_key','log_date',name='uq_habit_date'),)
    id=Column(Integer,primary_key=True)
    habit_key=Column(String,nullable=False,index=True)
    log_date=Column(Date,nullable=False,index=True)
    completed=Column(Boolean,default=False)
