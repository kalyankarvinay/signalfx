# Introduction

collectd-mongodb is a [collectd](http://www.collectd.org/) plugin that collects statistics from a MongoDB server.

This plugin is a direct port of the MongoDB C plugin that will be part of collectd 5.1, it works with Collectd 4.9.x and 4.10.x.

# Requirements

* Collectd 4.9 or later (for the Python plugin)
* Python 2.4 or later
* MongoDB 2.6 or later
* PyMongo 3.x (**To use SSL/TLS, install Pymongo with TLS support by running `pip install pymongo[tls]`.**)

# Configuration

The plugin has some configuration options even though none are mandatory. This is done by passing parameters via the <Module> config section in your Collectd config. The following parameters are recognized:

* `User` - the username for authentication
* `Password` - the password for authentication
* `Host` - hostname or IP address of the mongodb server; defaults to 127.0.0.1
* `Port` - the port of the mongodb server; defaults to 27017
* `Database` - the databases you want to monitor defaults to "admin". You can provide more than one database. Note that the first database _must_ be "admin", as it is used to perform a serverStatus()
* `Interval` - How frequently to send metrics in seconds | collectd `Interval` setting |
* `SendCollectionMetrics` - Whether to send collection level metrics or not; defaults to false.
* `SendCollectionTopMetrics` - Whether to send collection level top (timing) metrics or not; defaults to false.
* `CollectionMetricsIntervalMultiplier` - How frequently to send collection level metrics as a multiple of the configured plugin interval (e.g. if the Interval is 15 and the multiplier is 4, collection level metrics will be fetched every minute); defaults to `6`.

## SSL/TLS Configuration
**To use SSL/TLS, install Pymongo with TLS support by running `pip install pymongo[tls]`.**

* UseTLS - set this to `true` if you want to connect to Mongo using TLS/x509/SSL.
* CACerts - path to a CA cert that will be used to verify the certificate that
    Mongo presents (not needed if not using TLS or if Mongo's cert is signed by
    a globally trusted issuer already installed in the default location on your
    OS)
* TLSClientCert - path to a client certificate (not needed unless your Mongo
    instance requires x509 client verification)
* User (**required for TLS client auth**) - The username associated with the client cert
    (this is the *subject* field of the client cert, formatted according to
    RFC2253 **and in the same order that was specified when creating the user
    in the Mongo `$external` database**).  You can get this value by running
    the following command: `openssl x509 -in <pathToClient PEM> -inform PEM
    -subject -nameopt RFC2253`.
* TLSClientKey - path to a client certificate key (not needed unless your Mongo
    instance requires x509 client verification, or if your client cert above
    has the key included)
* TLSClientKeyPassphrase - passphrase for the TLSClientKey above (not needed if
    not using TLS Client auth, requires Python 2.7.9+)




The following is an example Collectd configuration for this plugin:

    <LoadPlugin python>
        Globals true
    </LoadPlugin>

    <Plugin python>
        # mongodb.py is at path /opt/collectd-plugins/mongodb.py
        ModulePath "/opt/collectd-plugins/"

        Import "mongodb"
        <Module mongodb>
            Host "127.0.0.1"
            Port "27017"
            User ""
            Password "password"
            Database "admin" "db-prod" "db-dev"

            UseTLS true

            # If using TLS client auth with cert and key in same file without passphrase
            TLSClientCert "/path/to/cert.pem"
            User "CN=example.com,OU=Acme\,Inc,L=Springfield,C=US"
        </Module>
    </Plugin>

The data-sets in types.db need to be added to the types.db file given by the collectd.conf TypesDB directive. See the types.db(5) man page for more information.

If you're monitoring a secured MongoDB deployment, declaring a user with minimal read-only roles is a good practice, such as : 


    db.createUser( {
      user: "collectd",
      pwd: "collectd",
      roles: [ { role: "readAnyDatabase", db: "admin" }, { role: "clusterMonitor", db: "admin" } ]
    });
 
