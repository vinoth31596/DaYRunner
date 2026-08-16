from pathlib import Path
from datetime import date, datetime, timedelta
import json, os
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from pywebpush import webpush, WebPushException
from .database import Base, engine, get_db, SessionLocal
from .models import Activity, ActivityLog, FocusSession, PushSubscription, ReminderDelivery, DailyHabitLog
BASE=Path(__file__).resolve().parent
app=FastAPI(title='Vinoth OS')
app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')
templates=Jinja2Templates(directory=BASE/'templates')

def format_time_12h(value):
    # Display stored HH:MM values as 12-hour AM/PM without changing DB storage.
    if not value:
        return ''
    try:
        return datetime.strptime(value, '%H:%M').strftime('%I:%M %p').lstrip('0')
    except (TypeError, ValueError):
        return value

templates.env.filters['time12'] = format_time_12h
Base.metadata.create_all(bind=engine)
TZ=os.getenv('FOCUSFLOW_TIMEZONE','America/New_York'); VAPID_PUBLIC=os.getenv('VAPID_PUBLIC_KEY',''); VAPID_PRIVATE=os.getenv('VAPID_PRIVATE_KEY',''); VAPID_SUBJECT=os.getenv('VAPID_SUBJECT','mailto:you@example.com')
DEFAULTS=[('Wake + water','06:30','06:35','Health'),('AG1','06:35','06:40','Health'),('Pre-gym snack','06:50','07:00','Health'),('Pre-workout','07:00','07:05','Gym'),('Gym','07:20','08:20','Gym'),('Breakfast + creatine','08:40','09:10','Health'),('Work','09:15','12:00','Work'),('Lunch','12:00','12:45','Personal'),('Work / meetings','12:45','15:30','Work'),('Break / walk','15:30','16:00','Relax'),('AI learning','16:00','17:30','Study'),('AI project','17:45','18:45','Study'),('Dinner','18:45','19:30','Personal'),('Personal time','19:30','20:30','Relax'),('Relaxation','20:30','21:30','Relax'),('Magnesium','21:30','21:35','Health'),('Wind down','21:35','22:15','Relax'),('Sleep','22:30','06:30','Sleep')]
def seed():
 db=SessionLocal()
 if db.query(Activity).count()==0:
  for x in DEFAULTS: db.add(Activity(title=x[0],start_time=x[1],end_time=x[2],category=x[3]))
  db.commit()
 db.close()
seed()
def selected_date(raw):
 try:return date.fromisoformat(raw) if raw else date.today()
 except:return date.today()
def day_data(db,d):
 acts=db.query(Activity).order_by(Activity.start_time).all(); logs={x.activity_id:x.completed for x in db.query(ActivityLog).filter(ActivityLog.log_date==d).all()}; rows=[{'id':a.id,'title':a.title,'start_time':a.start_time,'end_time':a.end_time,'category':a.category,'completed':logs.get(a.id,False),'reminder_enabled':a.reminder_enabled,'reminder_offset':a.reminder_offset} for a in acts]; done=sum(x['completed'] for x in rows); return rows,round(done/len(rows)*100) if rows else 0

HABITS=[('no_alcohol','No Alcohol Today','🍺'),('diet_done','Diet Done Today','🥗')]
def habit_data(db,d):
 logs={x.habit_key:x.completed for x in db.query(DailyHabitLog).filter(DailyHabitLog.log_date==d).all()}
 return [{'key':key,'title':title,'icon':icon,'completed':logs.get(key,False)} for key,title,icon in HABITS]
def habit_streak(db,key):
 d=date.today(); n=0
 for _ in range(3660):
  log=db.query(DailyHabitLog).filter_by(habit_key=key,log_date=d).first()
  if not log or not log.completed: break
  n+=1; d-=timedelta(days=1)
 return n

def streak(db,category=None):
 d=date.today(); n=0
 for _ in range(365):
  acts=db.query(Activity).filter(Activity.category==category).all() if category else db.query(Activity).all()
  ids=[a.id for a in acts]; ok=bool(ids) and db.query(ActivityLog).filter(ActivityLog.log_date==d,ActivityLog.activity_id.in_(ids),ActivityLog.completed==True).count()>0
  if not ok: break
  n+=1; d-=timedelta(days=1)
 return n
@app.get('/',response_class=HTMLResponse)
def home(request:Request,day:str|None=None,db:Session=Depends(get_db)):
 d=selected_date(day); acts,p=day_data(db,d); habits=habit_data(db,d); return templates.TemplateResponse('index.html',{'request':request,'activities':acts,'habits':habits,'progress':p,'day':d,'today':date.today(),'page':'today','vapid_public':VAPID_PUBLIC})
