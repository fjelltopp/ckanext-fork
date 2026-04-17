import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
import ckanext.fork.util as util
import logging
import re

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
        # CKAN's Solr schema (ckan/config/solr/schema.xml) indexes `res_name` but
        # NOT `res_id`, so package_search cannot find datasets by resource UUID
        # substring (required by ADX-879). We fetch up to 100 datasets and filter
        # resource IDs in Python. Capped by rows=100: instances with more datasets
        # won't match resource IDs beyond the top 100 by default sort. Lifting
        # this cap would require adding res_id to Solr (e.g. via
        # IPackageController.before_index) so package_search can filter directly.
        search_results = toolkit.get_action('package_search')(context, {
            "q": "*:*",
            "rows": 100,
            "include_private": True
        })
        datasets = search_results['results']

    # Split query into tokens for dataset-level matching (allows partial matches like "01")
    query_tokens = q_lower.split()

    for dataset in datasets:

        if not dataset['resources']:
            continue

        resources = []
        has_matching_resource = False

        for resource in dataset['resources']:
            last_modified = toolkit.h.time_ago_from_timestamp(resource['last_modified'])
            # For resources: match based on number of matching tokens
            # - Single token queries: require exact match (full string)
            # - Multi-token queries: require at least 2 tokens to match
            resource_lower = resource['name'].lower()
            resource_id_lower = resource['id'].lower()

            if len(query_tokens) == 1:
                # Single token: use full string matching
                match = q_lower in resource_lower or q_lower in resource_id_lower
                matching_tokens = 1 if match else 0
            else:
                # Multi-token: count how many tokens match
                matching_tokens = sum(
                    1 for token in query_tokens
                    if token in resource_lower or token in resource_id_lower
                )
                # Require at least 2 tokens to match
                match = matching_tokens >= 2

            if match:
                has_matching_resource = True
            resources.append({
                'id': resource['id'],
                'name': resource['name'],
                'format': resource['format'],
                'filename': resource['url'].split('/')[-1],
                'last_modified': last_modified,
                'match': match
            })

        organization_title = dataset.get('organization', {}).get('title', "")
        # For datasets: match any token from query (allows "01" in "Resource 01" to match "test-dataset-01")
        dataset_match = any(
            token in dataset['name'].lower() or token in dataset['title'].lower()
            for token in query_tokens
        )

        # Only include dataset if it matches at dataset level OR has matching resources
        if dataset_match or has_matching_resource:
            pkg_list.append({
                'id': dataset['id'],
                'name': dataset['name'],
                'title': dataset['title'],
                'owner_org': organization_title,
                'match': dataset_match,
                'resources': resources
            })

    # Sort results: datasets with name/title matches first, then resource-only matches
    # Within each group, maintain the order from package_search
    for i, item in enumerate(pkg_list):
        item['_original_index'] = i
    pkg_list.sort(key=lambda x: (not x['match'], x['_original_index']))
    # Remove the temporary index
    for item in pkg_list:
        del item['_original_index']

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
    except logic.NotFound:
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
        current = util.get_current_resource(context, resource)
        resource_metadata_changed = util.check_metadata_for_file_change(current, resource)
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
