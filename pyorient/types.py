import sys
import time
from datetime import date, datetime
from decimal import Decimal


class OrientRecord(object):
    """
    Object that represent an Orient Document / Record

    """
    oRecordData = property(lambda self: self.__o_storage)

    def __str__(self):
        rep = ""
        if self.__o_storage:
            rep = str( self.__o_storage )
        if self.__o_class is not None:
            rep = "'@" + str(self.__o_class) + "':" + rep + ""
        if self.__version is not None:
            rep = rep + ",'version':" + str(self.__version)
        if self.__rid is not None:
            rep = rep + ",'rid':'" + str(self.__rid) + "'"
        return '{' + rep + '}'

    def __init__(self, content=None):

        self.__rid = None
        self.__version = None
        self.__o_class = None
        self.__o_storage = {}

        if not content:
            content = {}
        for key in content.keys():
            if key == '__rid':  # Ex: select @rid, field from v_class
                self.__rid = content[ key ]
                # self.__rid = OrientRecordLink( content[ key ][ 1: ] )
            elif key == '__version':  # Ex: select @rid, @version from v_class
                self.__version = content[key]
            elif key == '__o_class':
                self.__o_class = content[ key ]
            elif key[0:1] == '@':
                # special case dict
                # { '@my_class': { 'accommodation': 'hotel' } }
                self.__o_class = key[1:]
                for _key, _value in content[key].items():
                    self.__o_storage[_key] = _value
            elif key == '__o_storage':
                self.__o_storage = content[key]
            else:
                self.__o_storage[key] = content[key]

    def _set_keys(self, content=dict):
        for key in content.keys():
                self._set_keys( content[key] )

    @property
    def _in(self):
        try:
            return self.__o_storage['in']
        except KeyError:
            return None

    @property
    def _out(self):
        try:
            return self.__o_storage['out']
        except KeyError:
            return None

    @property
    def _rid(self):
        return self.__rid

    @property
    def _version(self):
        return self.__version

    @property
    def _class(self):
        return self.__o_class

    def update(self, **kwargs):
        self.__rid = kwargs.get('__rid', None)
        self.__version = kwargs.get('__version', None)
        if self.__o_class is None:
            self.__o_class = kwargs.get('__o_class', None)

    """ This method is for backward compatibility when someone
        use 'getattr(record, a_key)' """
    def __getattr__(self, item):
        """
        :param item: string
        :return: mixed
        :raise: AttributeError
        """
        try:
            return self.__o_storage[item]
        except KeyError:
            raise AttributeError( "'OrientRecord' object has no attribute "
                                  "'" + item + "'" )


class OrientRecordLink(object):
    def __init__(self, recordlink):
        cid, rpos = recordlink.split(":")
        self.__link = recordlink
        self.clusterID = cid
        self.recordPosition = rpos

    def __str__(self):
        return self.get_hash()

    def get(self):
        return self.__link

    def get_hash(self):
        return "#%s" % self.__link


class OrientBinaryObject(object):
    """
    This will be a RidBag
    """
    def __init__(self, stri):
        self.b64 = stri

    def getRaw(self):
        return "_" + self.b64 + "_"

    def getBin(self):
        import base64
        return base64.b64decode(self.b64)


class OrientCluster(object):
    def __init__(self, name, cluster_id, cluster_type=None, segment=None):
        """
        Information regarding a Cluster on the Orient Server
        :param name: str name of the cluster
        :param id: int id of the cluster
        :param type: cluster type (only for version <24 of the protocol)
        :param segment: cluster segment (only for version <24 of the protocol)
        """
        #: str name of the cluster
        self.name = name
        #: int idof the cluster
        self.id = cluster_id
        self.type = cluster_type
        self.segment = segment

    def __str__(self):
        return "%s: %d" % (self.name, self.id)

    def __eq__(self, other):
        return self.name == other.name and self.id == other.id

    def __ne__(self, other):
        return self.name != other.name or self.id != other.id


class OrientVersion(object):

    def __init__(self, release):
        """
        Object representing Orient db release Version

        :param release: String release
        """

        #: string full OrientDB release
        self.release = release

        #: Major version
        self.major = None

        #: Minor version
        self.minor = None

        #: build number
        self.build = None

        self._parse_version(release)

    def _parse_version( self, string_release ):

        if not isinstance(string_release, str):
            string_release = string_release.decode()

        try:
            version_info = string_release.split( "." )
            self.major = int( version_info[0] )
            self.minor = version_info[1]
            self.build = version_info[2]
        except IndexError:
            pass

        if "-" in self.minor:
            _temp = self.minor.split( "-" )
            self.minor = int( _temp[0] )
            self.build = _temp[1]
        else:
            self.minor = int( self.minor )

        build = self.build.split( " ", 1 )[0]
        try:
            build = int( build )
        except ValueError:
            pass

        self.build = build

    def __str__(self):
        return self.release


class OrientNode(object):
    def __init__(self, node_dict=None):
        """
        Represent a server node in a multi clusered configuration

        TODO: extends this object with different listeners if we're going to support in the driver an abstarction of the HTTP protocol, for now we are not interested in that

        :param node_dict: dict with starting configs (usaully from a db_open, db_reload record response)
        """
        #: node name
        self.name = None

        #: node is
        self.id = None

        #: datetime object the node was started
        self.started_on = None

        #: binary listener host
        self.host = None

        #: binary lister port
        self.port = None

        if node_dict is not None:
            self._parse_dict(node_dict)

    def _parse_dict(self, node_dict):
        self.id = node_dict['id']
        self.name = node_dict['name']
        self.started_on = node_dict['startedOn']
        listener = None
        for l in node_dict['listeners']:
            if l['protocol'] == 'ONetworkProtocolBinary':
                listener = l
                break

        if listener:
            listen = listener['listen'].split(':')
            self.host = listen[0]
            self.port = listen[1]

    def __str__(self):
        return self.name
