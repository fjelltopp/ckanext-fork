import pytest
from ckan.tests import factories
from ckanext.fork import helpers
from ckan.plugins import toolkit
import mock


@pytest.mark.usefixtures('clean_db', 'with_request_context')
class TestForkMetadata():

    def test_expected_behaviour(self, forked_data):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        toolkit.g.user = factories.User(sysadmin=True)['name']
        response = helpers.fork_metadata(resource)
        assert response == {
            'resource_id': forked_data['resource']['id'],
            'resource_name': forked_data['resource']['name'],
            'dataset_id': forked_data['dataset']['id'],
            'dataset_name': forked_data['dataset']['name'],
            'dataset_title': forked_data['dataset']['title'],
            'activity_id': forked_data['activity_id']
        }

    def test_returns_empty_dict_for_no_fork(self):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id']
        )
        response = helpers.fork_metadata(resource)
        assert response == {}

    @mock.patch('ckanext.fork.helpers.get_forked_data',
                side_effect=toolkit.NotAuthorized())
    def test_returns_empty_dict_for_unauthorized_fork(self, mocked_function, forked_data):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        response = helpers.fork_metadata(resource)
        assert response == {}
