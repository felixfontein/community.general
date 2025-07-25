# -*- coding: utf-8 -*-
# Copyright (c) 2015, Steve Gargan <steve.gargan@gmail.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r"""
author: Unknown (!UNKNOWN)
name: consul_kv
short_description: Fetch metadata from a Consul key value store
description:
  - Lookup metadata for a playbook from the key value store in a Consul cluster. Values can be easily set in the kv store
    with simple rest commands.
  - C(curl -X PUT -d 'some-value' http://localhost:8500/v1/kv/ansible/somedata).
requirements:
  - 'python-consul python library U(https://python-consul.readthedocs.io/en/latest/#installation)'
options:
  _raw:
    description: List of key(s) to retrieve.
    type: list
    elements: string
  recurse:
    type: boolean
    description: If V(true), retrieves all the values that have the given key as prefix.
    default: false
  index:
    description:
      - If the key has a value with the specified index then this is returned allowing access to historical values.
    type: int
  datacenter:
    description:
      - Retrieve the key from a consul datacenter other than the default for the consul host.
    type: str
  token:
    description: The acl token to allow access to restricted values.
    type: str
  host:
    default: localhost
    type: str
    description:
      - The target to connect to, must be a resolvable address.
      - It is determined from E(ANSIBLE_CONSUL_URL) if that is set.
    ini:
      - section: lookup_consul
        key: host
  port:
    description:
      - The port of the target host to connect to.
      - If you use E(ANSIBLE_CONSUL_URL) this value is used from there.
    type: int
    default: 8500
  scheme:
    default: http
    type: str
    description:
      - Whether to use http or https.
      - If you use E(ANSIBLE_CONSUL_URL) this value is used from there.
  validate_certs:
    default: true
    description: Whether to verify the TLS connection or not.
    type: bool
    env:
      - name: ANSIBLE_CONSUL_VALIDATE_CERTS
    ini:
      - section: lookup_consul
        key: validate_certs
  client_cert:
    description: The client cert to verify the TLS connection.
    type: str
    env:
      - name: ANSIBLE_CONSUL_CLIENT_CERT
    ini:
      - section: lookup_consul
        key: client_cert
  url:
    description:
      - The target to connect to.
      - 'Should look like this: V(https://my.consul.server:8500).'
    type: str
    version_added: 1.0.0
    env:
      - name: ANSIBLE_CONSUL_URL
    ini:
      - section: lookup_consul
        key: url
"""

EXAMPLES = r"""
- ansible.builtin.debug:
    msg: 'key contains {{item}}'
  with_community.general.consul_kv:
    - 'key/to/retrieve'

- name: Parameters can be provided after the key be more specific about what to retrieve
  ansible.builtin.debug:
    msg: 'key contains {{item}}'
  with_community.general.consul_kv:
    - 'key/to recurse=true token=E6C060A9-26FB-407A-B83E-12DDAFCB4D98'

- name: retrieving a KV from a remote cluster on non default port
  ansible.builtin.debug:
    msg: "{{ lookup('community.general.consul_kv', 'my/key', host='10.10.10.10', port=2000) }}"
"""

RETURN = r"""
_raw:
  description:
    - Value(s) stored in consul.
  type: dict
"""

from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.common.text.converters import to_text

try:
    import consul

    HAS_CONSUL = True
except ImportError as e:
    HAS_CONSUL = False


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        if not HAS_CONSUL:
            raise AnsibleError(
                'python-consul is required for consul_kv lookup. see http://python-consul.readthedocs.org/en/latest/#installation')

        # get options
        self.set_options(direct=kwargs)

        scheme = self.get_option('scheme')
        host = self.get_option('host')
        port = self.get_option('port')
        url = self.get_option('url')
        if url is not None:
            u = urlparse(url)
            if u.scheme:
                scheme = u.scheme
            host = u.hostname
            if u.port is not None:
                port = u.port

        validate_certs = self.get_option('validate_certs')
        client_cert = self.get_option('client_cert')

        values = []
        try:
            for term in terms:
                params = self.parse_params(term)
                consul_api = consul.Consul(host=host, port=port, scheme=scheme, verify=validate_certs, cert=client_cert)

                results = consul_api.kv.get(params['key'],
                                            token=params['token'],
                                            index=params['index'],
                                            recurse=params['recurse'],
                                            dc=params['datacenter'])
                if results[1]:
                    # responds with a single or list of result maps
                    if isinstance(results[1], list):
                        for r in results[1]:
                            values.append(to_text(r['Value']))
                    else:
                        values.append(to_text(results[1]['Value']))
        except Exception as e:
            raise AnsibleError(
                f"Error locating '{term}' in kv store. Error was {e}")

        return values

    def parse_params(self, term):
        params = term.split(' ')

        paramvals = {
            'key': params[0],
            'token': self.get_option('token'),
            'recurse': self.get_option('recurse'),
            'index': self.get_option('index'),
            'datacenter': self.get_option('datacenter')
        }

        # parameters specified?
        try:
            for param in params[1:]:
                if param and len(param) > 0:
                    name, value = param.split('=')
                    if name not in paramvals:
                        raise AnsibleAssertionError(f"{name} not a valid consul lookup parameter")
                    paramvals[name] = value
        except (ValueError, AssertionError) as e:
            raise AnsibleError(e)

        return paramvals
