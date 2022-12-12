import logging
import ckan.logic as logic
from ckanext.fork.util import get_forked_data
from ckan.plugins import toolkit

log = logging.getLogger(__name__)


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


def get_current_resource(context, resource):
    try:
        current = toolkit.get_action('resource_show')(
            context,
            {"id": resource["id"]}
        )
    except logic.NotFound as e:
        log.info(f"No existing resource found with error: {e}")
        current = {}
    except KeyError as e:
        log.info(f"No resource id provided, probably a new resource. Original error: {e}")
        current = {}
    except Exception as e:
        log.exception(f"I can't find the original resource for unknown reason: {e}")
        raise e

    return current


def check_metadata_for_changes(current, resource):
    file_metadata_changed = False
    if resource.get("fork_resource") or current.get("fork_resource"):
        for key in ['lfs_prefix', 'size', 'sha256', 'url_type']:
            new_value = resource.get(key, "")
            if new_value:
                original_value = current.get(key, "")
                if original_value != new_value:
                    file_metadata_changed = True
    return file_metadata_changed
