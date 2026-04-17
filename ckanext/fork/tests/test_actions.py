import io
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
    datasets.append(factories.Dataset(
        title="Private Dataset",
        name="test-dataset-04",
        owner_org=organization['id'],
        private=True
    ))

    for (d, dataset) in enumerate(datasets):
        dataset["resources"] = [factories.Resource(
            name=f"Test Resource {(d*3)+r:02d}",
            package_id=dataset['id'],
            id=f"{str(d)*8}-{str(d)*4}-{str(d)*4}-{str(d)*4}-{str(r)*12}"
        ) for r in range(3)]

    return datasets


@pytest.mark.usefixtures('clean_db_with_migrations', 'with_plugins', 'with_request_context')
class TestResourceAutocomplete():

    def test_resource_autocomplete_raises_error_if_no_query(self):
        with pytest.raises(toolkit.ValidationError):
            call_action('resource_autocomplete')

    @pytest.mark.parametrize("q,result_names", [
        ('02', ['test-dataset-02', 'test-dataset-00']),
        ('00', ['test-dataset-00', 'test-dataset-04', 'test-dataset-02', 'test-dataset-01']),
        ('01', ['test-dataset-01', 'test-dataset-00']),
        ('Resource 01', ['test-dataset-01', 'test-dataset-00']),
        ('22222222-2222-2222-2222-000000000000', ['test-dataset-02']),
        ('00000000-0000-0000-0000-111111111111', ['test-dataset-00']),
        # Check private datasets are included in the response
        ('Private Resource 01', ['test-dataset-04', 'test-dataset-01', 'test-dataset-00'])
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


@pytest.mark.usefixtures('clean_db_with_migrations', 'with_plugins')
class TestResourceShow():

    def test_synced_fork_display(self, forked_data):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        response = call_action('resource_show', id=resource['id'])
        assert response['fork_synced']

    def test_unsynced_fork(self, forked_data):
        user = factories.User()
        call_action('resource_patch', context={'user': user['name']}, id=forked_data['resource']['id'], sha256='newsha')
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id'],
            fork_activity=forked_data['activity_id']
        )
        response = call_action('resource_show', id=resource['id'])
        assert not response['fork_synced']

    def test_no_access_to_forked_resource(self, forked_data):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id'],
            fork_activity=forked_data['activity_id']
        )
        user = factories.User()
        call_action('package_patch', context={'user': user['name']}, id=forked_data['dataset']['id'], private=True)
        user = factories.User()
        response = toolkit.get_action('resource_show')(
            {'user': user['name']},
            {'id': resource['id']}
        )
        assert response['fork_synced']


