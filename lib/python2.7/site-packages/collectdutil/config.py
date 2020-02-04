"""
Functions to help with collectd config objects.

See https://collectd.org/documentation/manpages/collectd-python.5.shtml#config
for a description of the config class passed into Python plugins by collectd.
"""
import collectd


def simple_config_to_dict(conf):
    """
    Converts a basic collectd config object to a dictionary, flattening any values
    that only have a single item into that single item as the value.

    If a config key appears more than once, the value in the dict will be a
    list of all of its occurrances.

    This does NOT support config instances with children config objects.
    """
    out = {}

    for val in conf.children:
        flattened_val = val.values
        if len(val.values) == 1:
            flattened_val = val.values[0]

        prev = out.get(val.key)
        if prev is not None:
            if not isinstance(prev, (list, tuple)):
                prev = [prev]

            flattened_val = prev + [flattened_val]

        out[val.key] = flattened_val

    return out


class Config(object):
    """Defines behavior and metric default values and translates collectd plugin configurations to object attributes.
    Takes a collectd generated config object and descriptor and metric dictionary specifications of the form:

    <Module my_plugin>
      DescriptorOne "desired_value"
      DescriptorTwo false
      Username "my_username"
      DescriptorThree "one"
      DescriptorThree "two" "three"
      DescriptorThree "four "five"
      ExtraDimension "custom_dimension" "dim_value"
      ExtraDimension "another_custom" "some_value"
    </Module>

    descriptors = {  # Plugin config descriptor to Config() attribute (w/ default value)
        'DescriptorOne': ('descriptor_one', 'some_default_value'),
        'DescriptorTwo': ('another_attribute', True),
        'URL': ('my_url', 'http://localhost/something'),
        'Username': ('username', 'admin'),
        'DescriptorThree': ('descriptor_three', 123)
    }

    cfg = Config(config, descriptors=descriptors)  # config is provided via collectd config callback
    assert cfg.descriptor_one == 'desired_value'
    assert cfg.another_attribute is False
    assert cfg.my_url == 'http://localhost/something'
    assert cfg.username == 'my_username'
    assert cfg.descriptor_three == [['one'], ['two', 'three'], ['four', 'five']]
    assert cfg.extra_dimensions == dict(custom_dimension='dim_value', another_custom='some_value')

    <Module my_plugin>
      Metric "metric_one" false
      Metric "metric_three" true
      Metric "metric_four" false
    </Module>

    metrics = {  # Metric descriptor first value (attribute) to type_instance, type, and default reporting flag
        'metric_one': ('plugin.metric.one', 'counter', True),
        'metric_two': ('plugin.metric.two', 'gauge', True),
        'metric_three': ('plugin.metric.three', 'derive', False),
        'metric_four': ('plugin.metric.four', 'absolute', True)
    }

    cfg = Config(config, metrics=metrics)
    assert cfg.metric_one is False
    assert cfg.metric_two is True
    assert cfg.metric_three is True
    assert cfg.metric_four is False
    type_instance, metric_type = cfg.metrics['metric_one'][:-1]

    All descriptor and metric key values will be made lowercase for case insensitivity.
    """

    def __init__(self, config=None, descriptors=None, metrics=None):
        descriptors = descriptors or {}
        metrics = metrics or {}
        # case insensitivity
        self.descriptors = dict([(k.lower(), v) for k, v in descriptors.items()])
        self.metrics = dict([(k.lower(), v) for k, v in metrics.items()])

        self.extra_dimensions = {}

        # Load defaults
        for attr, val in self.descriptors.values():
            setattr(self, attr, val)
        for attr, val in self.metrics.items():
            setattr(self, attr, val[2])
        if not config:
            return

        seen = set()
        for child in config.children:
            descriptor = child.key.lower()
            if descriptor == 'metric':
                if not child.values:
                    raise TypeError('Missing metric name provided in plugin config.')
                metric = child.values[0].lower()
                if metric not in self.metrics:
                    collectd.warning('Unsupported metric "{0}".'.format(metric))
                    continue
                if len(child.values) != 2:
                    prefix = 'No boolean' if len(child.values) == 1 else 'Too many values'
                    default = getattr(self, metric)
                    collectd.warning('{0} provided for Metric "{1}." Using default value {2}'
                                     .format(prefix, metric, str(default).lower()))
                else:
                    setattr(self, metric, bool(child.values[1]))
            else:
                if descriptor == 'extradimension':
                    if len(child.values) != 2:
                        collectd.warning('Invalid ExtraDimension values: {0}. Will not source.'
                                         .format(str(child.values)))
                        continue
                    self.extra_dimensions[child.values[0]] = child.values[1]
                    continue
                if descriptor not in self.descriptors:
                    collectd.warning('Unsupported config descriptor "{0.key}".'.format(child))
                    continue
                attr = self.descriptors[descriptor][0]
                if attr in seen:
                    current = getattr(self, attr)
                    current.append(child.values)
                else:
                    seen.add(attr)
                    setattr(self, attr, [child.values])
        for attr in seen:  # Single child values shouldn't be in lists
            current = getattr(self, attr)
            if len(current) == 1:
                if len(current[0]) == 1:
                    current = current[0]
                setattr(self, attr, current[0])

    def __str__(self):
        descriptors = ['{0}: {1}'.format(v[0], getattr(self, v[0])) for v in self.descriptors.values()]
        descriptors.sort()
        cfg = 'Config: ' + '\n'.join(descriptors)
        cfg += '\nMetrics: ' + '\n'.join(['{0}: {1}'.format(k, getattr(self, k)) for k in self.metrics])
        return cfg

    __repr__ = __str__
