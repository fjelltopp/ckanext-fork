import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
import ckanext.fork.util as util


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

        organization = package.get('organization')
        organization_title = organization['title'] if organization else ""
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
        if resource.get("fork"):
            resource = util.blob_storage_duplicate_resource(context, resource)
    return next_action(context, data_dict)


@toolkit.chained_action
def package_show(next_action, context, data_dict):
    dataset = next_action(context, data_dict)
    for resource in dataset["resources"]:
        if resource.get("fork"):
            forked_resource_id, forked_activity_id = util.parse_fork(resource["fork"])
            forked_data = util.get_forked_data(
                context,
                forked_resource_id,
                forked_activity_id
            )
            resource["forked_resource"] = {
                "resource_id": forked_resource_id,
                "resource_name": forked_data["resource"]["name"],
                "dataset_id": forked_data["dataset"]["id"],
                "dataset_title": forked_data["dataset"]["title"],
                "activity_id": forked_data["activity_id"],
                "synced": util.is_synced_fork(context, resource)
            }
    return dataset
