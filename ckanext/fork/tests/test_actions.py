import pytest
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories, helpers


@pytest.fixture(scope="class")
def datasets(reset_db, reset_index):
    """
    Creates 3 datasets each with three resources. Both
    datasets and resources are numbered uniquely and
    incrementally.

    Test Dataset 01 contains:
        Test Resource 00, Test Resource 01, Test Resource 02
    Test Dataset 02 contains:
        Test Resource 03, Test Resource 04, Test Resource 05
    Test Dataset 03 contains:
        Test Resource 06, Test Resource 07, Test Resource 08

    """
    reset_db()
    reset_index()
    organization = factories.Organization()
    datasets = [factories.Dataset(
        title=f"Test Dataset {i:02d}",
        name=f"test-dataset-{i:02d}",
        owner_org=organization['id']
    ) for i in range(3)]
    for (d, dataset) in enumerate(datasets):
        dataset["resources"] = [factories.Resource(
            name=f"Test Resource {(d*3)+r:02d}",
            package_id=dataset['id']
        ) for r in range(3)]
    return datasets


@pytest.mark.usefixtures('with_request_context')
class TestResourceAutocomplete():

    def test_resource_autocomplete_raises_error_if_no_query(self):
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action('resource_autocomplete')

    @pytest.mark.parametrize("q,result_names", [
        ('02', ['test-dataset-02', 'test-dataset-00']),
        ('00', ['test-dataset-00', 'test-dataset-02', 'test-dataset-01']),
        ('01', ['test-dataset-01', 'test-dataset-00']),
        ('Resource 01', ['test-dataset-01', 'test-dataset-00']),
    ])
    def test_resource_autocomplete(self, q, result_names, datasets):
        result = helpers.call_action('resource_autocomplete', q=q)
        assert result_names == [d['name'] for d in result]

    def test_resource_autocomplete_output_format(self, datasets):
        result = helpers.call_action('resource_autocomplete', q="Test Resource 08")
        assert type(result) == list
        for dataset in result:
            assert set(dataset.keys()) == {
                'id',
                'name',
                'title',
                'owner_org',
                'match',
                'resources'
            }
            for resource in dataset['resources']:
                assert set(resource.keys()) == {
                    'id',
                    'name',
                    'match',
                    'last_modified'
                }


@pytest.mark.usefixtures('clean_db')
class TestPackageShow():

    def test_forked_resource_display(self):
        giftless_metadata = {
            "sha256": "dummysha",
            "size": 999,
            "lfs_prefix": "test/resource",
            "url_type": "upload"
        }
        forked_dataset = factories.Dataset()
        forked_resource = factories.Resource(
            package_id=forked_dataset['id'],
            **giftless_metadata
        )
        helpers.call_action('package_patch', id=forked_dataset['id'], notes='An activity')
        forked_activity_id = helpers.call_action(
            'package_activity_list',
            id=forked_dataset['id']
        )[0]['id']
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork=forked_resource['id']
        )
        response = helpers.call_action('resource_show', id=resource['id'])
        assert response['forked_resource'] == {
            'resource_id': forked_resource['id'],
            'resource_name': forked_resource['name'],
            'dataset_id': forked_dataset['id'],
            'dataset_title': forked_dataset['title'],
            'activity_id': forked_activity_id,
            'synced': True
        }

    def test_unsynced_fork(self):
        giftless_metadata = {
            "sha256": "dummysha",
            "size": 999,
            "lfs_prefix": "test/resource",
            "url_type": "upload"
        }
        forked_dataset = factories.Dataset()
        forked_resource = factories.Resource(
            package_id=forked_dataset['id'],
            **giftless_metadata
        )
        helpers.call_action('package_patch', id=forked_dataset['id'], notes='An activity')
        forked_activity_id = helpers.call_action(
            'package_activity_list',
            id=forked_dataset['id']
        )[0]['id']
        result = helpers.call_action('resource_patch', id=forked_resource['id'], sha256='newsha')
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork=f"{forked_resource['id']}@{forked_activity_id}"
        )
        response = helpers.call_action('resource_show', id=resource['id'])
        assert not response['forked_resource']['synced']


@pytest.mark.usefixtures('clean_db')
class TestPackageCreate():

    def test_resource_create_with_no_activity_id(self):
        giftless_metadata = {
            "sha256": "dummysha",
            "size": 999,
            "lfs_prefix": "test/resource",
            "url_type": "upload"
        }
        forked_dataset = factories.Dataset()
        forked_resource = factories.Resource(
            package_id=forked_dataset['id'],
            **giftless_metadata
        )
        helpers.call_action('package_patch', id=forked_dataset['id'], notes='An activity')
        forked_activity_id = helpers.call_action(
            'package_activity_list',
            id=forked_dataset['id']
        )[0]['id']
        dataset = factories.Dataset()
        resource = helpers.call_action(
            "resource_create",
            package_id=dataset['id'],
            fork=forked_resource['id']
        )
        assert resource['fork'] == f"{forked_resource['id']}@{forked_activity_id}"
        assert resource['sha256'] == giftless_metadata['sha256']
        assert resource['size'] == giftless_metadata['size']
        assert resource['lfs_prefix'] == giftless_metadata['lfs_prefix']
        assert resource['url_type'] == giftless_metadata['url_type']

    def test_resource_create_with_activity_id(self):
        giftless_metadata = {
            "sha256": "dummysha",
            "size": 999,
            "lfs_prefix": "test/resource",
            "url_type": "upload"
        }
        forked_dataset = factories.Dataset()
        forked_resource = factories.Resource(
            package_id=forked_dataset['id'],
            **giftless_metadata
        )
        helpers.call_action('package_patch', id=forked_dataset['id'], notes='An activity')
        forked_activity_id = helpers.call_action(
            'package_activity_list',
            id=forked_dataset['id']
        )[0]['id']
        helpers.call_action('resource_patch', id=forked_resource['id'], sha256='newsha')
        dataset = factories.Dataset()
        resource = helpers.call_action(
            "resource_create",
            {'ignore_auth': True, 'user': 'dummyuser'},
            package_id=dataset['id'],
            fork=f"{forked_resource['id']}@{forked_activity_id}"
        )

        assert resource['fork'] == f"{forked_resource['id']}@{forked_activity_id}"
        assert resource['sha256'] == giftless_metadata['sha256']
        assert resource['size'] == giftless_metadata['size']
        assert resource['lfs_prefix'] == giftless_metadata['lfs_prefix']
        assert resource['url_type'] == giftless_metadata['url_type']
