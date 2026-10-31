"""Instant Flow: user-owned case studies and published project pages."""
import os,json,sqlite3,uuid,re,io
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlparse
from flask import Blueprint,request,jsonify,session,render_template,abort,send_file
from werkzeug.utils import secure_filename

flow=Blueprint('flow',__name__)
ROOT=Path(__file__).resolve().parent
DB=ROOT/'sentinel.db'
MEDIA=ROOT/'flow_media'; MEDIA.mkdir(exist_ok=True)
ALLOWED={'png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','webp':'image/webp','gif':'image/gif','mp4':'video/mp4','webm':'video/webm'}
MAX_MEDIA=25*1024*1024

def db():
 c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE IF NOT EXISTS flow_projects(id TEXT PRIMARY KEY,owner INTEGER NOT NULL,slug TEXT UNIQUE NOT NULL, data TEXT NOT NULL,published INTEGER NOT NULL DEFAULT 0,created TEXT NOT NULL,updated TEXT NOT NULL)')
 c.execute('CREATE TABLE IF NOT EXISTS flow_media(id TEXT PRIMARY KEY,project TEXT NOT NULL,owner INTEGER NOT NULL,filename TEXT NOT NULL,original TEXT NOT NULL,mimetype TEXT NOT NULL,created TEXT NOT NULL)')
 return c

def stamp():return datetime.now(timezone.utc).isoformat()
def clean(x,n=2000):return str(x or '').strip()[:n]
def valid_url(s):
 if not s:return True
 try:
  p=urlparse(s)
  return p.scheme in ('https','http') and bool(p.hostname) and not p.username and not p.password and len(s)<2048
 except ValueError:return False

def normalize(raw):
 if not isinstance(raw,dict):raise ValueError('Invalid project details')
 fields=['name','description','live_url','github_url','technologies','ai_tools','human_work','ai_assisted','ai_generated','third_party','team_work','challenges','solutions','deployment','results','intro']
 d={k:clean(raw.get(k),5000 if k in ('description','challenges','solutions','human_work','ai_assisted','ai_generated','team_work','results') else 1500) for k in fields}
 if not d['name']:raise ValueError('Project name is required')
 for k in ('live_url','github_url'):
  if not valid_url(d[k]):raise ValueError(k+' must be a valid HTTP(S) URL')
 rawp=raw.get('percentages') or {};d['percentages']={}
 if not isinstance(rawp,dict):rawp={}
 for k in ('human','assisted','generated','third_party','team'):
  v=rawp.get(k,'')
  if v!='' and v is not None:
   try:
    v=float(v)
    if not 0<=v<=100:raise ValueError()
   except (ValueError,TypeError):raise ValueError('Contribution percentages must be between 0 and 100')
   d['percentages'][k]=v
 steps=raw.get('timeline') or []
 if not isinstance(steps,list):raise ValueError('Invalid timeline')
 d['timeline']=[{'title':clean(x.get('title'),120),'date':clean(x.get('date'),40),'detail':clean(x.get('detail'),1500)} for x in steps[:60] if isinstance(x,dict)]
 return d

def mine(pid):
 with db() as c:return c.execute('SELECT * FROM flow_projects WHERE id=? AND owner=?',(pid,session['uid'])).fetchone()

def payload(row):
 d=json.loads(row['data']);d.update(id=row['id'],slug=row['slug'],published=bool(row['published']),created=row['created'],updated=row['updated'])
 return d


