import json
import unittest
import os
from unittest import mock

from backports.tempfile import TemporaryDirectory
from nose.tools import assert_true, assert_false, assert_equal, assert_is_not_none

from localstack.utils import persistence


class TestPersistence(unittest.TestCase):
    temp_dir = None

    # just in case tests run in parallel, we want to only
    # create the temp_dir once
    @classmethod
    def setup_class(cls):
        cls.temp_dir = TemporaryDirectory()
        #persistence.DATA_DIR = cls.temp_dir.name

    @classmethod
    def teardown_class(cls):
        cls.temp_dir.cleanup()
        #persistence.DATA_DIR = None

    def test_should_record(self):
        assert_true(persistence.should_record('s3', 'PUT', None, None, None))
        assert_true(persistence.should_record('s3', 'POST', None, None, None))
        assert_true(persistence.should_record('s3', 'DELETE', None, None, None))

        assert_false(persistence.should_record('s3', 'GET', None, None, None))
        assert_false(persistence.should_record('s3', 'FAKE_METHOD', None, None, None))
        assert_false(persistence.should_record('not_s3', 'PUT', None, None, None))
        assert_false(persistence.should_record(None, None, None, None, None))

    def test_record(self):
        with mock.patch('localstack.utils.persistence.DATA_DIR', self.temp_dir.name):
            # verify mock worked
            assert_is_not_none(persistence.DATA_DIR)
            assert_equal(persistence.DATA_DIR, self.temp_dir.name)

            persistence.record(
                's3', 'POST', 'path',
                {'data': 'data_val'},
                {'header1': 'header_val'},
            )
            assert_equal(os.listdir(self.temp_dir.name), ['s3_api_calls.json'])
            s3_filepath = os.path.join(self.temp_dir.name, 's3_api_calls.json')

            # make sure we wrote the JSON we expect to the file
            with open(s3_filepath, 'r') as s3_file:
                j = json.load(s3_file)
                print(j)
                assert_equal(j['m'], 'POST')
                assert_equal(j['a'], 's3')
                assert_equal(j['h'], {'header1': 'header_val'})
                assert_equal(j['p'], 'path')

    def test_get_file_path(self):
        with mock.patch('localstack.utils.persistence.DATA_DIR', self.temp_dir.name):
            # verify mock worked
            assert_is_not_none(persistence.DATA_DIR)
            assert_equal(persistence.DATA_DIR, self.temp_dir.name)

            assert_equal(
                persistence.get_file_path('s3', create=True),
                persistence.DATA_DIR + '/s3_api_calls.json'
            )

            assert_false(
                persistence.get_file_path('invalid_api', create=False)
            )
