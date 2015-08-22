# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import
import ipaddress
import unittest
import unipath
from pybsd import System, Jail, Master
from .. import extract_message


class JailTestCase(unittest.TestCase):
    master_params = {
        'name': 'master',
        'hostname': 'master.foo.bar',
        'ext_if': ('re0', ['148.241.178.106/24', '1c02:4f8:0f0:14e6::/110']),
        'int_if': ('eth0', ['192.168.0.0/24', '1c02:4f8:0f0:14e6::0:0:1/110']),
        # 'lo_if': ('lo0', ['127.0.0.1/24', '::1/110']),
        'j_if': ('re0', ['10.0.2.0/24', '10.0.1.0/24', '1c02:4f8:0f0:14e6::2:0:1/110', '1c02:4f8:0f0:14e6::1:0:1/110']),
        'jlo_if': ('lo1', ['127.0.2.0/24', '127.0.1.0/24', '::0:2:0:0/110', '::0:1:0:0/110']),
    }
    params = {
        'name': 'system',
        'uid': 12,
        'hostname': 'system.foo.bar',
        'master': None,
        'jail_type': 'Z',
        'auto_start': True,
        'jail_class': 'web',
    }

    def setUp(self):
        params = self.params.copy()
        params['master'] = Master(**self.master_params)
        self.system = Jail(**params)

    def test_bad_master(self):
        master_params = self.master_params.copy()
        del master_params['j_if']
        del master_params['jlo_if']
        params = self.params.copy()
        params['master'] = System(**master_params)
        with self.assertRaises(SystemError) as context_manager:
            self.system = Jail(**params)
        self.assertEqual(extract_message(context_manager), u'`master` is not a jail master')

    def test_clone_jail(self):
        jail2 = self.system.master.clone_jail(self.system, 'new_jail', 13)
        self.assertNotEqual(self.system, jail2)

    def test_idempotent_add_jail(self):
        jail2 = self.system.master.add_jail(self.system)
        self.assertEqual(self.system, jail2)

    def test_already_attached(self):
        master2 = Master(name='master2',
                         hostname='master2.foo.bar',
                         ext_if=('re0', ['8.8.8.8/24'])
                         )
        with self.assertRaises(SystemError) as context_manager:
            master2.add_jail(self.system)
        self.assertEqual(extract_message(context_manager), u'Jail `system` is already attached to `master`')

    def test_no_name(self):
        params = self.params.copy()
        del params['name']
        with self.assertRaises(TypeError):
            Jail(**params)

    def test_name(self):
        self.assertEqual(self.system.name, 'system',
                        'incorrect name')

    def test_no_hostname(self):
        params = self.params.copy()
        del params['hostname']
        system = Jail(**params)
        self.assertEqual(system.hostname, 'system',
                        'incorrect hostname')

    def test_hostname(self):
        self.assertEqual(self.system.hostname, 'system.foo.bar',
                        'incorrect hostname')

    def test_no_uid(self):
        params = self.params.copy()
        del params['uid']
        with self.assertRaises(TypeError):
            self.system = Jail(**params)

    def test_uid(self):
        self.assertEqual(self.system.uid, 12,
                        'incorrect uid')

    def test_unattached_no_jail_type(self):
        params = self.params.copy()
        del params['jail_type']
        del params['master']
        self.system = Jail(**params)
        self.assertEqual(self.system.jail_type, None,
                        'incorrect jail_type')

    def test_attached_no_jail_type(self):
        master_params = self.master_params.copy()
        master_params['name'] = 'foo'
        params = self.params.copy()
        del params['jail_type']
        params['master'] = Master(**master_params)
        self.system = Jail(**params)
        self.assertEqual(self.system.jail_type, 'Z',
                        'incorrect jail_type')

    def test_jail_type(self):
        self.assertEqual(self.system.jail_type, 'Z',
                        'incorrect jail_type')

    def test_no_auto_start(self):
        params = self.params.copy()
        del params['auto_start']
        self.system = Jail(**params)
        self.assertEqual(self.system.auto_start, False,
                        'incorrect auto_start')

    def test_auto_start(self):
        self.assertEqual(self.system.auto_start, True,
                        'incorrect auto_start')

    def test_attached_default_status(self):
        self.assertEqual(self.system.status, 'S',
                        'incorrect status')

    def test_unattached_default_status(self):
        params = self.params.copy()
        del params['master']
        self.system = Jail(**params)
        self.assertEqual(self.system.status, 'D',
                        'incorrect jail_type')

    def test_unattached_class_id(self):
        params = self.params.copy()
        del params['master']
        self.system = Jail(**params)
        self.assertEqual(self.system.jail_class_id, None,
                        'incorrect jail_class_id')

    def test_unattached_jid(self):
        params = self.params.copy()
        del params['master']
        self.system = Jail(**params)
        self.assertEqual(self.system.jid, None,
                        'incorrect jid')

    def test_jid(self):
        self.assertEqual(self.system.jid, 1,
                        'incorrect jid')

    def test_no_master_path(self):
        params = self.params.copy()
        del params['master']
        self.system = Jail(**params)
        self.assertEqual(self.system.path, None,
                        'incorrect path')

    def test_path(self):
        self.assertEqual(self.system.path, unipath.Path('/usr/jails/system'),
                        'incorrect path')

    def test_no_master_ext_if(self):
        params = self.params.copy()
        del params['master']
        self.system = Jail(**params)
        self.assertEqual(self.system.ext_if, None,
                        'incorrect ext_if')

    def test_ext_if_name(self):
        self.assertEqual(self.system.ext_if.name, 're0',
                        'incorrect ext_if name')

    def test_ext_if_ifsv4(self):
        self.assertSequenceEqual(self.system.ext_if.ifsv4, [ipaddress.IPv4Interface('10.0.2.12/24')],
                        'incorrect ext_if ifsv4')
        self.assertSequenceEqual(self.system.ext_if.ifsv6, [ipaddress.IPv6Interface('1c02:4f8:0f0:14e6::2:12:1/110')],
                        'incorrect ext_if ifsv6')

    def test_ext_if_failed_assignement(self):
        with self.assertRaises(AttributeError) as context_manager:
            self.system.ext_if = ('re0', ['8.8.8.8/24'])
        self.assertEqual(extract_message(context_manager), u"can't set attribute")

    def test_no_master_lo_if(self):
        params = self.params.copy()
        del params['master']
        self.system = Jail(**params)
        self.assertEqual(self.system.lo_if, None,
                        'incorrect lo_if')

    def test_lo_if_name(self):
        self.assertEqual(self.system.lo_if.name, 'lo1',
                        'incorrect lo_if name')

    def test_lo_if_ifsv4(self):
        self.assertSequenceEqual(self.system.lo_if.ifsv4, [ipaddress.IPv4Interface('127.0.2.12/24')],
                        'incorrect lo_if ifsv4')
        self.assertSequenceEqual(self.system.lo_if.ifsv6, [ipaddress.IPv6Interface('::0:2:12:0/110')],
                        'incorrect lo_if ifsv6')

    def test_lo_if_failed_assignement(self):
        with self.assertRaises(AttributeError) as context_manager:
            self.system.lo_if = ('re0', ['8.8.8.8/24'])
        self.assertEqual(extract_message(context_manager), u"can't set attribute")
