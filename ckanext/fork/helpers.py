from ckanext.fork.util import get_forked_data
from ckan.plugins import toolkit


def fork_metadata(resource):
    metadata = {}

    if resource.get('fork_resource'):
        forked_resource_id = resource.get("fork_resource")
        forked_activity_id = resource.get("fork_activity")

        try:
            forked_data = get_forked_data(
                {},
                forked_resource_id,
                forked_activity_id
            )
            metadata = {
                "resource_id": forked_resource_id,
                "resource_name": forked_data["resource"]["name"],
                "dataset_id": forked_data["dataset"]["id"],
                "dataset_name": forked_data["dataset"]["name"],
                "dataset_title": forked_data["dataset"]["title"],
                "activity_id": forked_data["activity_id"]
            }
        except toolkit.NotAuthorized:
            pass

    return metadata

