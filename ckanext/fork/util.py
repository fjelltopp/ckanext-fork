from ckan.plugins import toolkit


def get_forked_data(context, resource_id, activity_id=None):

    if activity_id:
        dataset = toolkit.get_action('activity_data_show')(context, {
            'id': activity_id,
            'object_type': 'package'
        })
        resource = [r for r in dataset['resources'] if r['id'] == resource_id][0]
    else:
        resource = toolkit.get_action('resource_show')(context, {'id': resource_id})
        dataset = toolkit.get_action('package_show')(context, {
            'id': resource['package_id']
        })
        activity_id = toolkit.get_action('package_activity_list')(
            context,
            {'id': dataset['id']}
        )[0]['id']

    return {
        'resource': resource,
        'dataset': dataset,
        'activity_id': activity_id
    }


def is_synced_fork(context, resource):

    if not resource.get('fork_resource'):
        return False

    forked_resource_id = resource.get('fork_resource')
    forked_resource_current_sha256 = toolkit.get_action("resource_show")(
        {**context, 'check_synced': False},
        {'id': forked_resource_id}
    ).get("sha256")
    return forked_resource_current_sha256 == resource.get("sha256")


def blob_storage_fork_resource(context, resource):
    resource_id = resource.get("fork_resource")
    activity_id = resource.get("fork_activity")
    forked_data = get_forked_data(context, resource_id, activity_id)

    for field in ['lfs_prefix', 'size', 'sha256', 'url_type']:
        resource[field] = forked_data['resource'][field]

    resource['fork_activity'] = forked_data['activity_id']
    return resource
