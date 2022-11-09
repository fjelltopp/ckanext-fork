import ckan.plugins.toolkit as toolkit


def valid_resource_id(key, data, errors, context):
    value = data[key]

    if not value:
        return

    try:
        toolkit.get_action('resource_show')(context, {'id': value})
    except toolkit.ObjectNotFound:
        raise toolkit.Invalid(toolkit._(f'Resource {value} does not exist'))


def valid_dataset_id(key, data, errors, context):
    value = data[key]

    if not value:
        return

    try:
        toolkit.get_action('package_show')(context, {'id': value})
    except toolkit.ObjectNotFound:
        raise toolkit.Invalid(toolkit._(f'Dataset {value} does not exist'))


def valid_activity_id(key, data, errors, context):
    value = data[key]

    if not value:
        return

    try:
        toolkit.get_action('activity_show')(context, {
            'id': value,
            'include_data': False
        })
    except toolkit.ObjectNotFound:
        raise toolkit.Invalid(toolkit._(f'Activity {value} does not exist'))


def check_forked_object(key, data, errors, context):

    if not data[key]:
        return

    if len(key) == 1:
        fork_field = 'fork_dataset'
        key = (fork_field,)
    else:
        fork_field = 'fork_resource'
        key = key[:-1] + (fork_field,)

    if not data.get(key):
        raise toolkit.Invalid(toolkit._(f"Object is not forked, please specify {fork_field}"))


def dataset_field_not_changed(key, data, errors, context):
    package = context.get('package')

    if not package:
        return

    old_value = getattr(package, key[0], '')
    new_value = data[key]

    if new_value != old_value:
        raise toolkit.Invalid(f'Cannot change value of key from {old_value} '
                              f'to {new_value}.  This key is read-only.')
