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

""" The ogm module provides Object to Graph Mapping features similar to ORM
facilities available for relational databases. All functionality is available
through the :py:class:`Store` class which is bound to a specific
:py:class:`neo4j.GraphDatabaseService` instance on creation.

Conceptually, a mapped object "owns" a single node within the graph along with
all of that node's outgoing relationships. These features are managed via a
pair of attributes called `__node__` and `__rel__` which store details of the
mapped node and the outgoing relationships respectively. The only specific
requirement for a mapped object is that it has a nullary constructor which can
be used to create new instances.

The `__node__` attribute holds a :py:class:`neo4j.Node` object which is the
node to which this object is mapped. If the attribute does not exist, or is
:py:const:`None`, the object is considered "unsaved".

The `__rel__` attribute holds a dictionary of outgoing relationship details.
Each key corresponds to a relationship type and each value to a list of
2-tuples representing the outgoing relationships of that type. Within each
2-tuple, the first value holds a dictionary of relationship properties (which
may be empty) and the second value holds the endpoint. The endpoint may be
either a :py:class:`neo4j.Node` instance or another mapped object. Any such
objects which are unsaved will be lazily saved as required by creation of the
relationship itself. The following data structure outline shows an example of
a `__rel__` attribute (where `alice` and `bob` represent other mapped objects::

    {
        "LIKES": [
            ({}, alice),
            ({"since": 1999}, bob)
        ]
    }

To manage relationships, use the :py:func:`Store.relate` and
:py:func:`Store.separate` methods. Neither method makes any calls to the
database and operates only on the local `__rel__` attribute. Changes must be
explicitly saved via one of the available save methods. The
:py:func:`Store.load_related` method loads all objects marked as related by
the `__rel__` attribute.

The code below shows an example of usage::

    from py2neo import neo4j, ogm

    class Person(object):

        def __init__(self, email=None, name=None, age=None):
            self.email = email
            self.name = name
            self.age = age

        def __str__(self):
            return self.name

    graph_db = neo4j.GraphDatabaseService()
    store = ogm.Store(graph_db)

    alice = Person("alice@example.com", "Alice", 34)
    store.save_unique("People", "email", alice.email, alice)

    bob = Person("bob@example.org", "Bob", 66)
    carol = Person("carol@example.net", "Carol", 42)
    store.relate(alice, "LIKES", bob)     # these relationships are not saved
    store.relate(alice, "LIKES", carol)   # until `alice` is saved
    store.save(alice)

    friends = store.load_related(alice, "LIKES", Person)
    print("Alice likes {0}".format(" and ".join(str(f) for f in friends)))

"""


from __future__ import unicode_literals

from . import neo4j


class NotSaved(ValueError):
    """ Raised when an object has not been saved but a bound node is required.
    """
    pass


