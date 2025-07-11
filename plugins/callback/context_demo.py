# -*- coding: utf-8 -*-
# Copyright (C) 2012, Michael DeHaan, <michael.dehaan@gmail.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
author: Unknown (!UNKNOWN)
name: context_demo
type: aggregate
short_description: Demo callback that adds play/task context
description:
  - Displays some play and task context along with normal output.
  - This is mostly for demo purposes.
requirements:
  - whitelist in configuration
"""

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    This is a very trivial example of how any callback function can get at play and task objects.
    play will be 'None' for runner invocations, and task will be None for 'setup' invocations.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'community.general.context_demo'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)
        self.task = None
        self.play = None

    def v2_on_any(self, *args, **kwargs):
        self._display.display(f"--- play: {getattr(self.play, 'name', None)} task: {self.task} ---")

        self._display.display("     --- ARGS ")
        for i, a in enumerate(args):
            self._display.display(f'     {i}: {a}')

        self._display.display("      --- KWARGS ")
        for k in kwargs:
            self._display.display(f'     {k}: {kwargs[k]}')

    def v2_playbook_on_play_start(self, play):
        self.play = play

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.task = task
