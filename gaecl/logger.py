# -*- coding: utf-8 -*-

import logging
import threading
import datetime
import re
from werkzeug.wrappers import Request
from google.cloud import logging as gcloud_logging


class RequestLogger(object):
    """Logger class to generate collerated log
    """
    def __init__(
        self,
        trace,
        request_data=None,
        client=None,
        project=None,
        module=None,
        version=None,
        log_name=None,
        child_log_name=None,
    ):
        """
        Args:
            trace (str): Trace id for the request
            request_data (dict): Request information
            client (google.cloud.logging.Client): Log client for GAE
            project (str): Project id
            module (str): Module name
            version (str): Module version
            log_name (str): Parent log name in cloud console
            child_log_name (str): Child log name in cloud console

        Note:
            log_name should be different from child_log_name to be collerated
        """
        self.project = project
        self.module = module
        self.version = version

        self.request_data = request_data or {}
        self.trace = trace
        self.resource = self.get_resource()

        log_name = log_name or 'app'
        child_log_name = child_log_name or '{}_child'.format(log_name)
        client = client or gcloud_logging.Client(self.project)
        self.parent_logger = client.logger(log_name).batch()
        self.child_logger = client.logger(child_log_name).batch()
        self.created_at = datetime.datetime.now()
        self.max_sent_severity = None

    def get_resource(self):
        """Get server resource information
        Returns:
            dict: Resource information
        """
        resource = gcloud_logging.resource.Resource(
            type='gae_app',
            labels={
                'project_id': self.project,
                'module_id': self.module,
                'version_id': self.version,
            },
        )
        return resource

    def get_response_data(self, response):
        """Get response information
        Args:
            response: Response information
        Returns:
            dict: Updated response information
        """
        delta = (datetime.datetime.now() - self.created_at).total_seconds()
        res = {
            'latency': '{}s'.format(delta),
        }
        if not response:
            return res
        elif isinstance(response, dict):
            res.update(response)
            return res
        res.update({
            'responseSize': len(response.data),
            'status': response.status_code,
        })
        return res

    def commit(self):
        """Commit log to stackdriver
        """
        self.child_logger.commit()
        self.parent_logger.commit()

    def _log(
        self,
        severity,
        content,
        is_parent=False,
        response=None,
    ):
        """Record each log line
        Args:
            severity (str): Log severity
            content: Log content
            is_parent (bool): If the log is parent of colleration
            response: Response information
        """
        logger = self.parent_logger if is_parent else self.child_logger
        log_func = logger.log_text
        args = [content]
        if not content:
            log_func = logger.log_empty
            args = []
        elif isinstance(content, dict):
            log_func = logger.log_struct
        now = datetime.datetime.now()
        kwargs = {
            'severity': severity,
            'trace': self.trace,
            'resource': self.resource,
            'timestamp': now,
        }
        self.max_sent_severity = max(
            [severity, self.max_sent_severity],
            key=self.severity_value,
        )
        if is_parent:
            req = self.get_response_data(response)
            req.update(self.request_data)
            kwargs['http_request'] = req
            kwargs['severity'] = self.max_sent_severity
        log_func(*args, **kwargs)

    def severity_value(self, severity):
        """Convert severity string to integer
        Args:
            severity (str): Severity string
        Returns:
            integer: Serverity integer
        """
        if severity == 'DEBUG':
            return logging.DEBUG
        elif severity == 'INFO':
            return logging.INFO
        elif severity == 'WARNING':
            return logging.WARNING
        elif severity == 'ERROR':
            return logging.ERROR
        elif severity == 'CRITICAL':
            return logging.CRITICAL
        return logging.NOTSET

    def debug(self, content, **kwargs):
        """Log with 'DEBUG' severity
        Args:
            content: Log content
        """
        self._log('DEBUG', content, **kwargs)

    def info(self, content, **kwargs):
        """Log with 'INFO' severity
        Args:
            content: Log content
        """
        self._log('INFO', content, **kwargs)

    def warn(self, content, **kwargs):
        """Log with 'WARNING' severity
        Args:
            content: Log content
        """
        self._log('WARNING', content, **kwargs)

    def warning(self, content, **kwargs):
        """Log with 'WARNING' severity
        Args:
            content: Log content
        """
        self.warn(content, **kwargs)

    def error(self, content, **kwargs):
        """Log with 'ERROR' severity
        Args:
            content: Log content
        """
        self._log('ERROR', content, **kwargs)

    def exception(self, content, **kwargs):
        """Log with 'ERROR' severity
        Args:
            content: Log content
        """
        self.error(content, **kwargs)

    def critical(self, content, **kwargs):
        """Log with 'CRITICAL' severity
        Args:
            content: Log content
        """
        self._log('CRITICAL', content, **kwargs)

    def log(self, severity, content, **kwargs):
        """Log with specified severity
        Args:
            severity (str): Log severity
            content: Log content
        """
        self._log(severity, content, **kwargs)

    def log_response(
        self,
        response=None,
        severity=None,
        status=None,
        **kwargs
    ):
        """Log response information.
        Response log it treated as parent log of colleration.
        Args:
            response: Response information
            severity (str): Log severity
            status (int): Http status code
        """
        if not severity:
            if status:
                severity = self.log_level_for_status(status)
            else:
                severity = 'INFO'
        self._log(severity, None, is_parent=True, response=response)

    def log_level_for_status(self, status):
        """Convert http status to log severity
        Args:
            status (int): Http status code
        Returns:
            severity (str): Log severity
        """
        if status >= 500:
            return 'ERROR'
        elif status >= 400:
            return 'WARNING'
        return 'INFO'


