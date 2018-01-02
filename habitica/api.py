#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Phil Adams http://philadams.net

Python wrapper around the Habitica (http://habitica.com) API
http://github.com/philadams/habitica
"""


import json

import requests

API_URI_BASE = 'api/v3'
API_CONTENT_TYPE = 'application/json'


class Habitica(object):
    """
    A minimalist Habitica API class.
    """

    def __init__(self, auth=None, resource=None, aspect=None):
        self.auth = auth
        self.resource = resource
        self.aspect = aspect
        self.headers = auth if auth else {}
        self.headers.update({'content-type': API_CONTENT_TYPE})

    def __getattr__(self, m):
        try:
            return object.__getattr__(self, m)
        except AttributeError:
            if not self.resource:
                return Habitica(auth=self.auth, resource=m)
            else:
                return Habitica(auth=self.auth, resource=self.resource,
                                aspect=m)

    def __call__(self, **kwargs):
        """
        Send a Habitica API call.

        Args:
            **kwargs: keyword argument dictionary
                Specifies the nature of the API call.

                Most of these are JSON key-value pairs, e.g. a request to
                'Update a task' should include a key-value pair that specifies
                the new name of the task such as {'text': 'Do the dishes'}.
                See Habitica's API documentation for more details.

                Some key-value pairs are special, and have meaning only when
                calling this function. These include:

                '_method':      the method of the HTTP request. Valid values
                                include 'get', 'put', 'post', and 'delete'. If
                                not specified, assumed to be 'get'.
                '_direction':   when "scoring" a task, this is the direction
                                in which to score. Valid values include 'up'
                                and 'down'. Specifying a '_direction' results
                                in undefined behavior when not scoring a task.
                '_position':    when moving a task within its task list, this
                                is the position to which the task should be
                                moved. See 'Move a task to a new position' in
                                the Habitica APIv3 documentation.
        """
        uri = self.__buildURI(**kwargs)

        # actually make the request of the API
        method = kwargs.pop('_method', 'get')
        if method in ['put', 'post', 'delete']:
            res = getattr(requests, method)(uri, headers=self.headers,
                                            data=json.dumps(kwargs))
        else:
            res = getattr(requests, method)(uri, headers=self.headers,
                                            params=kwargs)

        if res.status_code == requests.codes.ok:
            return res.json()["data"]
        else:
            res.raise_for_status()

    def __buildURI(self, **kwargs):
        """
        Construct and return the URI needed for the API call.
        """
        def resourceAccessURI(uri, resource):
            """
            Concatenate the fields needed to access a resource.

            # uri = 'https://habitica.com/api/v3', resource = 'tags'
            getResource(uri)  # returns 'https://habitica.com/api/v3/tags'
            """
            # e.g., https://habitica.com/api/v3/groups
            return uri + '/' + resource

        def aspectAccessURI(uri, resource, aspect):
            """
            Concatenate the fields needed to access a resource aspect.
            """
            if self.aspect == 'tasks':
                # e.g., https://habitica.com/api/v3/tasks/user
                uri = '%s/%s/%s' % (uri,
                                    aspect,
                                    resource)
            elif self.aspect == 'tags':
                # e.g., https://habitica.com/api/v3/tags
                uri = '%s/%s' % (uri,
                                 self.aspect)
            else:
                uri = '%s/%s/%s' % (uri,
                                    resource,
                                    aspect)
            return uri

        def aspectIDAccessURI(uri, aspect, aspect_id):
            """
            Concatenate the fields needed to access a ID-ed resource aspect.
            """
            uri = '%s/%s/%s' % (uri,
                                aspect,
                                str(aspect_id))
            if self.aspect == 'tasks':
                if '_direction' in kwargs:
                    # "Score" a task, i.e. complete a todo or a daily,
                    # or +/- a habit.
                    # https://habitica.com/api/v3/tasks/:taskID/score/[up/down]
                    uri = '%s/score/%s' % (uri, kwargs.pop('_direction'))
                elif '_position' in kwargs:
                    # Move a task to a new position in the list.
                    # https://habitica.com/api/v3/tasks/:taskID/move/to/[pos]
                    uri = '%s/move/to/%s' % (uri, kwargs.pop('_position'))
            return uri

        # https://habitica.com/api/v3
        uri = '%s/%s' % (self.auth['url'],
                         API_URI_BASE)

        if self.aspect:
            # Are we given the ID of a specific aspect?
            aspect_id = kwargs.pop('_id', None)
            if aspect_id is None:
                aspect_id = kwargs.pop('id', None)

            if aspect_id is not None:
                # Return an ID for specific access to the ID-ed aspect.
                return aspectIDAccessURI(uri, self.aspect, aspect_id)

            # Return a URI for broadly accessing a resource aspect.
            return aspectAccessURI(uri, self.resource, self.aspect)

        return resourceAccessURI(uri, self.resource)