@pytest.mark.usefixtures('clean_db_with_migrations', 'with_plugins')
class TestResourceCreate():

    def test_not_fork_resource_create(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        assert not resource.get('fork_resource', False)
        assert not resource.get('fork_activity', False)
        assert not resource.get('fork_synced', False)

    def test_fork_resource_create_with_no_activity_id(self, forked_data):
        user = factories.User()
        dataset = factories.Dataset()
        resource = call_action(
            "resource_create",
            context={'user': user['name']},
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        assert resource['fork_activity'] == forked_data['activity_id']

        for key in ['sha256', 'size', 'lfs_prefix', 'url_type']:
            assert resource[key] == forked_data['resource'][key]

    def test_fork_resource_create_with_activity_id(self, forked_data):
        user = factories.User()
        call_action('resource_patch', context={'user': user['name']}, id=forked_data['resource']['id'], sha256='newsha')
        dataset = factories.Dataset()
        resource = call_action(
            "resource_create",
            context={'user': user['name']},
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id'],
            fork_activity=forked_data['activity_id']
        )

        for key in ['sha256', 'size', 'lfs_prefix', 'url_type']:
            assert resource[key] == forked_data['resource'][key]


@pytest.mark.usefixtures('clean_db_with_migrations', 'with_plugins')
class TestResourceUpdate():

    def test_fork_resource_update_with_no_activity_id(self, forked_data):
        user = factories.User()
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        forked_data['resource'] = call_action(
            'resource_patch',
            context={'user': user['name']},
            id=forked_data['resource']['id'],
            sha256='newsha'
        )
        forked_data['activity_id'] = call_action(
            'package_activity_list',
            id=forked_data['dataset']['id']
        )[0]['id']
        resource = call_action(
            "resource_update",
            context={'user': user['name']},
            id=resource['id'],
            fork_resource=forked_data['resource']['id']
        )
        assert resource['fork_activity'] == forked_data['activity_id']

        for key in ['sha256', 'size', 'lfs_prefix', 'url_type']:
            assert resource[key] == forked_data['resource'][key]

    def test_fork_resource_update_with_activity_id(self, forked_data):
        user = factories.User()
        call_action('resource_patch', context={'user': user['name']}, id=forked_data['resource']['id'], sha256='newsha')
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        resource = call_action(
            "resource_update",
            context={'user': user['name']},
            id=resource['id'],
            fork_resource=forked_data['resource']['id'],
            fork_activity=forked_data['activity_id']
        )
        resource = factories.Resource(package_id=dataset['id'])
        resource = call_action(
            "resource_update",
            context={'user': user['name']},
            id=resource['id'],
            fork_resource=forked_data['resource']['id'],
            fork_activity=forked_data['activity_id']
        )

        for key in ['sha256', 'size', 'lfs_prefix', 'url_type']:
            assert resource[key] == forked_data['resource'][key]

    def test_non_fork_resource_update_with_new_fork_resource(self, forked_data):
        user = factories.User()
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
        )
        resource = call_action(
            "resource_update",
            context={'user': user['name']},
            id=resource['id'],
            fork_resource=forked_data['resource']['id'],
        )
        assert resource['fork_activity'] == forked_data['activity_id']

        for key in ['sha256', 'size', 'lfs_prefix', 'url_type']:
            assert resource[key] == forked_data['resource'][key]

    def test_fork_resource_update_with_new_non_fork_resource_details(self, forked_data):
        user = factories.User()
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        resource = call_action(
            "resource_update",
            context={'user': user['name']},
            id=resource['id'],
            url='http://link.to.some.data'
        )
        assert resource['fork_resource'] == ''
        assert resource['fork_activity'] == ''

    def test_fork_resource_update_with_new_metadata(self, forked_data):
        user = factories.User()
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )
        resource['description'] = 'New description'
        resource = call_action(
            "resource_update",
            context={'user': user['name']},
            **resource
        )
        assert resource['fork_resource'] == forked_data['resource']['id']
        assert resource['fork_activity'] == forked_data['activity_id']
        assert resource['description'] == 'New description'

    def test_non_fork_resource_update_with_new_fork_details(self, forked_data):
        user = factories.User()
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
        )
        resource = call_action(
            "resource_update",
            context={'user': user['name']},
            id=resource['id'],
            fork_resource=forked_data['resource']['id']
        )
        assert resource['fork_activity'] == forked_data['activity_id']

        for key in ['sha256', 'size', 'lfs_prefix', 'url_type']:
            assert resource[key] == forked_data['resource'][key]

    def test_fork_resource_update_with_new_non_fork_resource_details_via_api_call(self, app, forked_data):
        """Test that uploading a file via HTTP API clears fork metadata."""
        user = factories.SysadminWithToken()
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            fork_resource=forked_data['resource']['id']
        )

        headers = {
            'Authorization': user['token'],
        }
        files = {
            'id': resource['id'],
            'upload': (io.BytesIO(b'some text data'), 'test.txt'),
        }
        response = app.post(
            url=toolkit.url_for(
                controller='api',
                action='action',
                logic_function='resource_update',
                ver='/3'
            ),
            headers=headers,
            data=files
        )
        assert response.status_code == 200

        resource = call_action(
            "resource_show",
            id=resource['id'],
        )
        assert resource['fork_resource'] == ''
        assert resource['fork_activity'] == ''


