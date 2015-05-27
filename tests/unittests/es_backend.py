# coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.test import SimpleTestCase
from django.conf import settings
from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend
from haystack.management.commands.update_index import do_update
from multilingual.elasticsearch_backend import ElasticsearchMultilingualSearchBackend, \
    ElasticsearchMultilingualSearchEngine
from .mocks import mock_indices, Data
from testproject.models import Document
from multilingual.utils import get_analyzer_for

try:
    from unittest import mock  # python >= 3.3
except ImportError:
    import mock  # python 2





@mock.patch('elasticsearch.Elasticsearch')
class MockingTest(SimpleTestCase):
    fixtures = ['small']
    maxDiff = None

    def test_mocking_works(self, mock_obj):
        # create a backend instance
        es = ElasticsearchMultilingualSearchBackend('default', **Data.connection_options)
        for language in settings.LANGUAGES:
            self.assertIn(language[0], es.existing_mapping.keys())
        # in the constructor, an Elasticsearche instance is created as 'conn' property.
        self.assertTrue(isinstance(es.conn, mock.Mock))
        self.assertIsNot(es.conn, mock_obj)  # a new mock is created.
        indices = mock_indices()  # use the indices mock from the mocks module.
        es.conn.attach_mock(indices, 'indices')
        self.assertEqual(es.conn.indices.get_mapping(), Data.existing_mapping)
        es.setup()
        # Data.connection_options.INDEX_NAME
        indices.get_mapping.assert_any_call(index='testproject-en')
        indices.get_mapping.assert_any_call(index='testproject-de')
        indices.get_mapping.assert_any_call(index='testproject-ru')

    def test_do_update(self, mock_obj):
        """
        Tests the update_index.do_update function
        """
        engine = ElasticsearchMultilingualSearchEngine()
        backend = mock.Mock()
        engine.backend = backend
        index = engine.get_unified_index()
        qs = Document.objects.all()
        start = 0
        end = len(qs)
        total = end - start
        do_update(backend, index, qs, start, end, total, verbosity=1, commit=False)
        # The update method has been called
        self.assertTrue(backend.update.called)
        call_args_list = backend.update.call_args_list
        # args, the queryset cannot be testet for equality.
        self.assertEqual(call_args_list[0][0][0], index)
        # kwargs
        self.assertEqual(call_args_list[0][1], {'commit': False})

    def test_setup_on_haystack_backend(self, mock_obj):
        """
        Tests the Setup method on the elasticsearch backend.
        """
        es = ElasticsearchSearchBackend('default', **Data.connection_options)
        self.assertFalse(es.setup_complete)
        es.setup()
        self.assertTrue(es.setup_complete)
        self.assertEqual(es.existing_mapping, Data.existing_mapping)
        es.conn.indices.create.assert_called_with(index='testproject',
                                                  ignore=400, body=es.DEFAULT_SETTINGS)
        es.conn.indices.put_mapping.assert_called_with(index='testproject',
                                                       doc_type='modelresult',
                                                       body=Data.existing_mapping)

    def test_setup_on_multilingual_backend(self, mock_obj):
        """
        Tests the Setup method on the elasticsearch backend.
        """
        es = ElasticsearchMultilingualSearchBackend('default', **Data.connection_options)
        self.assertFalse(es.setup_complete)
        es.setup()
        self.assertTrue(es.setup_complete)
        self.assertNotEqual(es.existing_mapping['de'], Data.existing_mapping)
        self.assertEqual(es.existing_mapping['de']['modelresult']['properties']['text']['analyzer'],
                         get_analyzer_for('de'))
        es.conn.indices.create.assert_any_call(index='testproject-de',
                                               ignore=400, body=es.DEFAULT_SETTINGS)
        es.conn.indices.put_mapping.assert_any_call(index='testproject-de',
                                                    doc_type='modelresult',
                                                    body=es.existing_mapping['de'])

        self.assertNotEqual(es.existing_mapping['en'], Data.existing_mapping)
        self.assertEqual(es.existing_mapping['en']['modelresult']['properties']['text']['analyzer'],
                         get_analyzer_for('en'))
        es.conn.indices.create.assert_any_call(index='testproject-en',
                                               ignore=400, body=es.DEFAULT_SETTINGS)
        es.conn.indices.put_mapping.assert_any_call(index='testproject-en',
                                                    doc_type='modelresult',
                                                    body=es.existing_mapping['en'])

        self.assertNotEqual(es.existing_mapping['fr'], Data.existing_mapping)
        self.assertEqual(es.existing_mapping['fr']['modelresult']['properties']['text']['analyzer'],
                         get_analyzer_for('fr'))
        es.conn.indices.create.assert_any_call(index='testproject-fr',
                                               ignore=400, body=es.DEFAULT_SETTINGS)
        es.conn.indices.put_mapping.assert_any_call(index='testproject-fr',
                                                    doc_type='modelresult',
                                                    body=es.existing_mapping['fr'])

    def test_haystack_clear(self, mock_obj):
        es = ElasticsearchSearchBackend('default', **Data.connection_options)
        es.setup()
        es.clear(commit=True)  # commit is ignored anyway
        es.conn.indices.delete.assert_called_with(index='testproject', ignore=404)

    def test_multilingual_clear(self, mock_obj):
        es = ElasticsearchMultilingualSearchBackend('default', **Data.connection_options)
        es.setup()
        es.clear(commit=False)
        es.conn.indices.delete.assert_any_call(index='testproject-en', ignore=404)
        es.conn.indices.delete.assert_any_call(index='testproject-fr', ignore=404)
        es.conn.indices.delete.assert_any_call(index='testproject-de', ignore=404)
        es.conn.indices.delete.assert_any_call(index='testproject-ru', ignore=404)




