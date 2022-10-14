import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
import ckanext.fork.util as util
import logging

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



@logic.validate(logic.schema.default_autocomplete_schema)
def resource_autocomplete(context, data_dict):
    q = toolkit.get_or_bust(data_dict, 'q')
    q_lower = q.lower()
    results = toolkit.get_action('package_search')(context, {
        "q": q,
        "rows": 10
    })['results']
    pkg_list = []

    for package in results:
        resources = []

        for resource in package['resources']:
            last_modified = toolkit.h.time_ago_from_timestamp(resource['last_modified'])
            match = q_lower in resource['name'].lower()
            resources.append({
                'id': resource['id'],
                'name': resource['name'],
                'last_modified': last_modified,
                'match': match
            })

        organization_title = package.get('organization', {}).get('title', "")
        match = q_lower in package['name'].lower() or q_lower in package['title'].lower()
        pkg_list.append({
            'id': package['id'],
            'name': package['name'],
            'title': package['title'],
            'owner_org': organization_title,
            'match': match,
            'resources': resources
        })

    return pkg_list


@toolkit.chained_action
def package_create_update(next_action, context, data_dict):

    for resource in data_dict.get("resources", []):

        if resource.get("fork_resource"):
            resource = util.blob_storage_fork_resource(context, resource)

    return next_action(context, data_dict)


@toolkit.chained_action
def package_show(next_action, context, data_dict):
    dataset = next_action(context, data_dict)

    for resource in dataset.get("resources", []):

        if resource.get("fork_resource"):
            resource['fork_synced'] = util.is_synced_fork(context, resource)

    return dataset

