# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import unittest

from pybsd import (BaseCommand, CommandConnectionError, CommandNotImplementedError, InvalidCommandExecutorError,
                   InvalidCommandNameError, Master)

from ..test_executors import TestExecutor


class NoNameCommand(BaseCommand):
    pass


class NoBinaryCommand(BaseCommand):
    name = 'some_command'


class BaseCommandTestCase(unittest.TestCase):
    executor_class = TestExecutor
    params = {
        'name': 'system',
        'hostname': 'system.foo.bar',
        'ext_if': ('re0', ['8.8.8.8/24']),
        'int_if': ('eth0', ['192.168.0.0/24'])
    }

    def setUp(self):

        class TestMaster(Master):
            ExecutorClass = self.executor_class

        self.system = TestMaster(**self.params)

    def test_no_name_command(self):
        with self.assertRaises(InvalidCommandNameError) as context_manager:
            NoNameCommand(env='something')
        self.assertEqual(context_manager.exception.message,
                         "Can't initialize command: `tests.commands.test_base` is missing a `name` property.")

    def test_env_no_executor(self):
        with self.assertRaises(InvalidCommandExecutorError) as context_manager:
            NoBinaryCommand(env='something')
        self.assertEqual(context_manager.exception.message,
                         "Can't initialize command: `some_command` must have a callable `Executor` method.")

    def test_env_executor_not_callable(self):
        self.system.execute = None
        with self.assertRaises(InvalidCommandExecutorError) as context_manager:
            NoBinaryCommand(env='something')
        self.assertEqual(context_manager.exception.message,
                         "Can't initialize command: `some_command` must have a callable `Executor` method.")

    def test_no_binary_command(self):
        _bc = NoBinaryCommand(env=self.system)
        with self.assertRaises(CommandNotImplementedError) as context_manager:
            _bc.invoke()
        self.assertEqual(context_manager.exception.message,
                         "Can't execute command: `some_command` is not implemented on `{system.name}`.".format(system=self.system))

    @unittest.skip('Cannot be tested until BaseCommand is actually able to connect remotely')
    def test_socket_error(self):
        with self.assertRaises(CommandConnectionError) as context_manager:
            pass
        self.assertEqual(context_manager.exception.message,
                         "Can't execute command: `some_command` - can't connect to `system.foo.bar`.")
