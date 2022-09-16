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
