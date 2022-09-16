import ckan.plugins.toolkit as toolkit


def valid_fork(key, data, errors, context):
    """
    Make sure an field is a valid organization_id
    """

    value = data[key]

    if not value:
        return

    if "@" in value:
        resource_id = value.split("@")[0]
        activity_id = value.split("@")[-1]
    else:
        resource_id = value
        activity_id = None

    try:
        toolkit.get_action('resource_show')(context, {'id': resource_id})
    except toolkit.ObjectNotFound:
        raise toolkit.Invalid(toolkit._(f'Resource {resource_id} does not exist'))

    if activity_id:

        try:
            toolkit.get_action('activity_show')(context, {
                'id': activity_id,
                'include_data': False
            })
        except toolkit.ObjectNotFound:
            raise toolkit.Invalid(toolkit._(f'Resource {activity_id} does not exist'))