@app.get('/history',response_class=HTMLResponse)
def history(request:Request,day:str|None=None,period:str='week',range_filter:str|None=Query(default=None, alias='range'),db:Session=Depends(get_db)):
 # Accept older ?range= links without shadowing Python's built-in range() function.
 period = range_filter or period
 d=selected_date(day)
 today=date.today()
 # Range options: week, month, year, all (start-to-date).
 if period=='month':
  start=d.replace(day=1); label=d.strftime('%B %Y')
 elif period=='year':
  start=date(d.year,1,1); label=str(d.year)
 elif period=='all':
  first_log=db.query(ActivityLog.log_date).order_by(ActivityLog.log_date.asc()).first()
  first_focus=db.query(FocusSession.session_date).order_by(FocusSession.session_date.asc()).first()
  candidates=[x[0] for x in (first_log,first_focus) if x and x[0]]
  start=min(candidates) if candidates else d
  label=f'{start.strftime("%b %d, %Y")} – {d.strftime("%b %d, %Y")}'
 else:
  period='week'; start=d-timedelta(days=6); label=f'Last 7 days ending {d.strftime("%b %d")}'
 if start>d:start=d
 acts,p=day_data(db,d)
 total_days=(d-start).days+1
 raw=[]
 for i in range(total_days):
  x=start+timedelta(days=i); _,pp=day_data(db,x); f=sum(s.minutes for s in db.query(FocusSession).filter(FocusSession.session_date==x).all()); raw.append({'date':x,'progress':pp,'focus':f})
 focus=sum(x['focus'] for x in raw)
 gymids=[a.id for a in db.query(Activity).filter(Activity.title=='Gym').all()]
 gym=db.query(ActivityLog).filter(ActivityLog.log_date>=start,ActivityLog.log_date<=d,ActivityLog.activity_id.in_(gymids),ActivityLog.completed==True).count() if gymids else 0
 avg=round(sum(x['progress'] for x in raw)/len(raw)) if raw else 0
 # Keep charts readable by aggregating longer ranges.
 if period in ('week','month'):
  chart=[{'label':x['date'].strftime('%a') if period=='week' else x['date'].strftime('%d'),'progress':x['progress'],'date':x['date']} for x in raw]
 else:
  buckets={}
  for x in raw:
   key=(x['date'].year,x['date'].month); buckets.setdefault(key,[]).append(x)
  chart=[]
  for (y,m),items in sorted(buckets.items()):
   chart.append({'label':date(y,m,1).strftime('%b') if period=='year' else date(y,m,1).strftime('%b %y'),'progress':round(sum(i['progress'] for i in items)/len(items)),'date':items[-1]['date']})
 
 # Daily habit metrics for the selected period.
 habit_metrics={}
 for key,title,icon in HABITS:
  completed_days=db.query(DailyHabitLog).filter(DailyHabitLog.habit_key==key,DailyHabitLog.log_date>=start,DailyHabitLog.log_date<=d,DailyHabitLog.completed==True).count()
  habit_metrics[key]={'title':title,'icon':icon,'days':completed_days,'rate':round(completed_days/total_days*100) if total_days else 0,'streak':habit_streak(db,key)}
 return templates.TemplateResponse('history.html',{'request':request,'activities':acts,'habits':habit_data(db,d),'habit_metrics':habit_metrics,'progress':p,'day':d,'today':today,'days':chart,'focus_total':focus,'gym_total':gym,'avg':avg,'study_streak':streak(db,'Study'),'gym_streak':streak(db,'Gym'),'page':'history','range':period,'range_label':label,'range_days':total_days})

@app.post('/habit/{habit_key}/toggle')
def toggle_habit(habit_key:str,request:Request,day:str=Form(''),db:Session=Depends(get_db)):
 valid={x[0] for x in HABITS}
 if habit_key not in valid: raise HTTPException(status_code=404,detail='Habit not found')
 d=selected_date(day)
 log=db.query(DailyHabitLog).filter_by(habit_key=habit_key,log_date=d).first()
 if log is None:
  log=DailyHabitLog(habit_key=habit_key,log_date=d,completed=True); db.add(log)
 else: log.completed=not log.completed
 db.commit(); db.refresh(log)
 if request.headers.get('x-requested-with')=='XMLHttpRequest': return JSONResponse({'ok':True,'habit_key':habit_key,'completed':bool(log.completed),'day':d.isoformat()})
 return RedirectResponse(f'/?day={d.isoformat()}#daily-goals',303)

@app.post('/add')
def add(title:str=Form(...),start_time:str=Form(...),end_time:str=Form(''),category:str=Form('Personal'),reminder_enabled:bool=Form(False),reminder_offset:int=Form(0),db:Session=Depends(get_db)):
 db.add(Activity(title=title,start_time=start_time,end_time=end_time,category=category,reminder_enabled=reminder_enabled,reminder_offset=reminder_offset));db.commit();return RedirectResponse('/',303)
