from ckan.plugins import toolkit


def parse_fork(value):
    if not type(value) == str:
        resource_id = None
        activity_id = None
    elif "@" in value:
        resource_id = value.split("@")[0]
        activity_id = value.split("@")[-1]
    else:
        resource_id = value
        activity_id = None
    return resource_id, activity_id


def get_forked_data(context, resource_id, activity_id=None):

    if activity_id:
        dataset = toolkit.get_action('activity_data_show')(context, {
            'id': activity_id,
            'object_type': 'package'
        })
        resource = [r for r in dataset['resources'] if r['id'] == resource_id][0]
    else:
        resource = toolkit.get_action('resource_show')(context, {'id': resource_id})
        dataset = toolkit.get_action('package_show')(context, {'id': resource['package_id']})
        activity_id = toolkit.get_action('package_activity_list')(
            context,
            {'id': dataset['id']}
        )[0]['id']

    return {
        'resource': resource,
        'dataset': dataset,
        'activity_id': activity_id
    }


def blob_storage_duplicate_resource(context, data_dict):
    fork = data_dict.get("fork")
    resource_id, activity_id = parse_fork(fork)
    forked_data = get_forked_data(context, resource_id, activity_id)

    for field in ['lfs_prefix', 'size', 'sha256', 'url_type']:
        data_dict[field] = forked_data['resource']['field']

    data_dict['fork'] = f"{resource_id}@{forked_data['activity_id']}"

    return context, data_dict
