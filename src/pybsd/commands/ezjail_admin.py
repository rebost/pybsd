# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging

import lazy

from ..exceptions import InvalidOutputError, SubprocessError, WhitespaceError
from .base import BaseCommand

__logger__ = logging.getLogger('pybsd')


class EzjailAdmin(BaseCommand):
    """Provides an interface to the ezjail-admin command"""

    name = 'ezjail-admin'

    @property
    def binary(self):
        return self.env.ezjail_admin_binary

    def check_kwargs(self, subcommand, **kwargs):
        # make sure there is no whitespace in the arguments
        for key, value in kwargs.items():
            if value is None:
                continue
            if subcommand == 'console' and key == 'cmd':
                continue
            if len(value.split()) != 1:
                raise WhitespaceError(self, self.env, key, value, subcommand)

    @lazy.lazy
    def list_headers(self):
        """
        rc:  command return code
        out: command stdout
        err: command stderr
        """
        rc, out, err = self.invoke('list')
        if rc:
            raise SubprocessError(self, self.env, err.strip(), 'list_headers')
        lines = out.splitlines()
        if len(lines) < 2:
            raise InvalidOutputError(self, self.env, u'output too short', 'list')
        headers = []
        current = ''
        for pos, char in enumerate(lines[1]):
            if char != '-' or pos >= len(lines[0]):
                headers.append(current.strip())
                if pos >= len(lines[0]):
                    break
                current = ''
            else:
                current = current + lines[0][pos]
        if headers != ['STA', 'JID', 'IP', 'Hostname', 'Root Directory']:
            raise InvalidOutputError(self, self.env, u"output has unknown headers\n['{}']".format(u"', '".join(headers)), 'list')
        return ('status', 'jid', 'ip', 'name', 'root')

    def list(self):
        headers = self.list_headers
        rc, out, err = self.invoke('list')
        if rc:
            raise SubprocessError(self, self.env, err.strip(), 'list')
        lines = out.splitlines()
        jails = {}
        current_jail = None
        for line in lines[2:]:
            if line[0:4] != '    ':
                line = line.strip()
                if not line:
                    continue
                entry = dict(zip(headers, line.split()))
                entry['ips'] = [entry['ip']]
                current_jail = jails[entry.pop('name')] = entry
            else:
                line = line.strip()
                if not line:
                    continue
                if_ip = line.split()[1]
                ip = if_ip.split('|')[1]
                current_jail['ips'].append(ip)
        return jails

    def console(self, cmd, jail_name):
        self.check_kwargs('console', cmd=cmd, jail_name=jail_name)
        rc, out, err = self.invoke('console',
                                   '-e',
                                   cmd,
                                   jail_name)
        return out

    # subcommands to be implemented:
    # def __ezjail_admin(self, subcommand, **kwargs):
    #     # make sure there is no whitespace in the arguments
    #     for key, value in kwargs.items():
    #         if value is None:
    #             continue
    #         if subcommand == 'console' and key == 'cmd':
    #             continue
    #         if len(value.split()) != 1:
    #             __logger__.error('The value `%s` of kwarg `%s` contains whitespace', value, key)
    #             sys.exit(1)
    #     if subcommand == 'console':
    #         return self._ezjail_admin(
    #             'console',
    #             '-e',
    #             kwargs['cmd'],
    #             kwargs['name'])
    #     elif subcommand == 'create':
    #         args = [
    #             'create',
    #             '-c', 'zfs']
    #         flavour = kwargs.get('flavour')
    #         if flavour is not None:
    #             args.extend(['-f', flavour])
    #         args.extend([
    #             kwargs['name'],
    #             kwargs['ip']])
    #         rc, out, err = self._ezjail_admin(*args)
    #         if rc:
    #             raise SubprocessError(self, self.env, err.strip(), 'create')
    #     elif subcommand == 'delete':
    #         rc, out, err = self._ezjail_admin(
    #             'delete',
    #             '-fw',
    #             kwargs['name'])
    #         if rc:
    #             raise SubprocessError(self, self.env, err.strip(), 'delete')
    #     elif subcommand == 'start':
    #         rc, out, err = self._ezjail_admin(
    #             'start',
    #             kwargs['name'])
    #         if rc:
    #             raise SubprocessError(self, self.env, err.strip(), 'start')
    #     elif subcommand == 'stop':
    #         rc, out, err = self._ezjail_admin(
    #             'stop',
    #             kwargs['name'])
    #         if rc:
    #             raise SubprocessError(self, self.env, err.strip(), 'stop')
    #     else:
    #         raise ValueError('Unknown subcommand `%s`' % subcommand)
