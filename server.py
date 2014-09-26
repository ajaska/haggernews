from flask import Flask, request, url_for, abort 
import urllib2
import lxml.html
from benisify import benisify

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_page(path):
    baseurl = 'https://news.ycombinator.com'
    url = '%s/%s?%s' % (baseurl, path, request.query_string)

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    raw_data = opener.open(url).read()

    if(path.endswith(('.gif', '.png','.jpg','.ico','.css'))):
        return raw_data

    data = lxml.html.document_fromstring(raw_data)

    c = data.find_class('title')
    c = [e.find('a') for e in c]
    for e in c:
        if e is not None:
            e.text = benisify(e.text)

    c = data.find_class('comment')
    c = [e.find('font') for e in c]
    for e in c:
        if e is not None and e.text:
            e.text = benisify(e.text)
            for ep in e.findall('p'):
                if ep is not None and ep.text:
                    ep.text = benisify(ep.text) 

    return lxml.html.tostring(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