class Store(object):

    def __init__(self, graph_db):
        self.graph_db = graph_db
        if self.graph_db.supports_optional_match:
            self.__delete_query = ("START a=node({A}) "
                                   "OPTIONAL MATCH a-[r]-b "
                                   "DELETE r, a")
        else:
            self.__delete_query = ("START a=node({A}) "
                                   "MATCH a-[r?]-b "
                                   "DELETE r, a")

    def _assert_saved(self, subj):
        try:
            node = subj.__node__
            if node is None:
                raise NotSaved(subj)
        except AttributeError:
            raise NotSaved(subj)

    def _get_node(self, endpoint):
        if isinstance(endpoint, neo4j.Node):
            return endpoint
        if not hasattr(endpoint, "__node__"):
            self.save(endpoint)
        return endpoint.__node__

    def _is_same(self, obj, endpoint):
        if isinstance(endpoint, neo4j.Node):
            if hasattr(obj, "__node__"):
                return endpoint == obj.__node__
            else:
                return False
        else:
            return endpoint is obj

    def is_saved(self, subj):
        """ Return :py:const:`True` if the object `subj` has been saved to
        the database, :py:const:`False` otherwise.

        :param subj: the object to test
        """
        return hasattr(subj, "__node__") and subj.__node__ is not None

    def relate(self, subj, rel_type, obj, properties=None):
        """ Define a relationship between `subj` and `obj` of type `rel_type`.
        This is a local operation only: nothing is saved to the database until
        a save method is called. Relationship properties may optionally be
        specified.

        :param subj: the object bound to the start of the relationship
        :param rel_type: the relationship type
        :param obj: the object bound to the end of the relationship
        :param properties: properties attached to the relationship (optional)
        """
        if not hasattr(subj, "__rel__"):
            subj.__rel__ = {}
        if rel_type not in subj.__rel__:
            subj.__rel__[rel_type] = []
        subj.__rel__[rel_type].append((properties or {}, obj))

    def separate(self, subj, rel_type, obj=None):
        """ Remove any relationship definitions which match the criteria
        specified. This is a local operation only: nothing is saved to the
        database until a save method is called. If no object is specified, all
        relationships of type `rel_type` are removed.

        :param subj: the object bound to the start of the relationship
        :param rel_type: the relationship type
        :param obj: the object bound to the end of the relationship (optional)
        """
        if not hasattr(subj, "__rel__"):
            return
        if rel_type not in subj.__rel__:
            return
        if obj is None:
            del subj.__rel__[rel_type]
        else:
            subj.__rel__[rel_type] = [
                (props, endpoint)
                for props, endpoint in subj.__rel__[rel_type]
                if not self._is_same(obj, endpoint)
            ]

    def load_related(self, subj, rel_type, cls):
        """ Load all nodes related to `subj` by a relationship of type
        `rel_type` into objects of type `cls`.

        :param subj: the object bound to the start of the relationship
        :param rel_type: the relationship type
        :param cls: the class to load all related objects into
        :return: list of `cls` instances
        """
        if not hasattr(subj, "__rel__"):
            return []
        if rel_type not in subj.__rel__:
            return []
        return [
            self.load(cls, self._get_node(endpoint))
            for rel_props, endpoint in subj.__rel__[rel_type]
        ]

    def load(self, cls, node):
        """ Load and return an object of type `cls` from database node `node`.

        :param cls: the class of the object to be returned
        :param node: the node from which to load object data
        :return: a `cls` instance
        """
        subj = cls()
        setattr(subj, "__node__", node)
        self.reload(subj)
        return subj

    def load_indexed(self, index_name, key, value, cls):
        """ Load zero or more indexed nodes from the database into a list of
        objects.

        :param index_name: the node index name
        :param key: the index key
        :param value: the index value
        :param cls: the class of the object to be returned
        :return: a list of `cls` instances
        """
        index = self.graph_db.get_index(neo4j.Node, index_name)
        nodes = index.get(key, value)
        return [self.load(cls, node) for node in nodes]

    def load_unique(self, index_name, key, value, cls):
        """ Load a uniquely indexed node from the database into an object.

        :param index_name: the node index name
        :param key: the index key
        :param value: the index value
        :param cls: the class of the object to be returned
        :return: as instance of `cls` containing the loaded data
        """
        index = self.graph_db.get_index(neo4j.Node, index_name)
        nodes = index.get(key, value)
        if not nodes:
            return None
        if len(nodes) > 1:
            raise LookupError("Multiple nodes match the given criteria; "
                              "consider using `load_all` instead.")
        return self.load(cls, nodes[0])

    def reload(self, subj):
        """ Reload properties and relationships from a database node into
        `subj`.

        :param subj: the object to reload
        :raise NotSaved: if `subj` is not linked to a database node
        """
        self._assert_saved(subj)
        # naively copy properties from node to object
        properties = subj.__node__.get_properties()
        for key in subj.__dict__:
            if not key.startswith("_") and key not in properties:
                setattr(subj, key, None)
        for key, value in properties.items():
            if not key.startswith("_"):
                setattr(subj, key, value)
        subj.__rel__ = {}
        for rel in subj.__node__.match():
            if rel.type not in subj.__rel__:
                subj.__rel__[rel.type] = []
            subj.__rel__[rel.type].append((rel.get_properties(), rel.end_node))

    def save(self, subj, node=None):
        """ Save an object to a database node.

        :param subj: the object to save
        :param node: the database node to save to (if omitted, will re-save to
            same node as previous save)
        """
        if node is not None:
            subj.__node__ = node
        # naively copy properties from object to node
        props = {}
        for key, value in subj.__dict__.items():
            if not key.startswith("_"):
                props[key] = value
        if hasattr(subj, "__node__"):
            subj.__node__.set_properties(props)
            query = neo4j.CypherQuery(self.graph_db, "START a=node({A}) "
                                                     "MATCH (a)-[r]->(b) "
                                                     "DELETE r")
            query.execute(A=subj.__node__._id)
        else:
            subj.__node__, = self.graph_db.create(props)
        # write rels
        if hasattr(subj, "__rel__"):
            batch = neo4j.WriteBatch(self.graph_db)
            for rel_type, rels in subj.__rel__.items():
                for rel_props, endpoint in rels:
                    end_node = self._get_node(endpoint)
                    if not neo4j.familiar(end_node, self.graph_db):
                        raise ValueError(end_node)
                    batch.create((subj.__node__, rel_type, end_node, rel_props))
            batch.run()
        return subj

    def save_indexed(self, index_name, key, value, *subj):
        """ Save one or more objects to the database, indexed under the
        supplied criteria.

        :param index_name: the node index name
        :param key: the index key
        :param value: the index value
        :param subj: one or more objects to save
        """
        index = self.graph_db.get_or_create_index(neo4j.Node, index_name)
        for subj in subj:
            index.add(key, value, self.save(self._get_node(subj)))

    def save_unique(self, index_name, key, value, subj):
        """ Save an object to the database, uniquely indexed under the
        supplied criteria.

        :param index_name: the node index name
        :param key: the index key
        :param value: the index value
        :param subj: the object to save
        """
        index = self.graph_db.get_or_create_index(neo4j.Node, index_name)
        node = index.get_or_create(key, value, {})
        self.save(subj, node)

    def delete(self, subj):
        """ Delete a saved object node from the database as well as all
        incoming and outgoing relationships.

        :param subj: the object to delete from the database
        :raise NotSaved: if `subj` is not linked to a database node
        """
        self._assert_saved(subj)
        node = subj.__node__
        del subj.__node__
        neo4j.CypherQuery(self.graph_db,
                          self.__delete_query).execute(A=node._id)
