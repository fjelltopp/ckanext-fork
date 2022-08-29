import ckan.logic as logic
import ckan.plugins.toolkit as toolkit


@logic.validate(logic.schema.default_autocomplete_schema)
def resource_autocomplete(context, data_dict):
    q = data_dict['q']
    q_lower = q.lower()
    data_dict['rows'] = 10
    results = toolkit.get_action('package_search')(context, data_dict)['results']
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

        organization = package.get('organization', {}).get('title')
        match = q_lower in package['name'].lower() or q_lower in package['title'].lower()
        pkg_list.append({
            'id': package['id'],
            'name': package['name'],
            'title': package['title'],
            'owner_org': organization,
            'match': match,
            'resources': resources
        })

    return pkg_list