@pytest.fixture
def dataset():
    """
    Creates a test dataset with 3 resources containing blob storage metadata.
    
    Used by TestDatasetFork and TestResourceFork to test forking functionality.
    """
    user = factories.User()
    org = factories.Organization()
    dataset = factories.Dataset(
        # CKAN 2.11 Fix: Removed type='auto-generate-name-from-title'
        # This was an invalid dataset type that caused routing errors in CKAN 2.11:
        # "Could not build url for endpoint 'auto-generate-name-from-title_resource.download'"
        # The plugin doesn't define custom types (package_types() returns [])
        # Removing this parameter allows CKAN to use the default 'dataset' type
        # type='auto-generate-name-from-title',
        owner_org=org['id'],
    )
    dataset['resources'] = [factories.Resource(
        package_id=dataset['id'],
        sha256='testsha256',
        size=999,
        lfs_prefix='test/prefix',
        url_type='upload'
    ) for i in range(3)]
    call_action('package_patch', context={'user': user['name']}, id=dataset['id'], notes="Create an activity")
    return call_action('package_show', id=dataset['id'])


@pytest.mark.usefixtures('clean_db_with_migrations', 'with_plugins')
class TestDatasetFork():

    def test_dataset_metadata_duplicated(self, dataset):
        user = factories.User()
        result = call_action(
            'dataset_fork',
            context={'user': user['name']},
            id=dataset['id'],
            name="duplicated-dataset"
        )
        fields = ['title', 'notes', 'private', 'num_resources']
        duplicated = [result.get(field) == dataset.get(field) for field in fields]
        assert all(duplicated), f"Duplication failed: {list(zip(fields, duplicated))}"

    def test_dataset_metadata_not_duplicated(self, dataset):
        user = factories.User()
        result = call_action(
            'dataset_fork',
            context={'user': user['name']},
            id=dataset['id'],
            name="duplicated-dataset"
        )
        fields = ['name', 'id']
        not_duplicated = [result.get(field) != dataset.get(field) for field in fields]
        assert all(not_duplicated), f"Duplication occured: {list(zip(fields, not_duplicated))}"

    def test_resource_metadata_duplicated(self, dataset):
        user = factories.User()
        result = call_action(
            'dataset_fork',
            context={'user': user['name']},
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
        user = factories.User()
        with pytest.raises(toolkit.ObjectNotFound):
            call_action(
                'dataset_fork',
                context={'user': user['name']},
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
        user = factories.User()
        data_dict = {
            'context': {'user': user['name']},
            'id': dataset['id'],
            'name': "duplicated-dataset",
            key: value
        }
        result = call_action('dataset_fork', **data_dict)
        assert result[key] == value


@pytest.mark.usefixtures('clean_db_with_migrations', 'with_plugins')
class TestResourceFork():

    def test_resource_metadata_duplicated(self, dataset):
        user = factories.User()
        resource = dataset['resources'][0]
        result = call_action(
            'resource_fork',
            context={'user': user['name']},
            id=resource['id']
        )
        fields = ['name', 'sha256', 'size', 'lfs_prefix', 'url_type']
        duplicated = [result.get(field) == resource.get(field) for field in fields]
        assert all(duplicated), f"Duplication failed: {list(zip(fields, duplicated))}"

    def test_resource_metadata_not_duplicated(self, dataset):
        user = factories.User()
        result = call_action(
            'resource_fork',
            context={'user': user['name']},
            id=dataset['resources'][0]['id']
        )
        assert dataset['resources'][0]['id'] != result['id']

    def test_resource_not_found(self):
        user = factories.User()
        with pytest.raises(toolkit.ObjectNotFound):
            call_action(
                'resource_fork',
                context={'user': user['name']},
                id='non-existant-id'
            )

    @pytest.mark.parametrize('key, value', [
        ('name', 'A new name'),
        ('name', ''),
        ('format', 'NEW'),
        ('format', 'JSON')
    ])
    def test_metadata_overidden(self, key, value, dataset):
        user = factories.User()
        data_dict = {
            'context': {'user': user['name']},
            'id': dataset['resources'][0]['id'],
            key: value
        }
        result = call_action('resource_fork', **data_dict)
        assert result[key] == value
