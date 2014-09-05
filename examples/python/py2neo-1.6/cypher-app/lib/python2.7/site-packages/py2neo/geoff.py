#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011-2014, Nigel Small
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import division, unicode_literals

import json
import logging
import re
from uuid import uuid4

from . import neo4j
from .util import deprecated
from .xmlutil import xml_to_geoff

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


logger = logging.getLogger(__name__)

SIMPLE_NAME = re.compile(r"^[A-Za-z_][0-9A-Za-z_]*$")


class ConstraintViolation(ValueError):
    """ Raised on an attempt to merge a unique path onto a non-unique path.
    """
    pass


class Subgraph(object):

    @classmethod
    def load(cls, file):
        """ Load Geoff data from a file into a Subgraph.
        """
        return cls(file.read())

    @classmethod
    def load_xml(cls, file, prefixes=None):
        """ Load and convert data within an XML file into a Subgraph.
        """
        src = file.read().encode("utf-8")
        file.close()
        return cls(xml_to_geoff(src, prefixes=prefixes))

    def __init__(self, source):
        """ Create a subgraph from Geoff source.
        """
        self._source = source
        parser = _Parser(self._source)
        self._nodes, self._rels, self._index_entries = parser.parse()

    def save(self, file):
        """ Save subgraph to a file in Geoff format.
        """
        pass  #TODO: actually write this bit

    @property
    def source(self):
        """ Return the Geoff source for this Subgraph.
        """
        return self._source

    @property
    def nodes(self):
        """ Return all nodes within this Subgraph.
        """
        return dict(self._nodes)

    @property
    def relationships(self):
        """ Return all relationships within this Subgraph.
        """
        return list(self._rels)

    @property
    def index_entries(self):
        """ Return all index entries within this Subgraph.
        """
        return dict(self._index_entries)

    @property
    def _indexed_nodes(self):
        """ Return the set of nodes which have one or more index entries
        pointing to them.
        """
        return dict(
            (entry.node.name, entry.node)
            for entry in self._index_entries.values()
        )

    @property
    def _related_nodes(self):
        """ Return the set of nodes which are involved in at least one
        relationship.
        """
        nodes = dict(
            (rel.start_node.name, rel.start_node)
            for rel in self._rels
        )
        nodes.update(dict(
            (rel.end_node.name, rel.end_node)
            for rel in self._rels
        ))
        return nodes

    @property
    def _odd_nodes(self):
        """ Return the set of nodes which have no index entries pointing to
        them and are involved in no relationships.
        """
        return dict(
            (name, node)
            for name, node in self._nodes.items()
            if name not in self._indexed_nodes
            if name not in self._related_nodes
        )

    def _get_relationship_query(self, unique):
        # will only work in 1.8.1 and above
        start, create, set, output_names, params = [], [], [], [], {}
        # determine query inputs
        input_names, input_entries = list(self._indexed_nodes.keys()), []
        for name in input_names:
            entry = [
                entry
                for entry in self._index_entries.values()
                if entry.node.name == name
            ][0]
            input_entries.append(entry)
        #
        def node_pattern(i, name):
            if name in input_names:
                return "(in{0})".format(input_names.index(name))
            elif name in output_names:
                return "(out{0})".format(output_names.index(name))
            else:
                try:
                    params["sp{0}".format(i)] = self._nodes[name].properties
                except KeyError:
                    raise SystemError("Broken internal reference - "
                                      "node '{0}' not found".format(name))
                output_names.append(name)
                return "(out{0} {{{1}}})".format(output_names.index(name), "sp{0}".format(i))
            #
        def rel_pattern(i, type_, properties):
            if properties:
                params["rp{0}".format(i)] = properties
                return "-[:`{0}` {{{1}}}]->".format(type_, "rp{0}".format(i))
            else:
                return "-[:`{0}`]->".format(type_)
            #
        # build start clause from inputs
        for i, entry in enumerate(input_entries):
            start.append("in{0} = node:{1}(`{2}`={{val{0}}})".format(i, entry.index_name, entry.key))
            params["val{0}".format(i)] = entry.value
            set.append("SET in{0} = {{pa{0}}}".format(i))
            params["pa{0}".format(i)] = entry.node.properties
        for i, rel in enumerate(self._rels):
            # build and append pattern
            create.append(node_pattern(2 * i, rel.start_node.name) + \
                          rel_pattern(i, rel.type, rel.properties) + \
                          node_pattern(2 * i + 1, rel.end_node.name)
            )
        if start:
            query = "START {0}\n{1} {2}".format(
                ",\n      ".join(start),
                "CREATE UNIQUE" if unique else "CREATE",
                ",\n              ".join(create),
            )
        else:
            query = "CREATE {0}".format(
                ",\n              ".join(create),
            )
        if set:
            query += "".join("\n" + line for line in set)
        if output_names:
            query += "\nRETURN {0}".format(
                ",\n       ".join("out{0}".format(i) for i in range(len(output_names))),
            )
        return query, params, output_names

    def _execute_load_batch(self, graph_db, unique):
        # build batch request
        batch = neo4j.WriteBatch(graph_db)
        # 1. indexed nodes
        index_entries = list(self.index_entries.values())
        for entry in index_entries:
            batch.get_or_create_indexed_node(entry.index_name, entry.key, entry.value, entry.node.properties)
        # 2. related nodes
        if self._rels:
            query, params, related_names = self._get_relationship_query(unique)
            batch.append_cypher(query, params)
        else:
            related_names = []
        # 3. odd nodes
        odd_names = list(self._odd_nodes.keys())
        for name in odd_names:
            batch.create(self._nodes[name].properties)
        # submit batch unless empty (in which case bail out and return nothing)
        if batch:
            responses = batch.submit()
        else:
            return {}
        # parse response and build return value
        return_nodes = {}
        # 1. unique_nodes
        for i, entry in enumerate(index_entries):
            return_nodes[entry.node.name] = responses.pop(0)
        # 2. related nodes
        if self._rels:
            r = responses.pop(0)
            if r:
                for i, value in enumerate(r):
                    return_nodes[related_names[i]] = value
        # 3. odd nodes
        for i, name in enumerate(odd_names):
            return_nodes[name] = responses.pop(0)
        return return_nodes

    @deprecated("The geoff module is deprecated, "
                "use the load2neo server extension instead")
    def insert_into(self, graph_db):
        """ Insert subgraph into graph database using Cypher CREATE.
        """
        return self._execute_load_batch(graph_db, False)

    @deprecated("The geoff module is deprecated, "
                "use the load2neo server extension instead")
    def merge_into(self, graph_db):
        """ Merge subgraph into graph database using Cypher CREATE UNIQUE.
        """
        try:
            return self._execute_load_batch(graph_db, True)
        except neo4j.BatchError as err:
            if err.__class__.__name__ == "UniquePathNotUniqueException":
                err = ConstraintViolation(
                    "Unable to merge relationship onto multiple "
                    "existing relationships."
                )
            raise err


