import pytest
from ckan import model
from ckan.tests import factories
from ckan.tests.helpers import call_action


@pytest.fixture
def forked_data():
    """
    Creates test data with fork metadata (requires activity plugin).

    Note: Tests using this fixture must use:
    @pytest.mark.usefixtures('clean_db_with_migrations', 'with_plugins')
    """
    giftless_metadata = {
        "sha256": "dummysha",
        "size": 999,
        "lfs_prefix": "test/resource",
        "url_type": "upload"
    }
    user = factories.User()
    organization = factories.Organization()
    forked_dataset = factories.Dataset(owner_org=organization['id'])
    forked_resource = factories.Resource(
        package_id=forked_dataset['id'],
        **giftless_metadata
    )
    # Trigger activity creation (factories don't create activities)
    call_action('package_patch', context={'user': user['name']}, id=forked_dataset['id'], notes='An activity')
    forked_activity_id = call_action(
        'package_activity_list',
        id=forked_dataset['id']
    )[0]['id']
    return {
        'dataset': forked_dataset,
        'resource': forked_resource,
        'activity_id': forked_activity_id
    }


@pytest.fixture
def clean_db_with_migrations(clean_db):
    """
    Extends the standard clean_db fixture to add activity plugin schema changes.

    In CKAN 2.11, the activity plugin adds a permission_labels column (text[])
    to the activity table. The clean_db fixture rebuilds the database without
    plugin-specific migrations, so we manually add the column here.
    """
    # Add the permission_labels column required by CKAN 2.11 activity plugin
    model.Session.execute("""
        ALTER TABLE activity
        ADD COLUMN IF NOT EXISTS permission_labels text[];
    """)
    model.Session.commit()
