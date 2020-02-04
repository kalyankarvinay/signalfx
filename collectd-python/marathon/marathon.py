from calendar import timegm
import dateutil.parser
import json
import logging
import six
from six.moves import urllib
import ssl
import sys
import time


# Helper functions
def time_diff(start_time, end_time=None):
    """Calculates the difference in seconds between two timestamps"""
    diff = 0.0
    if end_time is None:
        end_time = time.time()
    else:
        end_time = timegm(dateutil.parser.parse(end_time).utctimetuple())
    diff = end_time - timegm(dateutil.parser.parse(start_time).utctimetuple())
    return diff


def str_to_bool(value):
    """Python 2.x does not have a casting mechanism for booleans.  The built in
    bool() will return true for any string with a length greater than 0.  It
    does not cast a string with the text "true" or "false" to the
    corresponding bool value.  This method is a casting function.  It is
    insensetive to case and leading/trailing spaces.  An Exception is raised
    if a cast can not be made.
    """
    value = str(value).strip().lower()
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        raise ValueError('Unable to cast value (%s) to boolean' % value)


def num_healthy_tasks(results):
    """Counts the number of healthy tasks in the marathon environment"""
    count = 0
    if hasattr(results, '__iter__'):
        for i in results:
            if 'alive' in i.keys():
                if i['alive'] is True:
                    count += 1
    else:
        log.error('num_healthy_tasks(): "results" not iterable {0}'
                  .format(results))
    return count


def num_unhealthy_tasks(results):
    """Counts the number of unhealthy tasks in the marathon environment"""
    count = 0
    if hasattr(results, '__iter__'):
        for i in results:
            if 'alive' in i.keys():
                if i['alive'] is False:
                    count += 1
    else:
        log.error('num_unhealthy_tasks(): "results" not iterable {0}'
                  .format(results))
    return count


def application_instance_multiplier(value, app, dig_it_up, api_version=None):
    """Digs up the number of instances of the supplied app,
    and returns the value multiplied by the number of instances
    """
    response = None
    instances = dig_it_up(app, 'instances')
    if instances is not None:
        response = value * instances
    return response


dims = {
    'marathon': [
        {
            'name': 'mesos_framework_id',
            'path': 'frameworkId',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'info',
            'api_version': 'v2'
        },
        {
            'name': 'mesos_framework_name',
            'path': 'marathon_config/framework_name',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'info',
            'api_version': 'v2'
        },
        {
            'name': 'marathon_framework_id',
            'path': 'frameworkId',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'info',
            'api_version': 'v2'
        },
        {
            'name': 'marathon_framework_name',
            'path': 'marathon_config/framework_name',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'info',
            'api_version': 'v2'
        }
    ],
    'metric': [],
    'app': [
        {
            'name': 'mesos_task_name',
            'path': 'id',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'apps',
            'api_version': 'v2'
        },
        {
            'name': 'marathon_app_id',
            'path': 'id',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'apps',
            'api_version': 'v2'
        },
        {
            'name': 'container_type',
            'path': 'container/type',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'apps',
            'api_version': 'v2'
        },
        {
            'name': 'container_image',
            'path': 'container/docker/image',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'apps',
            'api_version': 'v2'
        },
        {
            'name': 'container_network',
            'path': 'container/docker/host',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'apps',
            'api_version': 'v2'
        }
    ],
    'queue':  [
        {
            'name': 'mesos_task_name',
            'path': 'id',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'apps',
            'api_version': 'v2'
        },
        {
            'name': 'marathon_app_id',
            'path': 'id',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'apps',
            'api_version': 'v2'
        },
        {
            'name': 'container_type',
            'path': 'container/type',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'apps',
            'api_version': 'v2'
        },
        {
            'name': 'container_image',
            'path': 'container/docker/image',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'apps',
            'api_version': 'v2'
        },
        {
            'name': 'container_network',
            'path': 'container/docker/host',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'apps',
            'api_version': 'v2'
        }
    ],
    'task': [
        {
            'name': 'mesos_task_id',
            'path': 'id',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'tasks',
            'api_version': 'v2'
        },
        {
            'name': 'mesos_agent',
            'path': 'slaveId',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'tasks',
            'api_version': 'v2'
        },
        {
            'name': 'mesos_task_name',
            'path': 'appId',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'tasks',
            'api_version': 'v2'
        },
        {
            'name': 'marathon_app_id',
            'path': 'appId',
            'start': '1.0.0',
            'stop': None,
            'api_end_point': 'tasks',
            'api_version': 'v2'
        }
    ]
}

