import os, json, sqlite3, uuid, re, requests
from flask import Blueprint, request, jsonify, session
from pathlib import Path

x=Blueprint('instinct_x',__name__)
DB=Path(__file__).resolve().parent/'sentinel.db'

def init():
 with sqlite3.connect(DB) as c:
  c.execute('CREATE TABLE IF NOT EXISTS x_memory(id TEXT PRIMARY KEY, user_id INTEGER, title TEXT, content TEXT, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
  c.execute('CREATE INDEX IF NOT EXISTS x_memory_owner ON x_memory(user_id)')
init()

PROMPTS={
 'twin':'You are a configurable digital twin. Follow the provided persona traits; never claim to be the real person. Return JSON with keys twin_response, standard_response, differences (array of strings). Standard response should be neutral and independent of persona.',
 'debate':'Stage a balanced, evidence-conscious debate. Return JSON with keys advocate, skeptic, judge, questions (array). Judge must distinguish unverified claims from evidence and avoid invented citations.',
 'future':'Simulate branching hypothetical outcomes, not factual predictions. Return JSON with keys assumptions (array), branches (array of objects with name, outcome, risks, next_step), uncertainty.',
 'mission':'Create an executable-looking but PLANNING-ONLY mission. No external actions have been performed. Return JSON with keys objective, steps (array of objects with title, detail, dependency, requires_approval), limitations. Keep steps specific and practical.',
 'invention':'Return JSON with keys name, tagline, problem, users, differentiator, features (array), architecture (array), roadmap (array), risks (array). Make a feasible product concept.',
 'strategy':'Act as a fair strategy coach. Return JSON with keys scenario, options (array of objects with action, upside, downside), ai_choice, rationale, challenge_question. No fictitious objective scoring.',
 'lens':'Analyze the supplied image. Return JSON with keys objects (array), visible_text (array), visual_observations (array), uncertainty, manipulation_note. Do not claim to prove authenticity from appearance alone.'
}

def ai(messages, vision=False):
 key=os.getenv('GROQ_API_KEY','').strip()
 if not key:return None,'Configure GROQ_API_KEY on the server to enable this AI feature.'
 model=os.getenv('GROQ_VISION_MODEL','meta-llama/llama-4-scout-17b-16e-instruct') if vision else os.getenv('GROQ_MODEL','openai/gpt-oss-120b')
 try:
  r=requests.post('https://api.groq.com/openai/v1/chat/completions',headers={'Authorization':'Bearer '+key},json={'model':model,'messages':messages,'temperature':0.45,'max_tokens':1500,'response_format':{'type':'json_object'}},timeout=24)
  if r.status_code>=400:return None,'AI provider returned HTTP '+str(r.status_code)+'. Check model and API settings.'
  raw=r.json()['choices'][0]['message']['content'];return json.loads(raw),None
 except (requests.RequestException,ValueError,KeyError,IndexError) as e:return None,'AI request failed: '+str(e)[:150]

@x.route('/api/x/<mode>',methods=['POST'])
def run(mode):
 if mode not in PROMPTS:return jsonify(error='Unknown experience'),404
 data=request.get_json(silent=True) or {}
 text=str(data.get('text','')).strip()[:6000]
 if not text:return jsonify(error='Enter a prompt or question.'),400
 content=text
 if mode=='twin':content='PERSONA CONFIG: '+json.dumps(data.get('persona',{}))+'\nQUESTION: '+text
 if mode=='strategy':content='PLAYER CHOICE: '+str(data.get('choice','Not selected'))+'\nSCENARIO: '+text
 if mode=='lens':
  image=str(data.get('image',''))
  if not re.match(r'^data:image/(jpeg|png|webp);base64,',image) or len(image)>5_000_000:return jsonify(error='Upload a JPG, PNG, or WEBP image under 3 MB.'),400
  messages=[{'role':'system','content':PROMPTS[mode]},{'role':'user','content':[{'type':'text','text':text},{'type':'image_url','image_url':{'url':image}}]}]
 else:messages=[{'role':'system','content':PROMPTS[mode]},{'role':'user','content':content}]
 result,error=ai(messages,mode=='lens')
 if error:return jsonify(error=error),503
 return jsonify(result=result)

@x.route('/api/x/memory',methods=['GET','POST','DELETE'])
def memory():
 uid=session.get('uid')
 if request.method=='GET':
  with sqlite3.connect(DB) as c:
   c.row_factory=sqlite3.Row
   rows=c.execute('SELECT id,title,content,created FROM x_memory WHERE user_id=? ORDER BY created DESC LIMIT 100',(uid,)).fetchall()
  return jsonify(items=[dict(r) for r in rows])
 d=request.get_json(silent=True) or {}
 if request.method=='DELETE':
  with sqlite3.connect(DB) as c:c.execute('DELETE FROM x_memory WHERE id=? AND user_id=?',(str(d.get('id','')),uid))
  return jsonify(ok=True)
 title=str(d.get('title','')).strip()[:100];content=str(d.get('content','')).strip()[:4000]
 if not title or not content:return jsonify(error='Title and content required'),400
 with sqlite3.connect(DB) as c:
  count=c.execute('SELECT COUNT(*) FROM x_memory WHERE user_id=?',(uid,)).fetchone()[0]
  if count>=100:return jsonify(error='Memory limit reached (100 items). Delete an item first.'),400
  c.execute('INSERT INTO x_memory(id,user_id,title,content) VALUES(?,?,?,?)',(str(uuid.uuid4()),uid,title,content))
 return jsonify(ok=True)
