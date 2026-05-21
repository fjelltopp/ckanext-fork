import pytest
from contextlib import nullcontext as does_not_raise
import ckanext.fork.validators as fork_validators
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories, helpers
from unittest import mock


@pytest.mark.usefixtures('clean_db')
class TestValidFork():

    VALID_ID_PARAMS = [
        (None, does_not_raise()),
        ("", does_not_raise()),
        ("{good_object_id}", does_not_raise()),
        ("bad-object-id", pytest.raises(toolkit.Invalid))
    ]

    @pytest.mark.parametrize("value, result", VALID_ID_PARAMS)
    def test_valid_dataset_id(self, value, result):
        dataset = factories.Dataset()

        if value:
            value = value.format(good_object_id=dataset['id'])

        key = ('some_key',)
        flattened_data = {key: value}

        with result:
            fork_validators.valid_dataset_id(key, flattened_data, {}, {'user': 'user'})

    @pytest.mark.parametrize("value, result", VALID_ID_PARAMS)
    def test_valid_resource_id(self, value, result):
        resource = factories.Resource()

        if value:
            value = value.format(good_object_id=resource['id'])

        key = ('resources', 0, 'some_key')
        flattened_data = {key: value}

        with result:
            fork_validators.valid_resource_id(key, flattened_data, {}, {'user': 'user'})

    @pytest.mark.usefixtures('clean_db_with_migrations', 'with_plugins')
    @pytest.mark.parametrize("value, result", VALID_ID_PARAMS)
    def test_valid_activity_id(self, value, result):
        user = factories.User()
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset["id"])

        # Trigger an activity by making a change (factories don't create activities)
        # Must provide user context for activity plugin
        helpers.call_action(
            'package_patch',
            context={'user': user['name']},
            id=dataset['id'],
            notes='Trigger activity'
        )

        # Get the activity created by the patch
        activity_list = helpers.call_action(
            'package_activity_list',
            id=dataset['id']
        )
        activity = activity_list[0]

        if value:
            value = value.format(good_object_id=activity['id'])

        key = ('some_key', )
        flattened_data = {key: value}

        with result:
            fork_validators.valid_activity_id(key, flattened_data, {}, {'user': user['name']})


    @pytest.mark.parametrize("fork_key, fork_value, result", [
        (('resources', 0, 'fork_resource'), "resource-id", does_not_raise()),
        (('resources', 0, 'fork_resource'), "", pytest.raises(toolkit.Invalid)),
        (('resources', 0, 'fork_resource'), None, pytest.raises(toolkit.Invalid)),
        (('fork_dataset',), "dataset-id", does_not_raise()),
        (('fork_dataset',), "", pytest.raises(toolkit.Invalid)),
        (('fork_dataset',), None, pytest.raises(toolkit.Invalid)),

    ])
    def test_check_forked_object(self, fork_key, fork_value, result):

        key = fork_key[:-1] + ("some_key",)
        flattened_data = {
            fork_key: fork_value,
            key: "some-value"
        }

        with result:
            fork_validators.check_forked_object(key, flattened_data, {}, {'user': 'user'})


    @pytest.mark.parametrize("new_value, result", [
        ("different-value", pytest.raises(toolkit.Invalid)),
        ("original-value", does_not_raise()),
    ])
    def test_dataset_field_not_changed(self, new_value, result):

        dataset = mock.Mock()
        dataset.some_key = "original-value"
        key = ('some_key',)
        flattened_data = {key: new_value}

        with result:
            fork_validators.dataset_field_not_changed(
                key,
                flattened_data,
                {},
                {'user': 'user', 'package': dataset}
            )