metrics = {
    'metric': [
        {
            'name': '',
            'start': '1.0.0',
            'stop': None,
            'type': '',
            'api_end_point': 'metrics',
            'api_version': '',
            'path': ''
        }
    ],
    'app': [
        {
            'name': 'marathon.app.cpu.allocated',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'cpus',
            'transformation': application_instance_multiplier
        },
        {
            'name': 'marathon.app.memory.allocated',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'mem',
            'transformation': application_instance_multiplier
        },
        {
            'name': 'marathon.app.disk.allocated',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'disk',
            'transformation': application_instance_multiplier
        },
        {
            'name': 'marathon.app.gpus.allocated',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'gpus',
            'transformation': application_instance_multiplier
        },
        {
            'name': 'marathon.app.cpu.allocated.per.instance',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'cpus'
        },
        {
            'name':
                'marathon.app.memory.allocated.per.instance',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'mem'
        },
        {
            'name': 'marathon.app.disk.allocated.per.instance',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'disk'
        },
        {
            'name': 'marathon.app.gpus.allocated.per.instance',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'gpus'
        },
        {
            'name': 'marathon.app.tasks.staged',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'tasksStaged'
        },
        {
            'name': 'marathon.app.tasks.running',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'tasksRunning'
        },
        {
            'name': 'marathon.app.tasks.unhealthy',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'tasksUnhealthy'
        },
        {
            'name': 'marathon.app.instances.total',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'instances'
        },
        {
            'name': 'marathon.app.deployments.total',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'path': 'deployments',
            'transformation': lambda x: len(x)
        }
    ],
    'queue': [
        {
            'name': 'marathon.app.delayed',
            'path': 'delay/overdue',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'apps',
            'api_version': 'v2',
            'transformation': lambda x: 0 if x is None else 1
        }
    ],
    'task': [
        {
            'name': 'marathon.task.start.time.elapsed',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'tasks',
            'api_version': 'v2',
            'path': 'startedAt',
            'transformation': time_diff
        },
        {
            'name': 'marathon.task.staged.time.elapsed',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'tasks',
            'api_version': 'v2',
            'path': 'stagedAt',
            'transformation': time_diff
        },
        {
            'name': 'marathon.task.healthchecks.passing.total',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'tasks',
            'api_version': 'v2',
            'path': 'healthCheckResults',
            'transformation': num_healthy_tasks
        },
        {
            'name': 'marathon.task.healthchecks.failing.total',
            'start': '1.0.0',
            'stop': None,
            'type': 'gauge',
            'api_end_point': 'tasks',
            'api_version': 'v2',
            'path': 'healthCheckResults',
            'transformation': num_unhealthy_tasks
        }
    ]
}


class VersionManager():
    def __init__(self, dictionary):
        """Returns a set of dims and metrics for a given type based on marathon
        version"""
        self.dictionary = dictionary

    def version_greater_than_or_equal(self, version, comparator):
        """Returns True or False if version is greater than or equal to the
        comparator
        """
        (v_major, v_minor, v_revision) = version.split('.')
        (c_major, c_minor, c_revision) = comparator.split('.')
        response = False
        if (v_major > c_major) \
            or (v_major == c_major and v_minor > c_minor) \
            or (v_major == c_major and v_minor == c_minor and
                v_revision >= c_revision):
            response = True
        return response

    def get(self, version_type, version, stats=None):
        log.debug("VersionManager.get(): invoked")

    # response = {
    #     'tasks': {
    #         'v2': [
    #                   {
    #                     'name': 'marathon.task.healthchecks.failing.total',
    #                     'start': '1.0.0',
    #                     'stop': None,
    #                     'type': 'gauge',
    #                     'api_end_point': 'tasks',
    #                     'api_verison': 'v2',
    #                     'path': 'healthCheckResults',
    #                     'transformation': num_unhealthy_tasks
    #                   }
    #               ]
    #     }
    # }

        response = {}
        if version_type in self.dictionary:
            for stat in self.dictionary[version_type]:
                # If within start
                if 'start' in stat and \
                  self.version_greater_than_or_equal(version, stat['start']):
                    # If within stop
                    if 'stop' in stat and \
                        ((stat['stop'] is not None and
                          not self.version_greater_than_or_equal(version,
                          stat['stop'])) or stat['stop'] is None):
                        # if end_point defined
                        if 'api_end_point' in stat and 'api_version' in stat:
                            # Create api_end_point in response if not there
                            if stat['api_end_point'] not in response:
                                response[stat['api_end_point']] = {}
                            # Create api_version in response[api_end_point]
                            if stat['api_version'] not in response[
                                    stat['api_end_point']]:
                                response[stat['api_end_point']][
                                    stat['api_version']] = []
                            # Assign metric to proper place
                            response[stat['api_end_point']][
                                stat['api_version']].append(stat)
                        else:
                            # api_end_point or api_version are not defined
                            log.info(('VersionManager.get() : api_end_point or'
                                      ' api_version are not defined for : {0}')
                                     .format(stat))
                    else:
                        # metric greater than or equal to stop
                        log.debug(('VersionManager.get() : stat greater than '
                                   'or equal to stop defined for : {0}')
                                  .format(stat))
                else:
                    log.debug(('VersionManager.get() : stat greater than '
                               'or equal to stop defined for : {0}')
                              .format(stat))

        log.debug("VersionManager.get(): complete")
        return response


