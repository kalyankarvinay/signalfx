from shlex import shlex


class ParsedConfig(object):
    """Converts a collectd plugin properties block to a pseudo-collectd config object
    cfg_str = '''
    DescriptorOne "one" "two" "three"
    DescriptorTwo 123 true "test"
    '''
    cfg = ParsedConfig(cfg_str)
    assert cfg.children[0].values == ['one', 'two', 'three']
    assert cfg.children[1].values == [123.0, True, 'test']
    """

    class Child(object):

        def __init__(self, properties_string):
            boolean = dict(true=True, false=False)
            sh = shlex(properties_string)
            sh.whitespace_split = True
            items = list(iter(sh.get_token, ''))
            self.key = items[0]
            self.values = items[1:]
            for i, item in enumerate(self.values):
                if '"' in item:
                    self.values[i] = item.replace('"', '')
                elif item in ('true', 'false'):
                    self.values[i] = boolean[item]
                else:
                    self.values[i] = float(item)

    def __init__(self, config_string=''):
        properties = [p.lstrip() for p in config_string.split('\n') if p.lstrip()]
        self.children = [self.Child(prop) for prop in properties]
