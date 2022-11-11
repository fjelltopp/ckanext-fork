import pytest
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories
from ckan.tests.helpers import call_action


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
            call_action('resource_autocomplete')

    @pytest.mark.parametrize("q,result_names", [
        ('02', ['test-dataset-02', 'test-dataset-00']),
        ('00', ['test-dataset-00', 'test-dataset-02', 'test-dataset-01']),
        ('01', ['test-dataset-01', 'test-dataset-00']),
        ('Resource 01', ['test-dataset-01', 'test-dataset-00']),
    ])
    def test_resource_autocomplete(self, q, result_names, datasets):
        result = call_action('resource_autocomplete', q=q)
        assert result_names == [d['name'] for d in result]

    def test_resource_autocomplete_output_format(self, datasets):
        result = call_action('resource_autocomplete', q="Test Resource 08")
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
                    'format',
                    'filename',
                    'match',
                    'last_modified'
                }


@pytest.mark.usefixtures('clean_db')
class TestPackageShow():

    def test_synced_fork_display(self, forked_data):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        response = call_action('resource_show', id=resource['id'])
        assert response['fork_synced']

    def test_unsynced_fork(self, forked_data):
        call_action('resource_patch', id=forked_data['resource']['id'], sha256='newsha')
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id'],
            fork_activity=forked_data['activity_id']
        )
        response = call_action('resource_show', id=resource['id'])
        assert not response['fork_synced']


@pytest.mark.usefixtures('clean_db')
class TestPackageCreate():

    def test_resource_create_with_no_activity_id(self, forked_data):
        dataset = factories.Dataset()
        resource = call_action(
            "resource_create",
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        assert resource['fork_activity'] == forked_data['activity_id']

        for key in ['sha256', 'size', 'lfs_prefix', 'url_type']:
            assert resource[key] == forked_data['resource'][key]

    def test_resource_create_with_activity_id(self, forked_data):
        call_action('resource_patch', id=forked_data['resource']['id'], sha256='newsha')
        dataset = factories.Dataset()
        resource = call_action(
            "resource_create",
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id'],
            fork_activity=forked_data['activity_id']
        )

        for key in ['sha256', 'size', 'lfs_prefix', 'url_type']:
            assert resource[key] == forked_data['resource'][key]


@pytest.mark.usefixtures('clean_db')
class TestPackageUpdate():

    def test_resource_update_with_no_activity_id(self, forked_data):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        forked_data['resource'] = call_action(
            'resource_patch',
            id=forked_data['resource']['id'],
            sha256='newsha'
        )
        forked_data['activity_id'] = call_action(
            'package_activity_list',
            id=forked_data['dataset']['id']
        )[0]['id']
        resource = call_action(
            "resource_update",
            id=resource['id'],
            fork_resource=forked_data['resource']['id']
        )
        assert resource['fork_activity'] == forked_data['activity_id']

        for key in ['sha256', 'size', 'lfs_prefix', 'url_type']:
            assert resource[key] == forked_data['resource'][key]

    def test_resource_update_with_activity_id(self, forked_data):
        call_action('resource_patch', id=forked_data['resource']['id'], sha256='newsha')
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        resource = call_action(
            "resource_update",
            id=resource['id'],
            fork_resource=forked_data['resource']['id'],
            fork_activity=forked_data['activity_id']
        )
        resource = factories.Resource(package_id=dataset['id'])
        resource = call_action(
            "resource_update",
            id=resource['id'],
            fork_resource=forked_data['resource']['id'],
            fork_activity=forked_data['activity_id']
        )

        for key in ['sha256', 'size', 'lfs_prefix', 'url_type']:
            assert resource[key] == forked_data['resource'][key]


@pytest.fixture
def dataset():
    org = factories.Organization()
    dataset = factories.Dataset(
        type='auto-generate-name-from-title',
        id="test-id",
        owner_org=org['id'],
    )
    dataset['resources'] = resources=[factories.Resource(
        package_id='test-id',
        sha256='testsha256',
        size=999,
        lfs_prefix='test/prefix',
        url_type='upload'
    ) for i in range(3)]
    call_action('package_patch', id=dataset['id'], notes="Create an activity")
    return call_action('package_show', id=dataset['id'])


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDatasetFork():

    def test_dataset_metadata_duplicated(self, dataset):
        result = call_action(
            'dataset_fork',
            id=dataset['id'],
            name="duplicated-dataset"
        )
        fields = ['title', 'notes', 'private', 'num_resources']
        duplicated = [result.get(field) == dataset.get(field) for field in fields]
        assert all(duplicated), f"Duplication failed: {list(zip(fields, duplicated))}"

    def test_dataset_metadata_not_duplicated(self, dataset):
        result = call_action(
            'dataset_fork',
            id=dataset['id'],
            name="duplicated-dataset"
        )
        fields = ['name', 'id']
        not_duplicated = [result.get(field) != dataset.get(field) for field in fields]
        assert all(not_duplicated), f"Duplication occured: {list(zip(fields, not_duplicated))}"

    def test_resource_metadata_duplicated(self, dataset):
        result = call_action(
            'dataset_fork',
            id=dataset['id'],
            name="duplicated-dataset"
        )
        assert len(dataset['resources']) == len(result['resources'])
        fields = ['name', 'sha256', 'size', 'lfs_prefix', 'url_type']

        for i in range(len(dataset['resources'])):
            for f in fields:
                duplicated = dataset['resources'][i][f] == result['resources'][i][f]
                assert duplicated, f"Field {f} did not duplicate for resource {i}"

    def test_dataset_not_found(self):
        with pytest.raises(toolkit.ObjectNotFound):
            call_action(
                'dataset_fork',
                id='non-existant-id',
                name="duplicated-dataset"
            )

    @pytest.mark.parametrize('key, value', [
        ('notes', 'Some new notes'),
        ('title', 'A new title'),
        ('private', True),
        ('resources', [])
    ])
    def test_metadata_overidden(self, key, value, dataset):
        data_dict = {
            'id': dataset['id'],
            'name': "duplicated-dataset",
            key: value
        }
        result = call_action('dataset_fork', **data_dict)
        assert result[key] == value


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestResourceFork():

    def test_resource_metadata_duplicated(self, dataset):
        resource = dataset['resources'][0]
        result = call_action(
            'resource_fork',
            id=resource['id']
        )
        fields = ['name', 'sha256', 'size', 'lfs_prefix', 'url_type']
        duplicated = [result.get(field) == resource.get(field) for field in fields]
        assert all(duplicated), f"Duplication failed: {list(zip(fields, duplicated))}"

    def test_resource_metadata_not_duplicated(self, dataset):
        result = call_action(
            'resource_fork',
            id=dataset['resources'][0]['id']
        )
        assert dataset['resources'][0]['id'] != result['id']

    def test_resource_not_found(self):
        with pytest.raises(toolkit.ObjectNotFound):
            call_action(
                'resource_fork',
                id='non-existant-id'
            )

    @pytest.mark.parametrize('key, value', [
        ('name', 'A new name'),
        ('name', ''),
        ('format', 'NEW'),
        ('format', 'JSON')
    ])
    def test_metadata_overidden(self, key, value, dataset):
        data_dict = {
            'id': dataset['resources'][0]['id'],
            key: value
        }
        result = call_action('resource_fork', **data_dict)
        assert result[key] == value