class Collector:
    """Collector class responsible for collecting information from a host"""
    def __init__(self, scheme, host=None, port=None, username=None, password=None,
                 dcos_auth_url=None, plugin_instance="unknown"):
        log.debug('Collector.__init__() [{0}:{1}]: invoked'
                  .format(host, port))
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.plugin_instance = plugin_instance
        self.version = "0.0.0"
        self.stats = {}
        self.scheme = scheme
        self.dcos_auth_url = dcos_auth_url
        pwd_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        pwd_mgr.add_password(None,
                             "{scheme}://{host}:{port}"
                             .format(scheme=self.scheme, host=self.host, port=self.port),
                             self.username,
                             self.password)
        handler = urllib.request.HTTPBasicAuthHandler(pwd_mgr)
        https_handler = urllib.request.BaseHandler()
        if scheme == 'https':
            https_handler = urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
        self.opener = urllib.request.build_opener(handler, https_handler)
        if dcos_auth_url:
            self.get_dcos_auth_token(dcos_auth_url, username, password)
        log.debug('Collector.__init__() [{0}:{1}]: complete'
                  .format(self.host, self.port))


    def get_dcos_auth_token(self, dcos_auth_url, username, password):
        if not username or not password:
            log.error('Collector.get_dcos_auth_token() [{0}:{1}]: Username/password for dcos is not \
                      configured correctly. Cannot refresh dcos auth token.'
                      .format(self.host, self.port))
        print(dcos_auth_url)
        try:
            headers = {"Content-Type":"application/json"}
            data = json.dumps({"uid":username,"password":password})
            req = urllib.request.Request(dcos_auth_url, headers=headers, data=data)
            response = urllib.request.urlopen(req, context=ssl._create_unverified_context())
            result = json.load(response)
            self.opener.addheaders = [('Authorization', ('token=%s' % (str(result['token']))))]
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            log.error(('Collector.get_dcos_auth_token() [{0}:{1}]: Error '
                       'connecting to {2} ({3})').format(self.host,
                                                   self.port,
                                                   dcos_auth_url, e))
        except Exception as e:
            log.error(('Collector.get_dcos_auth_token() [{0}:{1}]: Error {2}').format(self.host,
                                        self.port,
                                        e))


    def __repr__(self):
        return str(self.__dict__)

    def _d(self, d):
        """Formats a dictionary of key/value pairs as a comma-delimited list of
        key=value tokens."""
        return ','.join(['='.join(p) for p in d.items()])

    def request(self, version="", api=""):
        """Makes a request to the specified version and api"""
        log.debug('MarathonCollector.request() [{0}:{1}]: invoked'
                  .format(self.host, self.port))

        result = {}

        try:
            if version != '':
                request_url = '{scheme}://{host}:{port}/{version}/{api}'.format(
                               scheme=self.scheme,
                               host=self.host,
                               port=str(self.port),
                               version=version,
                               api=api)
            else:
                request_url = '{scheme}://{host}:{port}/{api}'.format(
                               scheme=self.scheme,
                               host=self.host,
                               port=str(self.port),
                               api=api)
            log.debug('MarathonCollector.request() [{0}:{1}]: Request URL {2}'
                      .format(self.host, self.port, request_url))
            response = self.opener.open(request_url, timeout=5)
            result = json.loads(response.read().decode('utf-8'))
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            if isinstance(e, urllib.error.HTTPError) and e.code == 401 and self.dcos_auth_url:
                log.info(('MarathonCollector.request() [{0}:{1}]: Refreshing '
                          'dcos auth token from: {2}').format(self.host,
                           self.port,
                           request_url))
                self.dcos_auth_token = self.get_dcos_auth_token(self.dcos_auth_url,
                                                                self.username,
                                                                self.password)
            else:
                log.error(('MarathonCollector.request() [{0}:{1}]: Error '
                           'connecting to {2}: {3}').format(self.host,
                                                       self.port,
                                                       request_url, e))
        except Exception as e:
            log.error('MarathonCollector.request() [{0}:{1}]: Error {2}'
                      .format(self.host, self.port, e))

        log.debug('MarathonCollector.request() [{0}:{1}]: Response : {2}'
                  .format(self.host,
                          self.port,
                          result))

        log.debug('MarathonCollector.request() [{0}:{1}]: complete'
                  .format(self.host, self.port))
        return result

    def dig_it_up(self, obj, path):
        """Find the specified value in the supplied object using the specified
        path"""
        log.debug('MarathonCollector.dig_it_up() [{0}:{1}]: invoked'
                  .format(self.host, self.port))

        result = None
        try:
            if isinstance(path, six.string_types):
                path = path.split('/')
            result = six.moves.reduce(lambda x, y: x[y], path, obj)
        except Exception:
            log.debug(('MarathonCollector.dig_it_up() [{0}:{1}]: failed to dig'
                       ' up {2} in {3}').format(self.host,
                                                self.port,
                                                path,
                                                obj))

        log.debug('MarathonCollector.dig_it_up() [{0}:{1}]: complete'
                  .format(self.host, self.port))
        return result

    def emit(self, name, dimensions, value, metric_type=None, t=None):
        """emit a metric through collectd"""
        log.debug('MarathonCollector.emit() [{0}:{1}]: invoked'
                  .format(self.host, self.port))
        if t is None:
            t = time.time()
        log.info(('Value parameters to be emitted:'
                  '\n name : {n}'
                  '\n dimensions : {d}'
                  '\n value: {v}'
                  '\n type_instance: {ti}'
                  '\n time: {t}').format(n=name,
                                         d=dimensions,
                                         v=str(value),
                                         ti=name,
                                         t=t))
        if value is not None:
            val = collectd.Values()
            val.plugin = 'marathon'
            val.plugin_instance = self.plugin_instance
            val.plugin_instance += '[{dims}]'.format(dims=self._d(dimensions))
            val.type = metric_type
            val.type_instance = name
            val.time = t
            val.meta = {'true': 'true'}
            val.values = [value]

            log.info('Value to be emitted {0}'.format(str(val)))

            val.dispatch()
        else:
            log.error(('MarathonCollector.emit() [{0}:{1}]: Metric {2} was '
                       'None and will not be emitted').format(self.host,
                                                              self.port,
                                                              name))

        log.debug('MarathonCollector.emit() [{0}:{1}]: complete'
                  .format(self.host, self.port))


