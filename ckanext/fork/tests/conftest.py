import pytest
from ckan.tests import factories
from ckan.tests.helpers import call_action


@pytest.fixture
def forked_data():
    giftless_metadata = {
        "sha256": "dummysha",
        "size": 999,
        "lfs_prefix": "test/resource",
        "url_type": "upload"
    }
    organization = factories.Organization()
    forked_dataset = factories.Dataset(owner_org=organization['id'])
    forked_resource = factories.Resource(
        package_id=forked_dataset['id'],
        **giftless_metadata
    )
    call_action('package_patch', id=forked_dataset['id'], notes='An activity')
    forked_activity_id = call_action(
        'package_activity_list',
        id=forked_dataset['id']
    )[0]['id']
    return {
        'dataset': forked_dataset,
        'resource': forked_resource,
        'activity_id': forked_activity_id
    }
