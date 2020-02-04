#!/usr/bin/python

import sys, os, time, re, subprocess

class Dispatch:
    def dispatch(self):
      pass

class DummyCollectd:
    def Values(self, plugin=None, type_instance=None, plugin_instance=None, type=None, values=None):
        print plugin, type_instance, plugin_instance, type, values
        return Dispatch()

try:
    import collectd
    import logging

    logging.basicConfig(level=logging.INFO)
except ImportError:
    collectd = DummyCollectd()

PLUGIN_NAME = 'version-checker'
TYPE_INSTANCE = 'vesion_check'
PLUGIN_INSTANCE = "example[docker=%s,running=kernel-%s,installed=%s]"

def popen(command):
    """ using subprocess instead of check_output for 2.6 comparability """
    output = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0]
    return output.strip()

def read():
    """
    produce a metric for configured versions of installed packages

    :return: None
    """

    release = popen(["uname", "-r"])
    docker = popen(["rpm", "-q", "docker"])
    installed = popen(["rpm", "-q", "kernel"])
    installed = installed.split("\n")[-1]

    collectd.Values(plugin=PLUGIN_NAME,
                    type_instance=TYPE_INSTANCE,
                    plugin_instance=PLUGIN_INSTANCE % (docker,release,installed),
                    type="gauge",
                    values=[1]).dispatch()


if __name__ != "__main__":
    collectd.register_read(read)
else:
    # outside plugin just collect the info
    read()
    if len(sys.argv) < 2:
        while True:
            time.sleep(10)
            read()