class MarathonTaskCollector(Collector):
    def __init__(self, scheme, host=None, port=None, version=None,
                 username=None, password=None, dcos_auth_url=None,
                 plugin_instance="unknown"):
        log.debug('MarathonTaskCollector.__init__() [{0}:{1}]: invoked'
                  .format(host, port))

        Collector.__init__(self,
                           scheme,
                           host,
                           port,
                           username=username,
                           password=password,
                           dcos_auth_url=dcos_auth_url,
                           plugin_instance=plugin_instance)

        log.debug('MarathonTaskCollector.__init__() [{0}:{1}]: complete'
                  .format(self.host, self.port))

    def update_version(self, version):
        """Fetches the current marathon instance version"""
        log.debug('MarathonTaskCollector.update_version() [{0}:{1}]: invoked'
                  .format(self.host, self.port))

        if version != self.version:
            log.info(('MarathonTaskCollector.update_version() [{0}{1}]: '
                      'version updated from {2} to {3}').format(self.host,
                                                                self.port,
                                                                self.version,
                                                                version))
            self.version = version
            self.stats = metric_manager.get('task', version)
            self.dims = dimension_manager.get('task', version)

        log.debug('MarathonTaskCollector.update_version() [{0}:{1}]: complete'
                  .format(self.host, self.port))

    def read(self, marathon_dimensions):
        log.debug('MarathonTaskCollector.read() [{0}:{1}]: invoked'
                  .format(self.host, self.port))

        for endpoint, api_versions in self.stats.items():
            for api_version, metrics in api_versions.items():
                dimension_paths = {}
                result = self.request(api_version, endpoint)
                if 'tasks' in result:
                    result = result['tasks']
                if endpoint in self.dims and \
                   api_version in self.dims[endpoint]:
                    for dimension in self.dims[endpoint][api_version]:
                        dimension_paths[dimension['name']] = dimension['path']

                for task in result:
                    start_ts = None
                    dimensions = {}
                    for dim, path in dimension_paths.items():
                        dimension_value = self.dig_it_up(task, path)
                        if dimension_value is not None:
                            dimensions[dim] = dimension_value
                    # Add marathon_dimensions
                    dimensions.update(marathon_dimensions)
                    # Add marathon_dimensions
                    dimensions.update(marathon_dimensions)
                    if 'mesos_task_name' in dimensions:
                        # Patch mesos_task_name
                        dimensions['mesos_task_name'] = dimensions[
                                                        'mesos_task_name'][1:]
                    if 'marathon_app_id' in dimensions:
                        # Patch marathon_app_id
                        dimensions['marathon_app_id'] = dimensions[
                                                        'marathon_app_id'][1:]
                    for metric in metrics:
                        name = metric['name']
                        metric_type = metric['type']
                        value = self.dig_it_up(task, metric['path'])
                        if value is not None:
                            if 'transformation' in metric and name == \
                               'marathon.task.staged.time.elapsed':
                                value = metric['transformation'](value,
                                                                 start_ts)
                            elif 'transformation'in metric.keys() and name == \
                                 'marathon.task.start.time.elapsed':
                                start_ts = value
                                value = metric['transformation'](value)
                            elif 'transformation' in metric.keys():
                                value = metric['transformation'](value)
                            self.emit(name, dimensions, value, metric_type)

        log.debug('MarathonTaskCollector.read() [{0}:{1}]: complete'
                  .format(self.host, self.port))


class MarathonAppCollector(Collector):
    def __init__(self, scheme, host=None, port=None, version=None,
                 username=None, password=None,
                 dcos_auth_url=None, plugin_instance="unknown"):
        log.debug('MarathonAppCollector.__init__() [{0}:{1}]: invoked'
                  .format(host, port))

        Collector.__init__(self,
                           scheme,
                           host,
                           port,
                           username=username,
                           password=password,
                           dcos_auth_url=dcos_auth_url,
                           plugin_instance=plugin_instance)

        log.info('MarathonAppCollector.__init__() [{0}:{1}]: complete'
                  .format(self.host, self.port))

    def update_version(self, version):
        """Fetches the current marathon instance version"""
        log.debug('MarathonAppCollector.update_version() [{0}:{1}]: invoked'
                  .format(self.host, self.port))

        if version != self.version:
            log.info(('MarathonAppCollector.update_version() [{0}{1}]: '
                      'version updated from {2} to {3}').format(self.host,
                                                                self.port,
                                                                self.version,
                                                                version))
            self.version = version
            self.stats = metric_manager.get('app', version)
            self.dims = dimension_manager.get('app', version)

        log.debug('MarathonAppCollector.update_version() [{0}:{1}]: completed'
                  .format(self.host, self.port))

    def read(self, marathon_dimensions):
        """read callback"""
        log.debug('MarathonAppCollector.read() [{0}:{1}]: invoked'
                  .format(self.host, self.port))
        for endpoint, api_versions in self.stats.items():
            for api_version, metrics in api_versions.items():
                dimension_paths = {}
                result = self.request(api_version, endpoint)
                if 'apps' in result:
                    result = result['apps']
                if endpoint in self.dims \
                   and api_version in self.dims[endpoint]:
                    for dimension in self.dims[endpoint][api_version]:
                        dimension_paths[dimension['name']] = dimension['path']

                for app in result:
                    dimensions = {}
                    for dim, path in dimension_paths.items():
                        dimension_value = self.dig_it_up(app, path)
                        if dimension_value is not None:
                            dimensions[dim] = dimension_value
                    # Add marathon_dimensions
                    dimensions.update(marathon_dimensions)
                    if 'mesos_task_name' in dimensions:
                        # Patch mesos_task_name
                        dimensions['mesos_task_name'] = dimensions[
                                                        'mesos_task_name'][1:]
                    if 'marathon_app_id' in dimensions:
                        # Patch marathon_app_id
                        dimensions['marathon_app_id'] = dimensions[
                                                        'marathon_app_id'][1:]
                    for metric in metrics:
                        name = metric['name']
                        metric_type = metric['type']
                        value = self.dig_it_up(app, metric['path'])
                        if value is not None:
                            if 'transformation' in metric.keys() and \
                              name.endswith('.allocated'):
                                value = metric['transformation'
                                               ](value,
                                                 app,
                                                 self.dig_it_up,
                                                 api_version)
                            elif 'transformation' in metric.keys():
                                value = metric['transformation'](value)
                            self.emit(name, dimensions, value, metric_type)
        log.debug('MarathonAppCollector.read() [{0}:{1}]: complete'
                  .format(self.host, self.port))