# URL-first import. Only GitHub's fixed API host is contacted; arbitrary sites are never fetched.
def import_from_url(value):
 from urllib.parse import urlsplit
 from ipaddress import ip_address
 import requests
 u=urlsplit(value.strip())
 if u.scheme not in ('http','https') or not u.hostname or u.username or u.password or u.port not in (None,80,443):
  raise ValueError('Enter a valid public HTTP(S) website or GitHub repository URL')
 host=u.hostname.lower().rstrip('.')
 if host in ('localhost',) or host.endswith(('.local','.internal','.localhost')):
  raise ValueError('Local or private addresses are not supported')
 try:
  ip_address(host)
  raise ValueError('IP address URLs are not supported')
 except ValueError as e:
  if str(e)=='IP address URLs are not supported':raise
 if len(value)>2048:raise ValueError('URL is too long')
 if host not in ('github.com','www.github.com') and (not '.' in host or any(not part or not re.fullmatch(r'[a-z0-9-]+',part) for part in host.split('.'))):
  raise ValueError('Invalid public domain')
 parts=[x for x in u.path.strip('/').split('/') if x]
 d={'name':host,'description':'Imported from '+host+'. Add a project description and verify the details.','live_url':value.strip(),'github_url':'','technologies':'','ai_tools':'','timeline':[],'percentages':{},'intro':'','human_work':'','ai_assisted':'','ai_generated':'','third_party':'','team_work':'','challenges':'','solutions':'','deployment':'','results':''}
 evidence={'source':'website_url','detected':['Submitted website URL and hostname'],'not_verified':['Website contents, authorship, development history, AI contributions and ownership']}
 if host in ('github.com','www.github.com'):
  if len(parts)<2 or not all(re.fullmatch(r'[A-Za-z0-9_.-]+',v) for v in parts[:2]):
   raise ValueError('Enter a GitHub repository URL such as https://github.com/owner/repository')
  owner,repo=parts[:2];repo=repo.removesuffix('.git')
  if not repo:raise ValueError('Invalid GitHub repository name')
  api='https://api.github.com/repos/'+owner+'/'+repo
  try:
   r=requests.get(api,headers={'Accept':'application/vnd.github+json','User-Agent':'InstantFlow/1.0'},timeout=7,allow_redirects=False)
   if r.status_code==404:raise ValueError('GitHub repository not found or not public')
   if r.status_code!=200:raise ValueError('GitHub metadata temporarily unavailable (HTTP '+str(r.status_code)+')')
   info=r.json()
  except requests.RequestException:raise ValueError('GitHub could not be reached. Please retry.')
  d.update(name=clean(info.get('name') or repo,150),description=clean(info.get('description') or 'Public GitHub repository',1500),github_url=clean(info.get('html_url') or value,1500),live_url=clean(info.get('homepage'),1500),technologies=clean(info.get('language'),1500))
  evidence={'source':'github_public_api','detected':['Repository name','Repository description (if provided)','Primary language (if provided)','Repository and homepage URLs'],'not_verified':['Human/AI contribution percentages','Authorship beyond GitHub metadata','Development milestones and challenges']}
  if d['live_url'] and not valid_url(d['live_url']):d['live_url']=''
  # Import language distribution when available, without making the request mandatory.
  try:
   lr=requests.get('https://api.github.com/repos/'+owner+'/'+repo+'/languages',headers={'Accept':'application/vnd.github+json','User-Agent':'InstantFlow/1.0'},timeout=5,allow_redirects=False)
   if lr.ok and isinstance(lr.json(),dict):d['technologies']=', '.join(list(lr.json())[:20])
  except (requests.RequestException,ValueError):pass
  d['timeline']=[{'title':'Repository created','date':clean(info.get('created_at'),40)[:10],'detail':'Date reported by the GitHub API; not proof of when development began.'}] if info.get('created_at') else []
 return normalize(d),evidence

@flow.post('/api/flow/import')
def import_project():
 body=request.get_json(silent=True) or {}
 value=clean(body.get('url'),2049)
 try:d,evidence=import_from_url(value)
 except ValueError as e:return jsonify(error=str(e)),400
 pid=uuid.uuid4().hex;slug=(re.sub(r'[^a-z0-9]+','-',d['name'].lower()).strip('-')[:45] or 'project')+'-'+pid[:8]
 d['import_evidence']=evidence
 with db() as c:c.execute('INSERT INTO flow_projects VALUES(?,?,?,?,?,?,?)',(pid,session['uid'],slug,json.dumps(d),0,stamp(),stamp()))
 return jsonify(project={**d,'id':pid,'slug':slug,'published':False},evidence=evidence),201

@flow.get('/api/flow/projects')
def projects():
 with db() as c:rows=c.execute('SELECT * FROM flow_projects WHERE owner=? ORDER BY updated DESC',(session['uid'],)).fetchall()
 return jsonify(projects=[payload(r) for r in rows])

@flow.post('/api/flow/projects')
def create():
 try:d=normalize(request.get_json(silent=True) or {})
 except ValueError as e:return jsonify(error=str(e)),400
 pid=uuid.uuid4().hex;slug=re.sub(r'[^a-z0-9]+','-',d['name'].lower()).strip('-')[:45] or 'project';slug+='-'+pid[:8]
 with db() as c:c.execute('INSERT INTO flow_projects VALUES(?,?,?,?,?,?,?)',(pid,session['uid'],slug,json.dumps(d),0,stamp(),stamp()))
 return jsonify(project={**d,'id':pid,'slug':slug,'published':False}),201