class _Parser(object):

    JSON_BOOLEAN = re.compile(r'(true|false)', re.IGNORECASE)
    JSON_NUMBER  = re.compile(r'(-?(0|[1-9]\d*)(\.\d+)?(e[+-]?\d+)?)', re.IGNORECASE)
    JSON_STRING  = re.compile(r'''(".*?(?<!\\)")''')
    NAME         = re.compile(r'(\w+)', re.UNICODE)
    WHITESPACE   = re.compile(r'(\s*)')

    def __init__(self, source):
        self.source = source       # original source data
        self.n = 0                 # pointer to next position to be parsed

    def _unexpected_character(self):
        next_char = self.peek()
        message = "Unexpected character {0} at position {1}".format(repr(next_char), self.n)
        return SyntaxError(message)

    def peek(self, length=1):
        return self.source[self.n:self.n + length]

    def parse(self):
        # FIRST PASS - work through source, extracting recognised elements
        self.n = 0
        elements = []   # temporary store for extracted elements
        self.parse_pattern(self.WHITESPACE)
        while self.n < len(self.source):
            element = self.parse_element()
            if isinstance(element, dict):
                if elements:
                    elements[-1].properties = element
                else:
                    raise TypeError("Property map cannot occur as first element.")
            elif isinstance(element, tuple):
                elements.extend(element)
            elif element is not None:
                elements.append(element)
            self.parse_pattern(self.WHITESPACE)
        # SECOND PASS - consolidate into collections of similar elements
        nodes, rels, index_entries = {}, [], {}
        def set_node(name, node):
            if name is None:
                nodes[uuid4()] = node
            elif name in nodes:
                nodes[name].properties.update(node.properties)
            else:
                nodes[name] = node
        for element in elements:
            if isinstance(element, AbstractNode):
                set_node(element.name, element)
            elif isinstance(element, AbstractRelationship):
                set_node(element.start_node.name, element.start_node)
                set_node(element.end_node.name, element.end_node)
                element.start_node = nodes[element.start_node.name]
                element.end_node = nodes[element.end_node.name]
                rels.append(element)
            elif isinstance(element, AbstractIndexEntry):
                set_node(element.node.name, element.node)
                element.node = nodes[element.node.name]
                key = (element.index_name, element.key, element.value, element.node.name)
                index_entries[key] = element
            else:
                raise TypeError("Unexpected element type '{0}'".format(element.__class__.__name__))
        return nodes, rels, index_entries

    def parse_array(self):
        items = []
        self.parse_literal("[")
        self.parse_pattern(self.WHITESPACE)
        next_char = self.peek()
        if next_char != "]":
            if next_char == '"':
                value_pattern = self.JSON_STRING
            elif next_char in "-0123456789":
                value_pattern = self.JSON_NUMBER
            elif next_char in "tf":
                value_pattern = self.JSON_BOOLEAN
            else:
                raise self._unexpected_character()
            items.append(self.parse_pattern(value_pattern, json.loads))
            self.parse_pattern(self.WHITESPACE)
            while self.peek() == ",":
                self.parse_literal(",")
                self.parse_pattern(self.WHITESPACE)
                items.append(self.parse_pattern(value_pattern, json.loads))
                self.parse_pattern(self.WHITESPACE)
        self.parse_literal("]")
        return items

    def parse_comment(self):
        self.parse_literal("/*")
        m = self.n
        while self.n < len(self.source) and self.peek(2) != "*/":
            self.n += 1
        comment = self.source[m:self.n]
        self.n += 2
        return comment

    def parse_element(self):
        element = None
        next_char = self.peek()
        if next_char == "(":
            node = self.parse_node()
            if self.peek(2) == "<=":
                # index entry
                self.parse_literal("<=")
                index_name, key, value = self.parse_index_point()
                element = AbstractIndexEntry(index_name, key, value, node)
            else:
                # path
                rels = []
                while self.n < len(self.source) and not self.parse_pattern(self.WHITESPACE):
                    next_char = self.peek()
                    if next_char == "-":
                        rel = self.parse_forward_path(node)
                        node = rel.end_node
                        rels.append(rel)
                    elif next_char == "<":
                        rel = self.parse_reverse_path(node)
                        node = rel.start_node
                        rels.append(rel)
                    else:
                        raise self._unexpected_character()
                if rels:
                    element = tuple(rels)
                else:
                    element = node
        elif next_char == "|":
            index_name, key, value = self.parse_index_point()
            self.parse_literal("=>")
            node = self.parse_node()
            element = AbstractIndexEntry(index_name, key, value, node)
        elif next_char == "/":
            self.parse_comment()
        elif next_char == "{":
            element = self.parse_property_map()
        else:
            raise self._unexpected_character()
        return element

    def parse_forward_path(self, start_node):
        self.parse_literal("-")
        rel = self.parse_relationship(start_node=start_node)
        self.parse_literal("->")
        rel.start_node = start_node
        rel.end_node = self.parse_node()
        return rel

    def parse_index_point(self):
        self.parse_literal("|")
        self.parse_pattern(self.WHITESPACE)
        index_name = self.parse_name()
        self.parse_pattern(self.WHITESPACE)
        next_char = self.peek()
        if next_char == "{":
            key, value = self.parse_property_pair()
            self.parse_pattern(self.WHITESPACE)
            self.parse_literal("|")
        elif next_char == "|":
            self.parse_literal("|")
            self.parse_pattern(self.WHITESPACE)
            key, value = self.parse_property_pair()
        else:
            raise self._unexpected_character()
        return index_name, key, value

    def parse_key_value_pair(self):
        key = self.parse_name()
        self.parse_pattern(self.WHITESPACE)
        self.parse_literal(":")
        self.parse_pattern(self.WHITESPACE)
        value = self.parse_value()
        return key, value

    def parse_literal(self, literal):
        len_literal = len(literal)
        test = self.source[self.n:self.n + len_literal]
        if test == literal:
            self.n += len_literal
            return literal
        else:
            raise self._unexpected_character()

    def parse_name(self):
        if self.peek() == "\"":
            return self.parse_pattern(self.JSON_STRING, json.loads)
        else:
            return self.parse_pattern(self.NAME)

    def parse_node(self):
        self.parse_literal("(")
        self.parse_pattern(self.WHITESPACE)
        next_char = self.peek()
        if next_char == ")":
            node = AbstractNode(None, None)
        elif next_char == "{":
            node = AbstractNode(None, self.parse_property_map())
        else:
            name = self.parse_name()
            if not self.parse_pattern(self.WHITESPACE):
                node = AbstractNode(name, None)
            else:
                node = AbstractNode(name, self.parse_property_map())
        self.parse_pattern(self.WHITESPACE)
        self.parse_literal(")")
        return node

    def parse_pattern(self, pattern, decoder=None):
        m = pattern.match(self.source, self.n)
        if m:
            self.n += len(m.group(0))
            value= m.group(0)
        else:
            raise self._unexpected_character()
        if decoder:
            value = decoder(value)
        return value

    def parse_property_map(self):
        properties = []
        self.parse_literal("{")
        self.parse_pattern(self.WHITESPACE)
        if self.peek() != "}":
            properties.append(self.parse_key_value_pair())
            self.parse_pattern(self.WHITESPACE)
            while self.peek() == ",":
                self.parse_literal(",")
                self.parse_pattern(self.WHITESPACE)
                properties.append(self.parse_key_value_pair())
                self.parse_pattern(self.WHITESPACE)
        self.parse_literal("}")
        return dict(properties)

    def parse_property_pair(self):
        self.parse_literal("{")
        self.parse_pattern(self.WHITESPACE)
        key, value = self.parse_key_value_pair()
        self.parse_pattern(self.WHITESPACE)
        self.parse_literal("}")
        return key, value

    def parse_relationship(self, start_node=None, end_node=None):
        self.parse_literal("[")
        self.parse_pattern(self.WHITESPACE)
        next_char = self.peek()
        if next_char != ":":
            # read and ignore relationship name, if present
            self.parse_name()
            self.parse_pattern(self.WHITESPACE)
        self.parse_literal(":")
        type = self.parse_name()
        self.parse_pattern(self.WHITESPACE)
        next_char = self.peek()
        if next_char == "{":
            rel = AbstractRelationship(start_node, type, self.parse_property_map(), end_node)
            self.parse_pattern(self.WHITESPACE)
        else:
            rel = AbstractRelationship(start_node, type, None, end_node)
        self.parse_literal("]")
        return rel

    def parse_reverse_path(self, end_node):
        self.parse_literal("<-")
        rel = self.parse_relationship(end_node=end_node)
        self.parse_literal("-")
        rel.start_node = self.parse_node()
        rel.end_node = end_node
        return rel

    def parse_value(self):
        next_char = self.peek()
        if next_char == "[":
            value = self.parse_array()
        elif next_char == '"':
            value = self.parse_pattern(self.JSON_STRING, json.loads)
        elif next_char in "-0123456789":
            value = self.parse_pattern(self.JSON_NUMBER, json.loads)
        elif next_char == "t":
            self.parse_literal("true")
            value = True
        elif next_char == "f":
            self.parse_literal("false")
            value = False
        elif next_char == "n":
            self.parse_literal("null")
            value = None
        else:
            raise self._unexpected_character()
        return value