class MarathonQueueCollector(Collector):
    def __init__(self, scheme, host=None, port=None, version=None,
                 username=None, password=None,
                 dcos_auth_url=None, plugin_instance="unknown"):
        log.debug('MarathonQueueCollector.__init__() [{0}:{1}]: invoked'
                  .format(host, port))

        Collector.__init__(self,
                           scheme,
                           host,
                           port,
                           username=username,
                           password=password,
                           dcos_auth_url=dcos_auth_url,
                           plugin_instance=plugin_instance)

        log.debug('MarathonQueueCollector.__init__() [{0}:{1}]: complete'
                  .format(self.host, self.port))

    def update_version(self, version):
        """Fetches the current marathon instance version"""
        log.debug('MarathonQueueCollector.update_version() [{0}:{1}]: invoked'
                  .format(self.host, self.port))
        if version != self.version:
            log.info(('MarathonQueueCollector.update_version() [{0}{1}]: '
                      'version updated from {2} to {3}').format(self.host,
                                                                self.port,
                                                                self.version,
                                                                version))
            self.version = version
            self.stats = metric_manager.get('queue', version)
            self.dims = dimension_manager.get('queue', version)
        log.debug('MarathonQueueCollector.update_version() [{0}:{1}]: complete'
                  .format(self.host, self.port))

    def read(self, marathon_dimensions):
        log.debug('MarathonQueueCollector.read() [{0}:{1}]: invoked'
                  .format(self.host, self.port))

        for endpoint, api_versions in self.stats.items():
            for api_version, metrics in api_versions.items():
                dimension_paths = {}
                result = self.request(api_version, endpoint)
                if 'queue' in result:
                    result = result['queue']
                if endpoint in self.dims and \
                   api_version in self.dims[endpoint]:
                    for dimension in self.dims[endpoint][api_version]:
                        dimension_paths[dimension['name']] = dimension['path']

                for app in result:
                    dimensions = {}
                    for dim, path in dimension_paths.items():
                        dimension_value = self.dig_it_up(app, path)
                        if dimension_value is not None:
                            dimensions[dim] = dimension_value
                    # Add marathon_dimensions
                    dimensions.update(marathon_dimensions)
                    if 'mesos_task_name' in dimensions:
                        # Patch mesos_task_name
                        dimensions['mesos_task_name'] = dimensions[
                                                        'mesos_task_name'][1:]
                    if 'marathon_app_id' in dimensions:
                        # Patch marathon_app_id
                        dimensions['marathon_app_id'] = dimensions[
                                                        'marathon_app_id'][1:]
                    for metric in metrics:
                        name = metric['name']
                        metric_type = metric['type']
                        value = self.dig_it_up(app, metric['path'])
                        try:
                            if 'transformation' in metric.keys():
                                value = metric['transformation'](value)
                        except Exception as e:
                            log.error(('MarathonQueueCollector.read() '
                                       '[{0}:{1}]: failed to transform '
                                       'value: {3} for metric: {4} due to: {5}'
                                       ).format(self.host, self.port, value,
                                                name, e))
                        self.emit(name, dimensions, value, metric_type)
        log.debug('MarathonQueueCollector.read() [{0}:{1}]: complete'
                  .format(self.host, self.port))


