"""
Common utility functions for dealing with metrics in collectd
"""

# This is only available when run in the collectd embedded python interpreter
import collectd


plugin_instance_max_length = 1024


class Metric(object):

    def __init__(self, type_instance, type, value, plugin='', plugin_instance='', dimensions=None, host='',
                 time=None, interval=None):
        self.type_instance = type_instance
        self.type = type
        self.value = value
        self.plugin = plugin
        self.plugin_instance = plugin_instance
        self.host = host
        self.time = time
        self.interval = interval
        self.dimensions = dimensions or {}
        self.encoded_dimensions = ''
        if self.dimensions:
            self.encoded_dimensions = encode_dimensions(self.dimensions,
                                                        plugin_instance_max_length - len(plugin_instance) - 2)

    def emit(self):
        kw = dict(plugin=self.plugin, plugin_instance=self.plugin_instance, type_instance=self.type_instance,
                  type=self.type, values=[self.value])
        if self.encoded_dimensions:
            kw['plugin_instance'] += '[{0.encoded_dimensions}]'.format(self)

        for attr in ('time', 'host', 'interval'):
            val = getattr(self, attr, None)
            if val is not None:
                kw[attr] = val
        val = collectd.Values(**kw)
        val.meta = dict(_=0)
        val.dispatch()

    def __str__(self):
        attrs = ('type_instance', 'type', 'value', 'plugin', 'plugin_instance', 'time', 'encoded_dimensions',
                 'interval', 'host')
        items = ['{0}: {1}'.format(attr, str(getattr(self, attr))) for attr in attrs]
        return 'Metric({0})\n'.format(', '.join(items))

    __repr__ = __str__


def dispatch_values(values=None, dimensions=None,
                    plugin=None, plugin_instance=None,
                    type=None, type_instance=None,
                    plugin_instance_max_length=plugin_instance_max_length,
                    time=None, host=None, interval=None):
    """
    Dispatch a collectd value list with the given fields, using the special
    SignalFx dimension encoding.
    """

    value = Metric(host=host, plugin=plugin, plugin_instance=plugin_instance, time=time, type=type,
                   dimensions=dimensions, type_instance=type_instance, values=values, interval=interval)
    value.emit()


def dispatch_datapoint(metric_name, value, dimensions, plugin):
    """
    A convenience method that papers over some of the complexities of collectd
    value lists when you just want to send a single value
    """
    return dispatch_values(values=[value], dimensions=dimensions,
                           plugin=plugin, type=metric_name)


def encode_dimensions(dimensions=None, max_len=plugin_instance_max_length - 2):
    """
    Encodes a dictionary of key/value pairs as a comma-delimited list of
    key=value tokens.  This string is suitable for use in the `[]` suffix
    syntax in `plugin_instance`, `host`, and `type_instance` fields.
    """
    if dimensions:
        encoded_dimensions = ','.join(['='.join((str(k), str(v))) for (k, v) in dimensions.items()])
        if len(encoded_dimensions) > max_len:
            collectd.warning('Truncating encoded dimensions: {0}'.format(encoded_dimensions))
            encoded_dimensions = encoded_dimensions[:max_len]
        return encoded_dimensions
    return ''