class WerkzeugRequestLogger(RequestLogger):
    """RequestLogger using werkzeug.wrappers.Request
    Suit for most of wsgi applications
    """
    def __init__(
        self,
        request,
        client=None,
        project=None,
        module=None,
        version=None,
        log_name=None,
        child_log_name=None,
    ):
        """
        Args:
            request (werkzeug.wrappers.Request): Request object
            client (google.cloud.logging.Client): Log client for GAE
            project (str): Project id
            module (str): Module name
            version (str): Module version
            log_name (str): Parent log name in cloud console
            child_log_name (str): Child log name in cloud console
        """
        request_data = self.__class__.get_request_data(request)
        trace = self.__class__.get_trace(project, request)
        super(WerkzeugRequestLogger, self).__init__(
            trace,
            request_data=request_data,
            client=client,
            project=project,
            module=module,
            version=version,
            log_name=log_name,
            child_log_name=child_log_name,
        )

    @classmethod
    def get_request_data(cls, request):
        """Extract request information from request object
        Args:
            request (werkzeug.wrappers.Request): Request object
        Returns:
            dict: Request information
        """
        remote_ip = request.remote_addr
        if request.access_route:
            remote_ip = request.access_route[0]
        req = {
            'requestUrl': request.full_path,
            'requestMethod': request.method,
            'requestSize': request.content_length or 0,
            'userAgent': request.headers.get('User-Agent', ''),
            'remoteIp': remote_ip,
            'referer': request.referrer,
        }
        return req

    @classmethod
    def get_trace(cls, project, request):
        """Get trace
        Args:
            project (str): Project id
            request (werkzeug.wrappers.Request): Request object
        Returns:
            str: trace
        """
        trace_id = request.headers.get('X-Cloud-Trace-Context', None)
        if trace_id:
            if ';' in trace_id:
                trace_id = trace_id.split(';')[0]
            if '/' in trace_id:
                trace_id = trace_id.split('/')[0]
        trace = 'projects/{project}/traces/{trace_id}'.format(
            project=project,
            trace_id=trace_id,
        )
        return trace


class RequestLoggerHandler(logging.StreamHandler):
    """Handler for logging
    """
    def __init__(self, request_logger, *args, **kwargs):
        """
        Args:
            request_logger (RequestLogger): RequestLogger object
        """
        super(RequestLoggerHandler, self).__init__(*args, **kwargs)
        self.request_logger = request_logger
        self.thread_id = threading.get_ident()

    def emit(self, record):
        """Emit each log record
        Args:
            record: log record
        """
        if self.thread_id != threading.get_ident():
            return
        message = super(RequestLoggerHandler, self).format(record)
        levelname = record.levelname
        self.request_logger.log(levelname, message)


class RequestLoggerMiddleware(object):
    """Middleware for wsgi application
    """
    def __init__(
        self,
        app,
        loggers=None,
        loglevel='INFO',
        project=None,
        module=None,
        version=None,
    ):
        """
        Args:
            app: wsgi app
            loggers: Loggers to attach handlers
            loglevel: Loglevel to set to root logger in case loggers are not
            specified
            project (str): Project id
            module (str): Module name
            version (str): Module version
        """
        self.app = app
        if loggers is not None:
            self.loggers = loggers
        else:
            loggers = self.get_app_loggers(app)
            logger = logging.getLogger()
            logger.setLevel(loglevel)
            loggers.append(logger)
            self.loggers = loggers
        self.loglevel = loglevel
        self.project = project
        self.module = module
        self.version = version
        self.client = gcloud_logging.Client(self.project)

    def get_app_loggers(self, app):
        """Seek loggers within all parent app layers
        Only used when loggers are not specified in constructor
        Args:
            app: wsgi app
        """
        loggers = []
        while app:
            if hasattr(app, 'logger'):
                loggers.append(app.logger)
            app = app.app if hasattr(app, 'app') else None
        return loggers

    def __call__(self, environ, start_response):
        request_logger = self.get_request_logger(environ)
        handler = self.get_request_handler(request_logger)
        for logger in self.loggers:
            logger.addHandler(handler)

        res_info = {}
        start_response_wrapper = self.get_start_response_wrapper(
            start_response,
            res_info,
        )
        res = self.app(environ, start_response_wrapper)
        request_logger.log_response(
            res_info,
            status=res_info.get('status', 200),
        )
        request_logger.commit()
        for logger in self.loggers:
            logger.removeHandler(handler)
        return res

    def get_request_logger(self, environ):
        """Get logger for a request
        Override this to use custom class
        Args:
            environ: Environment variables
        Returns:
            RequestLogger: logger used for this request
        """
        request = Request(environ, populate_request=False)
        return WerkzeugRequestLogger(
            request,
            client=self.client,
            project=self.project,
            module=self.module,
            version=self.version,
        )

    def get_request_handler(self, request_logger):
        """Get log handler for a request
        Override this to use custom class
        Args:
            request_logger (RequestLogger): Request logger for this request
        Returns:
            RequestLoggerHandler: handler used for this request
        """
        return RequestLoggerHandler(request_logger)

    def get_start_response_wrapper(self, start_response, res_info):
        """Get wrapper function to handle a request
        Override this to use custom function
        Args:
            start_response: Original function to handle this request
            res_info (dict): Container to set response information for log
        Returns:
            function: Wrapper function
        """
        def wrapper(status, response_headers, *args):
            log_status = status
            if isinstance(status, str):
                m = re.match(r'^(\d+).*$', status)
                if m:
                    log_status = int(m.group(1))
            res_info['status'] = log_status
            headers = dict(response_headers)
            content_length = headers.get('Content-Length', 0)
            res_info['responseSize'] = content_length
            start_response(status, response_headers, *args)
        return wrapper