class MarathonMetricsCollector(Collector):
    def __init__(self, scheme, host=None, port=None, version=None, username=None,
                 password=None, dcos_auth_url=None):
        log.debug('MarathonMetricsCollector.__init__() [{0}:{1}]: invoked'
                  .format(host, port))

        Collector.__init__(self, scheme, host, port, username=username,
                           password=password, dcos_auth_url=dcos_auth_url)

        log.debug('MarathonMetricsCollector.__init__() [{0}:{1}]: complete'
                  .format(self.host, self.port))

    def update_version(self, version):
        """Fetches the current marathon instance version"""
        log.debug(('MarathonMetricsCollector.update_version() [{0}:{1}]: '
                   'invoked').format(self.host, self.port))

        if version != self.version:
            log.info(('MarathonMetricsCollector.update_version() [{0}{1}]: '
                      'version updated from {2} to {3}').format(self.host,
                                                                self.port,
                                                                self.version,
                                                                version))
            self.version = version
            self.stats = metric_manager.get('metric', version)

        log.debug(('MarathonMetricsCollector.update_version() [{0}:{1}]: '
                   'complete').format(self.host, self.port))

    def read(self, marathon_dimensions):
        log.debug('MarathonMetricsCollector.read() [{0}:{1}]: invoked'
                  .format(self.host, self.port))
        result = None

        for endpoint, api_versions in self.stats.items():
            for api_version, metrics in api_versions.items():
                result = self.request(api_version, endpoint)

        if hasattr(result, 'keys'):
            if 'gauges' in result:
                self.gauges(result['gauges'], marathon_dimensions)
            if 'counters' in result:
                self.counters(result['counters'], marathon_dimensions)
            if 'meters' in result:
                self.meters(result['meters'], marathon_dimensions)
        else:
            log.debug(('MarathonMetricsCollector.read() [{0}:{1}]: '
                       'Unable to read results').format(self.host,
                                                        self.port))

        log.debug('MarathonMetricsCollector.read() [{0}:{1}]: complete'
                  .format(self.host, self.port))

    def gauges(self, gauges, dimensions):
        log.debug('MarathonMetricsCollector.gauges() [{0}:{1}]: invoked'
                  .format(self.host, self.port))

        for gauge, info in six.iteritems(gauges):
            try:
                name = gauge
                metric_type = 'gauge'
                value = info['value']
                self.emit(name, dimensions, value, metric_type)
            except:
                log.info('MarathonMetricsCollector.gauges() [{0}:{1}]: '
                         'No gauges found'.format(self.host, self.port))

        log.debug('MarathonMetricsCollector.gauges() [{0}:{1}]: complete'
                  .format(self.host, self.port))

    def counters(self, counters, dimensions):
        log.debug('MarathonMetricsCollector.counters() [{0}:{1}]: invoked'
                  .format(self.host, self.port))

        for counter, info in six.iteritems(counters):
            try:
                name = counter
                metric_type = 'gauge'
                value = info['count']
                self.emit(name, dimensions, value, metric_type)
            except:
                log.info('MarathonMetricsCollector.counters() [{0}:{1}]: '
                         'No counters found'.format(self.host, self.port))

        log.debug('MarathonMetricsCollector.counters() [{0}:{1}]: complete'
                  .format(self.host, self.port))

    def meters(self, meters, dimensions):
        log.debug('MarathonMetricsCollector.meters() [{0}:{1}]: invoked'
                  .format(self.host, self.port))

        for meter, info in six.iteritems(meters):
            try:
                name = meter + '.' + info['units'].replace('/', '.per.')
                metric_type = 'gauge'
                value = info['mean_rate']
                self.emit(name, dimensions, value, metric_type)
            except:
                log.info('MarathonMetricsCollector.meters() [{0}:{1}]: '
                         'No meters found'.format(self.host, self.port))

        log.debug('MarathonMetricsCollector.meters() [{0}:{1}]: complete'
                  .format(self.host, self.port))

    def get(self):
        log.debug('MarathonMetricsCollector.get() [{0}:{1}]: invoked'
                  .format(self.host, self.port))

        result = []
        try:
            result = self.request(self.version, self.api)
        except:
            log.info('MarathonMetricsCollector.get() [{0}:{1}]: '
                     'Failed to get metrics'.format(self.host, self.port))

        log.debug('MarathonMetricsCollector.get() [{0}:{1}]: complete'
                  .format(self.host, self.port))
        return result


