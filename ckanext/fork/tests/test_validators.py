import pytest
from contextlib import nullcontext as does_not_raise
import ckanext.fork.validators as fork_validators
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories


@pytest.mark.usefixtures('clean_db')
class TestValidFork():

    @pytest.mark.parametrize("fork_value, result", [
        (None, does_not_raise()),
        ("", does_not_raise()),
        ("{resource_id}", does_not_raise()),
        ("{resource_id}@", does_not_raise()),
        ("{resource_id}@{activity_id}", does_not_raise()),
        ("{resource_id}@bad-activity-id", pytest.raises(toolkit.Invalid)),
        ("bad-resource-id", pytest.raises(toolkit.Invalid)),
        ("bad-resource-id@bad-activity-id", pytest.raises(toolkit.Invalid)),
        ("@{activity_id}", pytest.raises(toolkit.Invalid))
    ])
    def test_valid_fork(self, fork_value, result):
        user = factories.User()
        resource = factories.Resource(id="good-resource-id")
        dataset = factories.Dataset(resources=[resource])
        activity = factories.Activity(
            activity_type="changed package",
            object_id=dataset["id"],
            user_id=user["id"]
        )

        if fork_value:
            fork_value = fork_value.format(
                resource_id=resource['id'],
                activity_id=activity['id']
            )

        key = ('resources', 0, 'fork')
        flattened_data = {key: fork_value}

        with result:
            fork_validators.valid_fork(key, flattened_data, {}, {'user': 'user'})
