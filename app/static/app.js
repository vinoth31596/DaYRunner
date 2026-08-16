let seconds=50*60, initialSeconds=50*60, handle=null;
let totalSessions=3, currentSession=1, breakMinutes=10, phase='focus';
const timer=document.getElementById('timer');
const statusEl=document.getElementById('sessionStatus');
function val(id, fallback){const el=document.getElementById(id); return el?Number(el.value)||fallback:fallback}
function syncSettings(){if(handle)return; initialSeconds=val('sessionMinutes',50)*60; seconds=initialSeconds; totalSessions=Math.max(1,val('sessionCount',3)); breakMinutes=Math.max(1,val('breakMinutes',10)); currentSession=1; phase='focus'; render()}
function render(){if(timer)timer.textContent=String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0'); if(statusEl)statusEl.textContent=phase==='focus'?`Session ${currentSession} of ${totalSessions}`:`Break before session ${currentSession+1}`}
function startTimer(){if(handle)return; totalSessions=Math.max(1,val('sessionCount',totalSessions)); breakMinutes=Math.max(1,val('breakMinutes',breakMinutes)); handle=setInterval(tick,1000)}
async function tick(){if(seconds>0){seconds--;render();return} pauseTimer(); if(phase==='focus'){await saveFocus(); notify(`Focus session ${currentSession} of ${totalSessions} complete.`); if(currentSession>=totalSessions){notify('All focus sessions complete. Great work!'); resetTimer(); return} phase='break'; seconds=breakMinutes*60; render(); startTimer()} else {currentSession++; phase='focus'; initialSeconds=val('sessionMinutes',50)*60; seconds=initialSeconds; notify(`Break complete. Starting session ${currentSession} of ${totalSessions}.`); render(); startTimer()}}
function pauseTimer(){clearInterval(handle);handle=null}
function resetTimer(){pauseTimer(); currentSession=1; phase='focus'; initialSeconds=val('sessionMinutes',50)*60; seconds=initialSeconds; totalSessions=Math.max(1,val('sessionCount',3)); breakMinutes=Math.max(1,val('breakMinutes',10));render()}
function skipPhase(){pauseTimer(); seconds=0; tick()}
async function saveFocus(){const name=document.getElementById('focusName')?.value||'Focus';const day=document.getElementById('activeDay')?.value;const mins=val('sessionMinutes',50);try{await fetch('/api/focus',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,day,minutes:mins})})}catch(e){console.log(e)}}
function notify(body){if('Notification'in window&&Notification.permission==='granted')new Notification('Vinoth OS',{body})}
async function enableNotifications(){if('Notification'in window){let p=await Notification.requestPermission();document.getElementById('notify').textContent=p==='granted'?'Reminders enabled':'Notifications not enabled'}}
['sessionMinutes','sessionCount','breakMinutes'].forEach(id=>document.getElementById(id)?.addEventListener('change',syncSettings));
if('serviceWorker'in navigator)navigator.serviceWorker.register('/static/sw.js');render();
function b64ToUint8Array(s){const pad='='.repeat((4-s.length%4)%4),b=(s+pad).replace(/-/g,'+').replace(/_/g,'/'),raw=atob(b);return Uint8Array.from([...raw].map(c=>c.charCodeAt(0)))}
async function enablePush(){const out=document.getElementById('pushStatus');try{if(!('serviceWorker'in navigator)||!('PushManager'in window))throw Error('Web Push is not supported here.');if(!window.FOCUSFLOW_VAPID_PUBLIC)throw Error('Server VAPID keys are not configured yet. See README.');const p=await Notification.requestPermission();if(p!=='granted')throw Error('Notification permission was not granted.');const reg=await navigator.serviceWorker.ready;let sub=await reg.pushManager.getSubscription();if(!sub)sub=await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:b64ToUint8Array(window.FOCUSFLOW_VAPID_PUBLIC)});const r=await fetch('/api/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(sub.toJSON())});if(!r.ok)throw Error('Could not save push subscription.');out.textContent='Push reminders enabled on this device.'}catch(e){out.textContent=e.message}}
async function testPush(){const out=document.getElementById('pushStatus');try{const r=await fetch('/api/push/test',{method:'POST'}),d=await r.json();out.textContent=d.sent?`Test sent to ${d.sent} subscribed device(s).`:'No push sent. Enable push and configure VAPID keys first.'}catch(e){out.textContent=e.message}}


// Complete/uncomplete schedule items without reloading the page.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.toggle-form').forEach((form) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = form.querySelector('.check');
      const activity = form.closest('.activity');
      if (!button || !activity || button.disabled) return;

      button.disabled = true;
      try {
        const response = await fetch(form.action, {
          method: 'POST',
          body: new FormData(form),
          headers: {'X-Requested-With': 'XMLHttpRequest'}
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        activity.classList.toggle('done', result.completed);
        button.textContent = result.completed ? '✓' : '○';
        button.setAttribute('aria-pressed', result.completed ? 'true' : 'false');
        const ring = document.getElementById('progressRing');
        if (ring) ring.textContent = `${result.progress}%`;
      } catch (error) {
        console.error('Could not update activity:', error);
        alert('Could not save this activity. Please try again.');
      } finally {
        button.disabled = false;
      }
    });
  });
});


// Delete schedule items without reloading or changing the current scroll position.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.delete-form').forEach((form) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const activity = form.closest('.activity');
      const button = form.querySelector('.delete');
      const title = form.dataset.activityTitle || 'this activity';
      if (!activity || !button || button.disabled) return;
      if (!window.confirm(`Delete ${title}?`)) return;

      button.disabled = true;
      try {
        const response = await fetch(form.action, {
          method: 'POST',
          headers: {'X-Requested-With': 'XMLHttpRequest'}
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        activity.remove();
        const ring = document.getElementById('progressRing');
        if (ring && Number.isFinite(result.progress)) ring.textContent = `${result.progress}%`;
        const count = document.querySelector('.section-title span');
        if (count) {
          const remaining = document.querySelectorAll('.activity').length;
          count.textContent = `${remaining} item${remaining === 1 ? '' : 's'}`;
        }
      } catch (error) {
        console.error('Could not delete activity:', error);
        alert('Could not delete this activity. Please try again.');
        button.disabled = false;
      }
    });
  });
});


// Toggle whole-day goals without reloading or moving the page.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.habit-form').forEach((form) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const card = form.querySelector('.habit-card');
      const check = form.querySelector('.habit-check');
      const detail = card?.querySelector('small');
      if (!card || !check || card.disabled) return;
      card.disabled = true;
      try {
        const response = await fetch(form.action,{method:'POST',body:new FormData(form),headers:{'X-Requested-With':'XMLHttpRequest'}});
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        card.classList.toggle('done', result.completed);
        card.setAttribute('aria-pressed', result.completed ? 'true' : 'false');
        check.textContent = result.completed ? '✓' : '○';
        if (detail) detail.textContent = result.completed ? 'Done for today' : 'Tap when completed';
      } catch (error) { console.error(error); alert('Could not save this daily goal. Please try again.'); }
      finally { card.disabled = false; }
    });
  });
});