class MarathonCollector(Collector):
    """The main marathon collector which collects information about a marathon
    host.  Includes collectors for metrics, tasks, and apps.
    """
    def __init__(self, scheme, host=None, port=None, username=None,
                 password=None, dcos_auth_url=None):
        # Initialize parent class
        Collector.__init__(self, scheme, host, port, username=username,
                           password=password, dcos_auth_url=dcos_auth_url)
        # The metrics api endpoint is not versioned
        self.metrics = MarathonMetricsCollector(scheme, host, port,
                                                username=username, password=password,
                                                dcos_auth_url=self.dcos_auth_url)
        self.tasks = MarathonTaskCollector(scheme, host, port,
                                           username=username, password=password,
                                           dcos_auth_url=self.dcos_auth_url)
        self.apps = MarathonAppCollector(scheme, host, port,
                                         username=username, password=password,
                                         dcos_auth_url=self.dcos_auth_url)
        self.queue = MarathonQueueCollector(scheme, host, port,
                                            username=username, password=password,
                                            dcos_auth_url=self.dcos_auth_url)
        self.dims = {}

    def update_plugin_instance(self, plugin_instance):
        self.plugin_instance = plugin_instance
        self.metrics.plugin_instance = plugin_instance
        self.tasks.plugin_instance = plugin_instance
        self.apps.plugin_instance = plugin_instance
        self.queue.plugin_instance = plugin_instance
        self.dims = {}


    def update_version(self):
        """Fetches the current marathon instance version"""
        api_version = "v2"
        api = "info"
        path = 'version'
        info = self.request(version=api_version, api=api)
        version = ""

        try:
            version = self.dig_it_up(info, path)

        except Exception as e:
            log.info(('MarathonCollector.update_version() [{0}{1}]: '
                      'error fetching Marathon version {2}').format(self.host,
                                                                    self.port,
                                                                    e))

        if version is not None and version != self.version:
            log.info(('MarathonCollector.update_version() [{0}{1}]: '
                      'version updated from {2} to {3}').format(self.host,
                                                                self.port,
                                                                self.version,
                                                                version))
            self.version = version
            self.dims = dimension_manager.get('marathon', version)
            self.metrics.update_version(version)
            self.tasks.update_version(version)
            self.apps.update_version(version)
            self.queue.update_version(version)

    def read(self):
        log.debug('MarathonCollector.read() [{0}:{1}]: invoked'
                  .format(self.host, self.port))

        dimensions = {}

        self.update_version()

        for endpoint, api_versions in self.dims.items():
            for api_version, metrics in api_versions.items():
                dimension_paths = {}
                result = self.request(api_version, endpoint)
                if endpoint in self.dims and \
                   api_version in self.dims[endpoint]:
                    for dimension in self.dims[endpoint][api_version]:
                        dimension_paths[dimension['name']] = dimension['path']

                dimensions = {}
                for dim, path in dimension_paths.items():
                    dimension_value = self.dig_it_up(result, path)
                    if dimension_value is not None:
                        dimensions[dim] = dimension_value

        # Update the plugin instances once we know them
        try:
            plugin_instance = '{0}.{1}'.format(
                                    dimensions['mesos_framework_name'],
                                    dimensions['mesos_framework_id'])
            self.update_plugin_instance(plugin_instance)
            dimensions['marathon_instance'] = plugin_instance

        except Exception as e:
            log.error(('MarathonCollector.read() [{0}:{1}]: unable to set '
                       'plugin_instance : {2}').format(self.host,
                                                       self.port,
                                                       e))
        self.metrics.read(dimensions)
        self.apps.read(dimensions)
        self.queue.read(dimensions)
        self.tasks.read(dimensions)

        log.debug('MarathonCollector.read() [{0}:{1}]: complete'
                  .format(self.host, self.port))


class MarathonPlugin:
    """The main plugin class used to configure and orchestrate collectors
    """
    def __init__(self):
        self.hosts = []


    def __repr__(self):
        return str(self.__dict__)

    def configure_callback(self, conf):
        log.debug('MarathonPlugin.configure_callback() : invoked')
        for node in conf.children:
            key = str(node.key).lower()
            try:
                if key == 'host':
                    if len(node.values) > 1:
                        if len(node.values) == 3:
                            host = MarathonCollector(node.values[0],
                                                     node.values[1],
                                                     node.values[2])
                            self.hosts.append(host)
                        elif 5 <= len(node.values) <= 6:
                            # if the username or password are empty strings
                            # or only spaces then don't use them
                            if node.values[3] is None or \
                               node.values[4] is None or \
                               node.values[3].strip(" ") == "" or \
                               node.values[4].strip(" ") == "":
                                log.info('MarathonPlugin.configure_callback() '
                                         ': either the username or password is'
                                         ' a blank string so leaving them out')
                                host = MarathonCollector(node.values[0],
                                                          node.values[1],
                                                          node.values[2])
                            else:
                                if (len(node.values) == 5) or (len(node.values) == 6 and \
                                                                (node.values[5].strip(" ") == "")):
                                    host = MarathonCollector(node.values[0],
                                                             node.values[1],
                                                             node.values[2],
                                                             node.values[3],
                                                             node.values[4])
                                else:
                                    if node.values[0] != 'https':
                                        raise Exception("Invalid Host Configuration {0}"
                                                            .format(node.values))
                                    log.info(('DC/OS auth URL: %s' % (node.values[5])))
                                    host = MarathonCollector(node.values[0],
                                                             node.values[1],
                                                             node.values[2],
                                                             node.values[3],
                                                             node.values[4],
                                                             node.values[5])
                            self.hosts.append(host)
                        else:
                            raise Exception("Invalid Host Configuration {0}"
                                            .format(node.values))

                elif key == 'verbose':
                    handle.verbose = str_to_bool(node.values[0])
            except Exception as e:
                log.error('Failed to load the configuration {0} due to {1}'
                          .format(node.key, e))
        log.debug('MarathonPlugin.configure_callback() : compete')

    def init_callback(self):
        log.debug('MarathonPlugin.init_callback() : invoked')
        collectd.register_read(self.read_callback)
        collectd.register_config(self.configure_callback)
        log.debug('MarathonPlugin.init_callback() : complete')
        return True

    def read_callback(self):
        log.debug('MarathonPlugin.read_callback() : invoked')

        # Iterate over host objects
        for host in self.hosts:
            host.read()
        log.debug('MarathonPlugin.read_callback() : complete')

    def flush_callback(self):
        log.debug('MarathonPlugin.flush_callback() : invoked')
        log.debug('MarathonPlugin.flush_callback() : complete')


