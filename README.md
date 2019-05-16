GAE Collerated Logger
===

Collerated request logger for GAE python3 flexible|standard environment

Install
---

from PyPI
```
pip install gaecl
```

from github
```
pip install --user git+https://github.com/takashi8/gaecl
```

Use as WSGI Middleware
---

```python
from gaecl import RequestLoggerMiddleware

# app: WSGI app instance

app = Flask(__name__)
app = RequestLoggerMiddleware(
    app,
    loglevel='INFO',
    project=os.getenv('GOOGLE_CLOUD_PROJECT'),
    module=os.getenv('GAE_SERVICE'),
    version=os.getenv('GAE_VERSION'),
)

@app.route('/')
def log():
    logging.info('info log')
    logging.warn('warn log')
    logging.error('error log')
    logging.critical('critical log')
    return 'ok'
```
