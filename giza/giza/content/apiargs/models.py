# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import copy

from giza.core.inheritance import InheritableContentBase, InheritanceReference

if sys.version_info >= (3, 0):
    basestring = str

class ApiArgData(InheritableContentBase):
    _option_registry = [
                         'arg_name', # TODO validate because limited field types
                         'interface', # TODO validate because limited possibilities
                         'operation'
                       ]

    @property
    def description(self):
        if self.optional is True:
            return 'Optional. ' + self.state['description']
        else:
            return self.state['description']

    @description.setter
    def description(self, value):
        if isinstance(value, list):
            value = '\n'.join(value)

        if not isinstance(value, basestring):
            raise TypeError

        if value.startswith('Optional. '):
            value = value[11:]
            self.optional = True

        self.state['description'] = value

    @property
    def type(self):
        return self.state['type']

    @type.setter
    def type(self, value):
        if 'type' not in self.state:
            self.state['type'] = []

        if isinstance(value, list):
            self.state['type'].extend(value)
        else:
            self.state['type'].append(value)

    def type_for_field_output(self):
        return ', '.join(self.type)

    def type_for_table_output(self):
        if len(self.type) == 0:
            return ''
        elif len(self.type) == 1:
            return self.type[0]
        elif len(self.type) == 2:
            return ' or '.join(self.type)
        else:
            tmp = copy.copy(self.type)
            tmp[-1] = ' or ' + tmp[-1]
            return ', '.join(tmp)

    @property
    def source(self):
        if 'source' in self.state:
            return self.state['source']
        else:
            return None

    @source.setter
    def source(self, value):
        if 'name' not in self.state and 'ref' not in self.state:
            try:
                self.state['name'] = value['name']
            except KeyError:
                self.state['ref'] = value['ref']

        self.state['source'] = InheritanceReference(value, self.conf)

    inherit = source

    @property
    def ref(self):
        if 'name' in self.state:
            return self.state['name']
        elif 'ref' in self.state:
            return self.state['ref']
        else:
            raise ValueError

    @ref.setter
    def ref(self, value):
        self.state['ref'] = value

    @property
    def name(self):
        if 'name' in self.state:
            return self.state['name']
        elif 'ref' in self.state:
            return self.state['ref']
        else:
            raise TypeError

    @name.setter
    def name(self, value):
        if isinstance(value, basestring):
            self.state['name'] = value
            self.state['ref'] = value
        else:
            raise TypeError

    @property
    def position(self):
        if not hasattr(self, '_position'):
            self._position = None

        return self._position

    @position.setter
    def position(self, value):
        if not hasattr(self, '_position'):
            self._position = None

        if isinstance(value, (int, float, complex)):
            self._position = int(value)
            self.state['position'] = self._position
        else:
            raise TypeError

    @property
    def optional(self):
        if 'optional' in self.state:
            return True
        else:
            return False

    @optional.setter
    def optional(self, value):
        if value is True:
            self.state['optional'] = True
        else:
            self.state['optional'] = False
