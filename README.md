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

See collerated log on cloud console
---

Choose **app** log on console to show parent log.
You can also see each child log separately by adding **app_child**.

![choose app log](https://user-images.githubusercontent.com/2031193/57907426-5eb8dd80-78b8-11e9-9b82-ac329ea12708.png "Choose app log")

Now your logs in a single request is collerated.

![collerated log](https://user-images.githubusercontent.com/2031193/57907442-68dadc00-78b8-11e9-9066-0fbd43a265ee.png "Collerated log")

Thanks for using
---
If you like this, a star to the [github repo](https://github.com/takashi8/gaecl) encourages me a lot;)
