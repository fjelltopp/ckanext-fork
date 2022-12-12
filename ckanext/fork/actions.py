import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
import ckanext.fork.util as util
import logging
import re
from ckanext.fork.helpers import check_metadata_for_changes, get_current_resource

log = logging.getLogger(__name__)


def dataset_fork(context, data_dict):
    dataset_id_or_name = toolkit.get_or_bust(data_dict, 'id')
    dataset = toolkit.get_action('package_show')(context, {'id': dataset_id_or_name})
    dataset_id = dataset['id']

    data_dict['fork_dataset'] = dataset_id
    data_dict['fork_activity'] = toolkit.get_action('package_activity_list')(
        context,
        {'id': dataset_id}
    )[0]['id']

    dataset.pop('id', None)
    dataset.pop('name', None)
    data_dict.pop('id', None)
    context.pop('package', None)

    dataset = {**dataset, **data_dict}

    for resource in dataset.get('resources', []):
        del resource['id']
        del resource['package_id']

    new_dataset = toolkit.get_action('package_create')(context, dataset)

    return toolkit.get_action('package_show')(context, {'id': new_dataset['id']})


def resource_fork(context, data_dict):
    resource_id = toolkit.get_or_bust(data_dict, 'id')
    activity_id = data_dict.pop('activity_id', None)
    forked_data = util.get_forked_data(context, resource_id, activity_id)
    resource = forked_data['resource']
    resource.pop('id')
    data_dict.pop('id')
    data_dict['fork_resource'] = resource_id
    data_dict['fork_activity'] = forked_data['activity_id']
    resource = {**resource, **data_dict}
    new_resource = toolkit.get_action('resource_create')(context, resource)
    return toolkit.get_action('resource_show')(
        {'for_View': True},
        {'id': new_resource['id']}
    )


@toolkit.side_effect_free
@logic.validate(logic.schema.default_autocomplete_schema)
def resource_autocomplete(context, data_dict):
    q = toolkit.get_or_bust(data_dict, 'q').strip()
    q_lower = q.lower()
    datasets = []
    pkg_list = []

    if _is_uuid(q_lower):
        datasets = _get_dataset_from_resource_uuid(context, q_lower)

    if not datasets:
        datasets = toolkit.get_action('package_search')(context, {
            "q": q,
            "rows": 10,
            "include_private": True
        })['results']

    for dataset in datasets:

        if not dataset['resources']:
            continue

        resources = []

        for resource in dataset['resources']:
            last_modified = toolkit.h.time_ago_from_timestamp(resource['last_modified'])
            match = q_lower in resource['name'].lower() or q_lower == resource['id']
            resources.append({
                'id': resource['id'],
                'name': resource['name'],
                'format': resource['format'],
                'filename': resource['url'].split('/')[-1],
                'last_modified': last_modified,
                'match': match
            })

        organization_title = dataset.get('organization', {}).get('title', "")
        match = q_lower in dataset['name'].lower() or q_lower in dataset['title'].lower()
        pkg_list.append({
            'id': dataset['id'],
            'name': dataset['name'],
            'title': dataset['title'],
            'owner_org': organization_title,
            'match': match,
            'resources': resources
        })

    return pkg_list


def _is_uuid(input):
    regex = r"[a-z, 0-9]{8}-[a-z, 0-9]{4}-[a-z, 0-9]{4}-[a-z, 0-9]{4}-[a-z, 0-9]{12}"
    return re.search(regex, input)


def _get_dataset_from_resource_uuid(context, uuid):
    try:
        resource = toolkit.get_action('resource_show')(
            context,
            {"id": uuid}
        )
        package = toolkit.get_action('package_show')(
            context,
            {"id": resource['package_id']}
        )
        return [package]
    except toolkit.NotFound:
        return []


@toolkit.chained_action
def package_create(next_action, context, data_dict):
    for resource in data_dict.get("resources", []):
        if resource.get("fork_resource"):
            resource = util.blob_storage_fork_resource(context, resource)

    return next_action(context, data_dict)


@toolkit.chained_action
def package_update(next_action, context, data_dict):
    for resource in data_dict.get("resources", []):
        current = get_current_resource(context, resource)
        resource_metadata_changed = check_metadata_for_changes(current, resource)
        if resource.get("fork_resource") and not resource_metadata_changed:
            resource = util.blob_storage_fork_resource(context, resource)
        else:
            resource['fork_resource'] = ''
            resource['fork_activity'] = ''

    return next_action(context, data_dict)


@toolkit.chained_action
def package_show(next_action, context, data_dict):
    dataset = next_action(context, data_dict)

    if context.get('check_synced', True):

        for resource in dataset.get("resources", []):

            if resource.get("fork_resource"):
                resource['fork_synced'] = util.is_synced_fork(context, resource)

    return dataset