@app.post('/activity/{aid}/reminder')
def reminder(aid:int,enabled:bool=Form(False),offset:int=Form(0),db:Session=Depends(get_db)):
 a=db.get(Activity,aid)
 if a:a.reminder_enabled=enabled;a.reminder_offset=offset;db.commit()
 return RedirectResponse('/',303)
@app.post('/toggle/{aid}')
def toggle(aid:int,request:Request,day:str=Form(''),db:Session=Depends(get_db)):
 d=selected_date(day)
 activity=db.get(Activity,aid)
 if activity is None:
  raise HTTPException(status_code=404,detail='Activity not found')
 log=db.query(ActivityLog).filter_by(activity_id=aid,log_date=d).first()
 if log is None:
  log=ActivityLog(activity_id=aid,log_date=d,completed=True)
  db.add(log)
 else:
  log.completed=not log.completed
 db.commit()
 db.refresh(log)
 _, progress = day_data(db,d)
 # AJAX/fetch completion updates should not reload the page.
 if request.headers.get('x-requested-with') == 'XMLHttpRequest':
  return JSONResponse({'ok':True,'activity_id':aid,'completed':bool(log.completed),'progress':progress,'day':d.isoformat()})
 # Keep normal form behavior as a fallback when JavaScript is unavailable.
 return RedirectResponse(f'/?day={d.isoformat()}#activity-{aid}',303)
@app.post('/delete/{aid}')
def delete(aid:int, request:Request, db:Session=Depends(get_db)):
 a=db.get(Activity,aid)
 if not a:
  if request.headers.get('x-requested-with') == 'XMLHttpRequest':
   return JSONResponse({'ok':False,'detail':'Activity not found'},404)
  return RedirectResponse('/',303)
 db.query(ActivityLog).filter(ActivityLog.activity_id==aid).delete()
 db.delete(a)
 db.commit()
 _, progress = day_data(db, selected_date(None))
 if request.headers.get('x-requested-with') == 'XMLHttpRequest':
  return JSONResponse({'ok':True,'activity_id':aid,'progress':progress})
 return RedirectResponse('/',303)
@app.post('/api/focus')
def save_focus(payload:dict,db:Session=Depends(get_db)):
 db.add(FocusSession(session_date=selected_date(payload.get('day')),name=str(payload.get('name') or 'Focus')[:120],minutes=max(1,int(payload.get('minutes',25)))));db.commit();return {'ok':True}
@app.post('/api/push/subscribe')
def subscribe(payload:dict,db:Session=Depends(get_db)):
 ep=payload.get('endpoint');keys=payload.get('keys',{})
 if not ep or not keys.get('p256dh') or not keys.get('auth'):return JSONResponse({'ok':False},400)
 x=db.query(PushSubscription).filter_by(endpoint=ep).first()
 if x:x.p256dh=keys['p256dh'];x.auth=keys['auth']
 else:db.add(PushSubscription(endpoint=ep,p256dh=keys['p256dh'],auth=keys['auth']))
 db.commit();return {'ok':True}
@app.post('/api/push/test')
def test_push(db:Session=Depends(get_db)):
 sent=send_push(db,'Vinoth OS','Test reminder received successfully.','/');return {'ok':True,'sent':sent}
def send_push(db,title,body,url='/'):
 if not(VAPID_PUBLIC and VAPID_PRIVATE): return 0
 sent=0
 for s in db.query(PushSubscription).all():
  try:
   webpush({'endpoint':s.endpoint,'keys':{'p256dh':s.p256dh,'auth':s.auth}},json.dumps({'title':title,'body':body,'url':url}),vapid_private_key=VAPID_PRIVATE,vapid_claims={'sub':VAPID_SUBJECT});sent+=1
  except WebPushException as e:
   if getattr(e.response,'status_code',0) in (404,410):db.delete(s)
 db.commit();return sent
def check_reminders():
 db=SessionLocal()
 try:
  now=datetime.now(ZoneInfo(TZ)); today=now.date()
  for a in db.query(Activity).filter(Activity.reminder_enabled==True).all():
   try:h,m=map(int,a.start_time.split(':')); due=datetime(today.year,today.month,today.day,h,m,tzinfo=ZoneInfo(TZ))-timedelta(minutes=a.reminder_offset or 0)
   except:continue
   if due<=now<due+timedelta(minutes=2) and not db.query(ReminderDelivery).filter_by(activity_id=a.id,delivery_date=today).first():
    if send_push(db,'Vinoth OS',f'{a.title} · {format_time_12h(a.start_time)}',f'/?day={today.isoformat()}')>0:db.add(ReminderDelivery(activity_id=a.id,delivery_date=today));db.commit()
 finally:db.close()
scheduler=BackgroundScheduler(timezone=TZ);scheduler.add_job(check_reminders,'interval',minutes=1,id='reminders',replace_existing=True);scheduler.start()
@app.on_event('shutdown')
def shutdown(): scheduler.shutdown(wait=False)
