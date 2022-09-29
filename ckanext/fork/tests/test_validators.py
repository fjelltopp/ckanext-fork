import pytest
from contextlib import nullcontext as does_not_raise
import ckanext.fork.validators as fork_validators
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories


@pytest.mark.usefixtures('clean_db')
class TestValidFork():

    @pytest.mark.parametrize("fork_resource, result", [
        (None, does_not_raise()),
        ("", does_not_raise()),
        ("{resource_id}", does_not_raise()),
        ("bad-resource-id", pytest.raises(toolkit.Invalid))
    ])
    def test_valid_fork_resource(self, fork_resource, result):
        resource = factories.Resource(id="good-resource-id")

        if fork_resource:
            fork_resource = fork_resource.format(resource_id=resource['id'])

        key = ('resources', 0, 'fork_resource')
        flattened_data = {key: fork_resource}

        with result:
            fork_validators.valid_fork_resource(key, flattened_data, {}, {'user': 'user'})

    @pytest.mark.parametrize("fork_resource, fork_activity, result", [
        (None, None, does_not_raise()),
        ("", "", does_not_raise()),
        ("{resource_id}", "{activity_id}", does_not_raise()),
        ("{resource_id}", "bad-activity-id", pytest.raises(toolkit.Invalid)),
        ("bad-resource-id", "{activity_id}", does_not_raise()),
        ("", "{activity_id}", pytest.raises(toolkit.Invalid)),
        (None, "{activity_id}", pytest.raises(toolkit.Invalid)),
    ])
    def test_valid_fork_activity(self, fork_resource, fork_activity, result):
        user = factories.User()
        resource = factories.Resource(id="good-resource-id")
        dataset = factories.Dataset(resources=[resource])
        activity = factories.Activity(
            activity_type="changed package",
            object_id=dataset["id"],
            user_id=user["id"]
        )

        if fork_resource:
            fork_resource = fork_resource.format(resource_id=resource['id'])

        if fork_activity:
            fork_activity = fork_activity.format(activity_id=activity['id'])

        key = ('resources', 0, 'fork_activity')
        flattened_data = {
            ('resources', 0, 'fork_resource'): fork_resource,
            key: fork_activity
        }

        with result:
            fork_validators.valid_fork_activity(key, flattened_data, {}, {'user': 'user'})
