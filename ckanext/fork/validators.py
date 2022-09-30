import ckan.plugins.toolkit as toolkit


def valid_fork_resource(key, data, errors, context):
    value = data[key]

    if not value:
        return

    try:
        toolkit.get_action('resource_show')(context, {'id': value})
    except toolkit.ObjectNotFound:
        raise toolkit.Invalid(toolkit._(f'Resource {value} does not exist'))


def valid_fork_activity(key, data, errors, context):
    value = data[key]

    if not value:
        return

    resource_key = key[:-1] + ('fork_resource',)

    if not data.get(resource_key):
        raise toolkit.Invalid(toolkit._("fork_resource not specified"))

    try:
        toolkit.get_action('activity_show')(context, {
            'id': value,
            'include_data': False
        })
    except toolkit.ObjectNotFound:
        raise toolkit.Invalid(toolkit._(f'Activity {value} does not exist'))

