import datetime
import flask
import lxml.cssselect, lxml.html
import urllib.error, urllib.request

from benisify import benisify

app = flask.Flask(__name__)
app.config.from_object(__name__)

static = ('.gif', '.png', '.jpg', '.ico', '.css', '.txt')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_page(path):
    baseurl = 'https://news.ycombinator.com'
    url = '{}/{}?{}'.format(baseurl, path, flask.request.query_string.decode('utf-8'))

    if path.endswith(static) and 'If-Modified-Since' in flask.request.headers:
        ims = datetime.datetime.strptime(flask.request.headers['If-Modified-Since'], '%Y-%m-%d %H:%M:%S.%f')
        if datetime.datetime.now() - ims < datetime.timedelta(minutes=10):
            return flask.Response(status=304)

    page = get_cache(url)
    if page is None:
        if path.endswith(static):
            page = get_url(url)
            set_cache(url, page, life=10)
        else:
            page = correct(get_url(url))
            set_cache(url, page)
    return page

def get_url(url):
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    try:
        data = opener.open(url).read()
    except urllib.error.HTTPError as e:
        flask.abort(e.code)
            
    return data

def correct(html_string):
    hparser = lxml.html.HTMLParser(encoding='utf-8')
    htree = lxml.html.document_fromstring(html_string, parser=hparser)

    # ``Correct'' the links, navbar, title, and comments
    sel = lxml.cssselect.CSSSelector('.title a, .pagetop > a, a[href="news"], title, .comment > span, .comment p')
    for t in sel(htree):
        if t is not None and t.text:
            t.text = benisify(t.text)

    # Fix for post-pre text sometimes not getting its own virtual text node
    sel = lxml.cssselect.CSSSelector('.comment font > pre')
    for t in sel(htree):
        if t is not None and t.tail:
            t.tail = benisify(t.tail)

    return lxml.html.tostring(htree)

# Cache functions
cache = {}

def get_cache(key):
    if key in cache:
        if datetime.datetime.now() - cache[key]['time'] < datetime.timedelta(minutes=cache[key]['life']):
            return cache[key]['content']
    return None

def set_cache(key, value, life=2):
    cache[key] = { 'time': datetime.datetime.now(),
                   'content': value,
                   'life': life }
    return True

# Don't even
@app.route('/login')
def return_404():
    flask.abort(404)


@app.after_request
def add_cache_headers(response):
    response.headers['Cache-Control'] = 'public, max-age=240'
    response.headers.add('Last-Modified', datetime.datetime.now())
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0')
