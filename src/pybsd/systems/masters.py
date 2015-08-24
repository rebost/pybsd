# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import
import copy
from lazy import lazy
import logging
import six
from ..commands import EzjailAdmin
from ..exceptions import (AttachNonJailError, JailAlreadyAttachedError, DuplicateJailNameError, DuplicateJailHostnameError,
                          DuplicateJailUidError)
from ..handlers import BaseJailHandler
from .base import System
from .jails import Jail

__logger__ = logging.getLogger('pybsd')


class Master(System):
    """Describes a system that will host jails

    Parameters
    ----------
    name : :py:class:`str`
        a name that identifies the system.
    ext_if : :py:class:`tuple` (:py:class:`str`, :py:class:`list` [:py:class:`str`])
        Definition of the system's outward-facing interface
    int_if : Optional[ :py:class:`tuple` (:py:class:`str`, :py:class:`list` [:py:class:`str`]) ]
        Definition of the system's internal network-facing interface. If it is not specified it defaults to ext_if,
        as in that case the same interface will be used for all networks.
    lo_if : Optional[ :py:class:`tuple` (:py:class:`str`, :py:class:`list` [:py:class:`str`]) ]
        Definition of the system's loopback interface. It defaults to ('lo0', ['127.0.0.1/8', '::1/110'])
    j_if : Optional[ :py:class:`tuple` (:py:class:`str`, :py:class:`list` [:py:class:`str`]) ]
        Definition of the interface the system provides to hosted jails as their external interface. By default, this will be
        the system's own ext_if.
    jlo_if : Optional[ :py:class:`tuple` (:py:class:`str`, :py:class:`list` [:py:class:`str`]) ]
        Definition of the interface the system provides to hosted jails as their loopback interface. By default, this will be
        the system's own lo_if.
    hostname : Optional[:py:class:`int`]
        The system's hostname.

    Attributes
    ----------
    JailHandlerClass : :py:class:`class`
        the class of the system's jail handler. It must be or extend :py:class:`~pybsd.BaseJailHandler`
    """
    JailHandlerClass = BaseJailHandler
    default_jail_type = 'Z'

    def __init__(self, name, ext_if, int_if=None, lo_if=None, j_if=None, jlo_if=None, hostname=None):
        super(Master, self).__init__(name, ext_if, int_if, lo_if, hostname)
        self._j_if = self.make_if(j_if)
        self._jlo_if = self.make_if(jlo_if)
        self.ezjail_admin = EzjailAdmin(env=self)
        self.jail_handler = self.JailHandlerClass(master=self)
        self.jails = {}

    @property
    def j_if(self):
        """:py:class:`~pybsd.Interface`: the interface the system provides to hosted jails as their external interface. By default,
        this will be the system's own ext_if.
        """
        return self._j_if or self.ext_if

    def reset_j_if(self):
        """Resets the system's j_if to its default value (its own ext_if)"""
        self._j_if = None

    @property
    def jlo_if(self):
        """:py:class:`~pybsd.Interface`: the interface the system provides to hosted jails as their loopback interface. By default,
        this will be the system's own lo_if.
        """
        return self._jlo_if or self.lo_if

    def reset_jlo_if(self):
        """Resets the system's jlo_if to its default value (its own lo_if)"""
        self._jlo_if = None

    def add_jail(self, jail):
        """Adds a jail to the system's jails list.

        Re-attaching an already-owned jail is transparent.

        Parameters
        ----------
        jail : :py:class:`~pybsd.Jail`
            The jail to be added

        Returns
        -------
        :py:class:`~pybsd.Jail`
            the jail that was added. This allows chaining of commands.

        Raises
        ------
        : :py:exc:`~pybsd.AttachNonJailError`
            if `jail` is not an instance of :py:class:`~pybsd.Jail`
        : :py:exc:`~pybsd.JailAlreadyAttachedError`
            if `jail` is already attached to another :py:class:`~pybsd.Master`
        : :py:exc:`~pybsd.DuplicateJailNameError`
            if another :py:class:`~pybsd.Jail` with the same name is already attached to `master`
        : :py:exc:`~pybsd.DuplicateJailHostnameError`
            if another :py:class:`~pybsd.Jail` with the same hostname is already attached to `master`
        : :py:exc:`~pybsd.DuplicateJailUidError`
            if another :py:class:`~pybsd.Jail` with the same uid is already attached to `master`
        """
        if not isinstance(jail, Jail):
            raise AttachNonJailError(self, jail)
        elif jail.is_attached:
            if jail.master == self:
                return jail
            raise JailAlreadyAttachedError(self, jail)
        elif jail.name in self.jails:
            raise DuplicateJailNameError(self, jail)
        elif jail.hostname in self.hostnames:
            raise DuplicateJailHostnameError(self, jail)
        elif jail.uid in self.uids:
            raise DuplicateJailUidError(self, jail)
        else:
            self.jails[jail.name] = jail
            jail.master = self
            jail.jail_type = jail.jail_type or self.default_jail_type
            return jail

    @property
    def hostnames(self):
        return [j.hostname for k, j in six.iteritems(self.jails)]

    @property
    def uids(self):
        return [j.uid for k, j in six.iteritems(self.jails)]

    def clone_jail(self, jail, name, uid, hostname=None):
        _jail = copy.deepcopy(jail)
        _jail.name = name
        _jail.hostname = hostname
        _jail.uid = uid
        _jail.master = None
        return self.add_jail(_jail)

    @lazy
    def ezjail_admin_binary(self):
        return u'/usr/local/bin/ezjail-admin'
