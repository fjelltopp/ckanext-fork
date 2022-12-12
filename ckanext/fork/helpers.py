from ckanext.fork.util import get_forked_data
from ckan.plugins import toolkit


def get_parent_resource_details(resource_id):
    try:
        resource = toolkit.get_action('resource_show')(data_dict={'id': resource_id})
    except toolkit.NotAuthorized:
        return {'success': False,
                'msg': "Unable to access parent resource information; current user may not be authorized to access this."}

    try:
        package = toolkit.get_action('package_show')(data_dict={'id': resource['package_id']})
    except toolkit.NotAuthorized:
        return {'success': False,
                'msg': "Unable to access parent resource information; current user may not be authorized to access this."}

    organization = package['organization']
    return {
        'success': True,
        'resource': {
            'name': resource['name'],
            'url': resource['url'].split('/download')[0]
        },
        'package': {
            'id': package['id'],
            'name': package['title'],
            'url': '/dataset/'+package['name']
        },
        'organization': {
            'name': organization['title'],
            'url': '/organization/'+organization['name']
        }
    }


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