@flow.route('/api/flow/projects/<pid>',methods=['GET','PUT','DELETE'])
def project(pid):
 row=mine(pid)
 if not row:return jsonify(error='Project not found'),404
 if request.method=='GET':return jsonify(project=payload(row))
 if request.method=='DELETE':
  with db() as c:
   files=c.execute('SELECT filename FROM flow_media WHERE project=? AND owner=?',(pid,session['uid'])).fetchall()
   c.execute('DELETE FROM flow_media WHERE project=?',(pid,));c.execute('DELETE FROM flow_projects WHERE id=?',(pid,))
  for f in files:(MEDIA/f['filename']).unlink(missing_ok=True)
  return jsonify(ok=True)
 try:d=normalize(request.get_json(silent=True) or {})
 except ValueError as e:return jsonify(error=str(e)),400
 with db() as c:c.execute('UPDATE flow_projects SET data=?,updated=? WHERE id=?',(json.dumps(d),stamp(),pid))
 return jsonify(project={**d,'id':pid,'slug':row['slug'],'published':bool(row['published'])})

@flow.post('/api/flow/projects/<pid>/publish')
def publish(pid):
 row=mine(pid)
 if not row:return jsonify(error='Project not found'),404
 body=request.get_json(silent=True) or {};enabled=bool(body.get('published'))
 with db() as c:c.execute('UPDATE flow_projects SET published=?,updated=? WHERE id=?',(int(enabled),stamp(),pid))
 return jsonify(ok=True,published=enabled,url='/flow/'+row['slug'])

@flow.get('/api/flow/projects/<pid>/media')
def media_list(pid):
 if not mine(pid):return jsonify(error='Project not found'),404
 with db() as c:rows=c.execute('SELECT id,original,mimetype FROM flow_media WHERE project=? ORDER BY created',(pid,)).fetchall()
 return jsonify(media=[dict(r) for r in rows])

@flow.post('/api/flow/projects/<pid>/media')
def upload_media(pid):
 if not mine(pid):return jsonify(error='Project not found'),404
 f=request.files.get('file')
 if not f:return jsonify(error='Choose a screenshot or video'),400
 ext=Path(secure_filename(f.filename or '')).suffix.lower().lstrip('.')
 if ext not in ALLOWED:return jsonify(error='Supported files: PNG, JPG, WEBP, GIF, MP4, WEBM'),400
 content=f.read(MAX_MEDIA+1)
 if len(content)>MAX_MEDIA:return jsonify(error='File exceeds 25 MB'),413
 if not content:return jsonify(error='Empty file'),400
 # Signature checks prevent HTML disguised as an image/video from being served.
 signatures={'png':content.startswith(b'\x89PNG\r\n\x1a\n'),'jpg':content.startswith(b'\xff\xd8\xff'),'jpeg':content.startswith(b'\xff\xd8\xff'),'gif':content.startswith((b'GIF87a',b'GIF89a')),'webp':content.startswith(b'RIFF') and content[8:12]==b'WEBP','mp4':content[4:8]==b'ftyp','webm':content.startswith(b'\x1a\x45\xdf\xa3')}
 if not signatures[ext]:return jsonify(error='File content does not match its extension'),400
 mid=uuid.uuid4().hex;filename=mid+'.'+ext;(MEDIA/filename).write_bytes(content)
 with db() as c:c.execute('INSERT INTO flow_media VALUES(?,?,?,?,?,?,?)',(mid,pid,session['uid'],filename,clean(f.filename,180),ALLOWED[ext],stamp()))
 return jsonify(media={'id':mid,'original':clean(f.filename,180),'mimetype':ALLOWED[ext]}),201

@flow.delete('/api/flow/projects/<pid>/media/<mid>')
def delete_media(pid,mid):
 if not mine(pid):return jsonify(error='Project not found'),404
 with db() as c:
  row=c.execute('SELECT filename FROM flow_media WHERE id=? AND project=? AND owner=?',(mid,pid,session['uid'])).fetchone()
  if not row:return jsonify(error='Media not found'),404
  c.execute('DELETE FROM flow_media WHERE id=?',(mid,))
 (MEDIA/row['filename']).unlink(missing_ok=True)
 return jsonify(ok=True)

@flow.get('/flow/<slug>')
def public_page(slug):
 with db() as c:row=c.execute('SELECT * FROM flow_projects WHERE slug=?',(slug,)).fetchone()
 if not row or (not row['published'] and session.get('uid')!=row['owner']):abort(404)
 with db() as c:files=c.execute('SELECT id,original,mimetype FROM flow_media WHERE project=? ORDER BY created',(row['id'],)).fetchall()
 return render_template('flow_public.html',project=payload(row),media=[dict(x) for x in files],preview=not bool(row['published']))

@flow.get('/flow/media/<mid>')
def public_media(mid):
 with db() as c:
  row=c.execute('SELECT m.*,p.published FROM flow_media m JOIN flow_projects p ON p.id=m.project WHERE m.id=?',(mid,)).fetchone()
 if not row or (not row['published'] and session.get('uid')!=row['owner']):abort(404)
 return send_file(MEDIA/row['filename'],mimetype=row['mimetype'],as_attachment=False,download_name=row['original'],max_age=3600)
