import dbus
import collectd


class SystemD(object):
    ACTIVE_STATE = "ActiveState"
    SUB_STATE = "SubState"
    LOAD_STATE = "LoadState"
    ALL_STATES = [ACTIVE_STATE, SUB_STATE, LOAD_STATE]

    def __init__(self):
        self.plugin_name = 'collectd-systemd'
        self.interval = 60.0
        self.verbose_logging = False
        self.services = []
        self.service_states = set()
        self.units = {}

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('{} plugin [verbose]: {}'.format(self.plugin_name, msg))

    def init_dbus(self):
        self.units = {}
        self.bus = dbus.SystemBus()
        self.manager = dbus.Interface(
            self.bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1'),
            'org.freedesktop.systemd1.Manager'
        )

    def get_unit(self, name):
        if name not in self.units:
            try:
                unit = dbus.Interface(self.bus.get_object('org.freedesktop.systemd1',
                                                          self.manager.GetUnit(name)),
                                      'org.freedesktop.DBus.Properties')
            except dbus.exceptions.DBusException as e:
                collectd.warning('{} plugin: failed to monitor unit {}: {}'.format(
                    self.plugin_name, name, e))
                return
            self.units[name] = unit
        return self.units[name]

    def get_service_state(self, name, state):
        unit = self.get_unit(name)
        if not unit:
            return 'broken'
        else:
            try:
                return unit.Get('org.freedesktop.systemd1.Unit', state)
            except dbus.exceptions.DBusException as e:
                self.log_verbose('{} plugin: failed to monitor unit {}: {}'.format(self.plugin_name, name, e))
                return 'broken'

    def configure_callback(self, conf):
        for node in conf.children:
            vals = [str(v) for v in node.values]
            if node.key == 'Service':
                self.services.extend(vals)
            elif node.key == 'ServiceStates':
                self.service_states.update(set(vals))
            elif node.key == 'Interval':
                self.interval = float(vals[0])
            elif node.key == 'Verbose':
                self.verbose_logging = (vals[0].lower() == 'true')
            else:
                raise ValueError('{} plugin: Unknown config key: {}'
                                 .format(self.plugin_name, node.key))
        if not self.services:
            self.log_verbose('No services defined in configuration')
            return
        if not self.service_states:
            self.log_verbose('No service state(s) defined in configuration')
            return
        if not self.service_states.issubset(set(self.ALL_STATES)):
            self.log_verbose('Invalid service state(s) defined in configuration. Valid service states are {0}, {1} '
                             'and {2}'.format(*self.ALL_STATES))
            return

        self.init_dbus()
        collectd.register_read(self.read_callback, self.interval)
        self.log_verbose('Configured with services={}, interval={}'
                         .format(self.services, self.interval))

    def read_callback(self):
        self.log_verbose('Read callback called')
        for name in self.services:
            if self.ACTIVE_STATE in self.service_states:
                self._dispatch_active_states(name)
            if self.SUB_STATE in self.service_states:
                self._dispatch_substates(name)
            if self.LOAD_STATE in self.service_states:
                self._dispatch_load_states(name)

    def _dispatch_active_states(self, name):
        full_name = name + '.service'
        active_state = self.get_service_state(full_name, self.ACTIVE_STATE)
        if active_state == 'broken':
            self.log_verbose(
                'Unit {0} reported as broken. Reinitializing the connection to dbus & retrying.'.format(full_name))
            self.init_dbus()
            active_state = self.get_service_state(full_name, self.ACTIVE_STATE)
        self._dispatch('gauge', name, 'active_state.active', int('active' == active_state), active_state)
        self._dispatch('gauge', name, 'active_state.inactive', int('inactive' == active_state), active_state)
        self._dispatch('gauge', name, 'active_state.activating', int('activating' == active_state), active_state)
        self._dispatch('gauge', name, 'active_state.deactivating', int('deactivating' == active_state), active_state)
        self._dispatch('gauge', name, 'active_state.reloading', int('reloading' == active_state), active_state)
        self._dispatch('gauge', name, 'active_state.failed', int('failed' == active_state), active_state)

    def _dispatch_substates(self, name):
        full_name = name + '.service'
        substate = self.get_service_state(full_name, self.SUB_STATE)
        if substate == 'broken':
            self.log_verbose(
                'Unit {0} reported as broken. Reinitializing the connection to dbus & retrying.'.format(full_name))
            self.init_dbus()
            substate = self.get_service_state(full_name, self.SUB_STATE)
        self._dispatch('gauge', name, 'substate.running', int('running' == substate), substate)
        self._dispatch('gauge', name, 'substate.exited', int('exited' == substate), substate)
        self._dispatch('gauge', name, 'substate.failed', int('failed' == substate), substate)
        self._dispatch('gauge', name, 'substate.dead', int('dead' == substate), substate)

    def _dispatch_load_states(self, name):
        full_name = name + '.service'
        load_state = self.get_service_state(full_name, self.LOAD_STATE)
        if load_state == 'broken':
            self.log_verbose(
                'Unit {0} reported as broken. Reinitializing the connection to dbus & retrying.'.format(full_name))
            self.init_dbus()
            load_state = self.get_service_state(full_name, self.LOAD_STATE)
        self._dispatch('gauge', name, 'load_state.loaded', int('loaded' == load_state), load_state)
        self._dispatch('gauge', name, 'load_state.not-found', int('not-found' == load_state), load_state)
        self._dispatch('gauge', name, 'load_state.error', int('error' == load_state), load_state)
        self._dispatch('gauge', name, 'load_state.masked', int('masked' == load_state), load_state)

    def _dispatch(self, _type, name, type_instance, value, state):
        self.log_verbose('Sending value: {}.{}={} (state={})'.format(self.plugin_name, name, value, state))
        val = collectd.Values(
            type=_type,
            plugin=self.plugin_name,
            type_instance=type_instance,
            meta={'0': True},
            values=[value])
        val.plugin_instance += '[{dims}]'.format(dims='systemd_service='+name)
        val.dispatch()


mon = SystemD()
collectd.register_config(mon.configure_callback)