class AbstractNode(object):

    def __init__(self, name, properties=None):
        self.name = name
        self.properties = properties or {}

    def __eq__(self, other):
        return self.name == other.name and self.properties == other.properties

    def __ne__(self, other):
        return self.name != other.name or self.properties != other.properties

    def __repr__(self):
        if self.properties:
            return "{0}({1}, {2})".format(self.__class__.__name__, repr(self.name), repr(self.properties))
        else:
            return "{0}({1})".format(self.__class__.__name__, repr(self.name))

    def __str__(self):
        if self.properties:
            return "({0} {1})".format(self.name, json.dumps(self.properties, separators=(",", ":")))
        else:
            return "({0})".format(self.name)


class AbstractRelationship(object):

    def __init__(self, start_node, type, properties, end_node):
        self.start_node = start_node
        self.type = type
        self.properties = properties or {}
        self.end_node = end_node

    def __eq__(self, other):
        return self.start_node == other.start_node and \
               self.type == other.type and \
               self.properties == other.properties and \
               self.end_node == other.end_node

    def __ne__(self, other):
        return self.start_node != other.start_node or \
               self.type != other.type or \
               self.properties != other.properties or \
               self.end_node != other.end_node

    def __str__(self):
        if self.properties:
            return "{0}-[:{1} {2}]->{3}".format(self.start_node, self.type, json.dumps(self.properties, separators=(",", ":")), self.end_node)
        else:
            return "{0}-[:{1}]->{2}".format(self.start_node, self.type, self.end_node)


class AbstractIndexEntry(object):

    def __init__(self, index_name, key, value, node):
        self.index_name = index_name
        self.key = key
        self.value = value
        self.node = node

    def __eq__(self, other):
        return self.index_name == other.index_name and \
               self.key == other.key and \
               self.value == other.value and \
               self.node == other.node

    def __ne__(self, other):
        return self.index_name != other.index_name or \
               self.key != other.key or \
               self.value != other.value or \
               self.node != other.node

    def __str__(self):
        return "|{0} {1}|=>{2}".format(self.index_name, json.dumps({self.key: self.value}, separators=(",", ":")), self.node)


def insert(graph_db, file):
    """ Insert Geoff data into a graph database.
    """
    Subgraph.load(file).insert_into(graph_db)


def merge(graph_db, file):
    """ Merge Geoff data into a graph database.
    """
    Subgraph.load(file).merge_into(graph_db)


def insert_xml(graph_db, file):
    """ Insert XML data into a graph database.
    """
    Subgraph.load_xml(file).insert_into(graph_db)


def merge_xml(graph_db, file):
    """ Merge XML data into a graph database.
    """
    Subgraph.load_xml(file).merge_into(graph_db)