class CollectdLogHandler(logging.Handler):
    """Log handler to forward statements to collectd
    A custom log handler that forwards log messages raised
    at level debug, info, notice, warning, and error
    to collectd's built in logging.  Suppresses extraneous
    info and debug statements using a "verbose" boolean
    Inherits from logging.Handler
    Arguments
        plugin -- name of the plugin (default 'unknown')
        verbose -- enable/disable verbose messages (default False)
    """
    def __init__(self, plugin="unknown", verbose=False):
        """Initializes CollectdLogHandler
        Arguments
            plugin -- string name of the plugin (default 'unknown')
            verbose -- enable/disable verbose messages (default False)
        """
        self.verbose = verbose
        self.plugin = plugin
        logging.Handler.__init__(self, level=logging.NOTSET)

    def emit(self, record):
        """
        Emits a log record to the appropraite collectd log function
        Arguments
        record -- str log record to be emitted
        """
        try:
            if record.msg is not None:
                if record.levelname == 'ERROR':
                    collectd.error('%s : %s' % (self.plugin, record.msg))
                elif record.levelname == 'WARNING':
                    collectd.warning('%s : %s' % (self.plugin, record.msg))
                elif record.levelname == 'NOTICE':
                    collectd.notice('%s : %s' % (self.plugin, record.msg))
                elif record.levelname == 'INFO' and self.verbose is True:
                    collectd.info('%s : %s' % (self.plugin, record.msg))
                elif record.levelname == 'DEBUG' and self.verbose is True:
                    collectd.debug('%s : %s' % (self.plugin, record.msg))
        except Exception as e:
            collectd.warning(('{p} [ERROR]: Failed to write log statement due '
                              'to: {e}').format(p=self.plugin,
                                                e=e
                                                ))


class CollectdLogger(logging.Logger):
    """Logs all collectd log levels via python's logging library
    Custom python logger that forwards log statements at
    level: debug, info, notice, warning, error
    Inherits from logging.Logger
    Arguments
    name -- name of the logger
    level -- log level to filter by
    """
    def __init__(self, name, level=logging.NOTSET):
        """Initializes CollectdLogger
        Arguments
        name -- name of the logger
        level -- log level to filter by
        """
        logging.Logger.__init__(self, name, level)
        logging.addLevelName(25, 'NOTICE')

    def notice(self, msg):
        """Logs a 'NOTICE' level statement at level 25
        Arguments
        msg - log statement to be logged as 'NOTICE'
        """
        self.log(25, msg)


# Set up logging
logging.setLoggerClass(CollectdLogger)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.propagate = False
handle = CollectdLogHandler('Marathon')
log.addHandler(handle)

if __name__ == '__main__':
    import os

    class ExecCollectdValues:
        def dispatch(self):
            if not getattr(self, 'host', None):
                self.host = os.environ.get('COLLECTD_HOSTNAME', 'localhost')
            identifier = '%s/%s' % (self.host, self.plugin)
            if getattr(self, 'plugin_instance', None):
                identifier += '-' + self.plugin_instance
            identifier += '/' + self.type
            if getattr(self, 'type_instance', None):
                identifier += '-' + self.type_instance
            print ('PUTVAL', identifier,
                   ':'.join(map(str, [int(self.time)] + self.values)))

    class ExecCollectd:
        def Values(self):
            return ExecCollectdValues()

        def register_read(self, callback):
            pass

        def register_config(self, callback):
            pass

        def register_init(self, callback):
            pass

        def register_flush(self, callback):
            pass

        def error(self, msg):
            print ('ERROR: ', msg)

        def warning(self, msg):
            print ('WARNING:', msg)

        def notice(self, msg):
            print ('NOTICE: ', msg)

        def info(self, msg):
            print ('INFO:', msg)

        def debug(self, msg):
            print ('DEBUG: ', msg)

    class MockCollectdConfigurations():
        def __init__(self):
            self.children = []

    class MockConfiguration():
        def __init__(self, key, values):
            self.key = key
            self.values = values

    # Instantiate required objects
    handle.verbose = True
    metric_manager = VersionManager(metrics)
    dimension_manager = VersionManager(dims)
    collectd = ExecCollectd()
    plugin = MarathonPlugin()
    configs = MockCollectdConfigurations()
    scheme = 'https'
    host = '10.0.129.78'
    port = '8443'
    user = 'sfx-collectd-1'
    passwd = 'signalfx'
    dcos_auth = 'https://leader.mesos/acs/api/v1/auth/login'
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) == 3:
        port = sys.argv[2]
    if len(sys.argv) == 4:
        user = sys.argv[3]
    if len(sys.argv) == 5:
        passwd = sys.argv[4]

    # Configurations
    mock_configurations = [
        {'host': [scheme, host, port, user, passwd, dcos_auth]},
        {'verbose': ['true']}
    ]
    # Mock collectd configurations
    for conf in mock_configurations:
        for k, v in six.iteritems(conf):
            configs.children.append(MockConfiguration(k, v))

    # Send mock configurations to configuration callback
    plugin.configure_callback(configs)

    if len(sys.argv) > 1:
        plugin.marathon_url = sys.argv[1]

    if not plugin.init_callback():
        sys.exit(1)

    while True:
        plugin.read_callback()
        time.sleep(1)


else:
    import collectd

    metric_manager = VersionManager(metrics)
    dimension_manager = VersionManager(dims)
    plugin = MarathonPlugin()
    collectd.register_config(plugin.configure_callback)
    collectd.register_init(plugin.init_callback)
