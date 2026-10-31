"""Conservative URL authenticity assessment. Does not fetch user-supplied URLs (SSRF-safe)."""
from flask import Blueprint, request, jsonify
from urllib.parse import urlsplit
import ipaddress, re, unicodedata, difflib

website_guardian = Blueprint('website_guardian', __name__)
OFFICIAL = {
 'oracle.com':'Oracle', 'wikipedia.org':'Wikipedia', 'wikimedia.org':'Wikimedia',
 'netflix.com':'Netflix', 'openai.com':'OpenAI', 'chatgpt.com':'ChatGPT',
 'groq.com':'Groq', 'console.groq.com':'Groq Console', 'brave.com':'Brave',
 'github.com':'GitHub', 'google.com':'Google', 'microsoft.com':'Microsoft',
 'apple.com':'Apple', 'amazon.com':'Amazon', 'python.org':'Python',
 'render.com':'Render', 'huggingface.co':'Hugging Face',
 'anthropic.com':'Anthropic', 'meta.com':'Meta', 'cloudflare.com':'Cloudflare',
 'paypal.com':'PayPal', 'linkedin.com':'LinkedIn', 'youtube.com':'YouTube',
 'instagram.com':'Instagram', 'ibm.com':'IBM', 'isro.gov.in':'ISRO',
 'gov.in':'Government of India (domain namespace)',
}
# Restrict broad namespaces from green automatic verification.
BROAD = {'gov.in'}
SUSPICIOUS_WORDS = ('login','verify','secure','support','account','update','wallet','payment','bonus','free','gift','reset')

def assessment(raw):
 if not isinstance(raw,str) or len(raw)>2048 or any(ord(c)<32 for c in raw):
  return {'error':'Enter one valid URL of at most 2048 characters.'},400
 raw=raw.strip()
 if not raw: return {'error':'Paste a website URL.'},400
 try:
  parsed=urlsplit(raw)
  if parsed.scheme.lower() not in ('http','https') or not parsed.netloc:
   return {'error':'Enter a complete http:// or https:// URL.'},400
  if parsed.username is not None or parsed.password is not None:
   return {'error':'URLs containing embedded credentials are not supported.'},400
  host=(parsed.hostname or '').lower().rstrip('.')
  port=parsed.port
  if not host or len(host)>253 or '..' in host: raise ValueError('invalid hostname')
  if host in ('localhost','localhost.localdomain') or host.endswith(('.localhost','.local','.internal','.test','.invalid','.example','.onion')):
   return {'error':'Private, test, and internal domains cannot be assessed.'},400
  try:
   addr=ipaddress.ip_address(host.strip('[]'))
   return {'error':'IP-address URLs are not eligible for website authenticity verification.'},400
  except ValueError: pass
  ascii_host=host.encode('idna').decode('ascii')
  if not re.fullmatch(r'(?=.{1,253}$)[a-z0-9-]+(?:\.[a-z0-9-]+)+',ascii_host) or any(x.startswith('-') or x.endswith('-') for x in ascii_host.split('.')):
   return {'error':'Invalid public domain format.'},400
 except (ValueError,UnicodeError):
  return {'error':'Invalid URL or domain.'},400
 issues=[]; tips=[]; evidence=[]
 if parsed.scheme.lower()!='https':
  issues.append('This link uses HTTP rather than HTTPS.');tips.append('Use HTTPS with a valid TLS certificate.')
 if port not in (None,80,443):
  issues.append('The URL uses an unusual network port.');tips.append('Confirm the port through the organization’s official documentation.')
 if ascii_host.startswith('xn--') or '.xn--' in ascii_host:
  issues.append('The domain uses internationalized (punycode) characters, which can conceal lookalikes.');tips.append('Verify the domain spelling from a trusted official source.')
 if len(ascii_host.split('.'))>4:
  issues.append('The URL has many subdomain levels.');tips.append('Check the registrable domain rather than a brand name in a subdomain.')
 if '@' in raw:
  issues.append('The link contains an @ symbol, which can mislead readers.');tips.append('Avoid links with embedded usernames or confusing authority components.')
 if any(w in ascii_host.split('.')[0].split('-') for w in SUSPICIOUS_WORDS):
  issues.append('The domain contains a term commonly used in phishing lures.');tips.append('Open the service from a bookmarked official website instead.')
 match=None
 for domain, brand in sorted(OFFICIAL.items(),key=lambda x:-len(x[0])):
  if ascii_host==domain or ascii_host.endswith('.'+domain):
   match=(domain,brand);break
 brand_mimic=None
 if not match:
  for domain,brand in OFFICIAL.items():
   if domain in BROAD:continue
   root=domain.split('.')[0]
   chunks=re.split(r'[.\-]',ascii_host)
   if root in chunks or (len(root)>4 and any(difflib.SequenceMatcher(None,root,c).ratio()>=0.78 for c in chunks if len(c)>3)):
    brand_mimic=(domain,brand);break
 if brand_mimic:
  issues.append('The domain resembles '+brand_mimic[1]+' but is not within its known official domain '+brand_mimic[0]+'.')
  tips.append('Use the official '+brand_mimic[1]+' domain: '+brand_mimic[0]+'.')
 if match and match[0] not in BROAD and parsed.scheme.lower()=='https' and not issues:
  status='green';title='Recognized official domain';confidence='High confidence in domain identity only'
  evidence.append('Domain belongs to the locally curated official-domain reference: '+match[0]+'.')
  evidence.append('HTTPS is specified in the URL (certificate and page were not tested).')
  tips.append('Continue to check page content and unexpected redirects before entering credentials.')
 elif brand_mimic or (issues and (len(issues)>=2 or parsed.scheme.lower()=='http')):
  status='amber';title='Suspicious — investigate before trusting';confidence='Heuristic warning, not proof of maliciousness'
 else:
  status='amber';title='Authenticity not independently verified';confidence='Insufficient evidence for official or malicious classification'
  if not issues:tips.append('Confirm this domain from the organization’s independently published official website.')
 if match and match[0] in BROAD:
  evidence.append('This is a broad domain namespace; individual sites require separate verification.')
 if not evidence:evidence.append('This offline assessment does not query threat intelligence, DNS, TLS, or live website content.')
 return {'status':status,'title':title,'domain':ascii_host,'scheme':parsed.scheme.lower(),
         'official_domain':match[0] if match and match[0] not in BROAD else None,
         'issues':issues,'evidence':evidence,'recommendations':list(dict.fromkeys(tips)),
         'confidence':confidence,'limitations':'A green result verifies only a curated domain match, not safety of every page. Red requires verified threat intelligence or confirmed malicious evidence; this offline checker does not claim that.'},200

@website_guardian.route('/api/website-guardian',methods=['POST'])
def check_website():
 payload=request.get_json(silent=True) or {}
 result,status=assessment(payload.get('url',''))
 return jsonify(result),status
