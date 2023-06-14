# coding: utf-8

import oci

##################################################################################################################
# define custom retry strategy
##################################################################################################################

custom_retry_strategy = oci.retry.RetryStrategyBuilder(
    max_attempts_check=True,
    max_attempts=10,
    total_elapsed_time_check=True,
    total_elapsed_time_seconds=600,
    retry_max_wait_between_calls_seconds=45,#Max Wait: 45sec between attempts
    retry_base_sleep_time_seconds=2,
    service_error_check=True,
    service_error_retry_on_any_5xx=True,
    service_error_retry_config={
        400: ['QuotaExceeded', 'LimitExceeded'],
        429: [],
        404: ['NotAuthorizedOrNotFound']
        },
    backoff_type=oci.retry.BACKOFF_FULL_JITTER_EQUAL_ON_THROTTLE_VALUE
    ).get_retry_strategy()

##################################################################################################################
# list all active instances
##################################################################################################################

def list_instances(core_client, compartment_id):

    Good_States=['RUNNING', 'STOPPED']
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    core_client.list_instances, 
                                                    compartment_id=compartment_id, 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        if (item.lifecycle_state in Good_States):
            resources.append(item)

    return resources

##################################################################################################################
# get boot volume for each instance
##################################################################################################################

def list_instances_bootvol(core_client, availability_domain, compartment_id, instance_id):
    
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    core_client.list_boot_volume_attachments,
                                                    availability_domain=availability_domain, 
                                                    compartment_id=compartment_id, 
                                                    instance_id=instance_id, 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all boot volume backups
##################################################################################################################

def list_boot_volume_backups(blk_storage_client, compartment_id, boot_volume_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    blk_storage_client.list_boot_volume_backups, 
                                                    compartment_id=compartment_id, 
                                                    boot_volume_id=boot_volume_id, 
                                                    lifecycle_state='AVAILABLE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data
    
    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all block volume attachement for each instance
##################################################################################################################

def list_instances_volattach(core_client, availability_domain, compartment_id, instance_id):
    
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    core_client.list_volume_attachments,
                                                    availability_domain=availability_domain, 
                                                    compartment_id=compartment_id, 
                                                    instance_id=instance_id, 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all block volume backups
##################################################################################################################

def list_volume_backups(blk_storage_client, compartment_id, volume_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    blk_storage_client.list_volume_backups,
                                                    compartment_id=compartment_id, volume_id=volume_id, 
                                                    lifecycle_state='AVAILABLE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data
            
    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active buckets
##################################################################################################################

def list_buckets(object_client,namespace_name, compartment_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    object_client.list_buckets, 
                                                    namespace_name=namespace_name, 
                                                    compartment_id=compartment_id, 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active fss
##################################################################################################################

def list_fss(fss_client, ad, compartment_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    fss_client.list_file_systems, 
                                                    compartment_id=compartment_id, 
                                                    availability_domain=ad, 
                                                    lifecycle_state='ACTIVE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active load balancers
##################################################################################################################

def list_load_balancers(loadbalancer_client, compartment_id):
    
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    loadbalancer_client.list_load_balancers, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='ACTIVE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active network load balancers
##################################################################################################################

def list_network_load_balancers(networkloadbalancer_client, compartment_id):
    
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    networkloadbalancer_client.list_network_load_balancers, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='ACTIVE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active network firewalls
##################################################################################################################

def list_network_firewalls(networkfw_client, compartment_id):
    
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    networkfw_client.list_network_firewalls, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='ACTIVE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active database systems
##################################################################################################################

def list_dbsystems(database_client, compartment_id):
    
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    database_client.list_db_systems, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='AVAILABLE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active db_homes in database systems
##################################################################################################################

def list_db_homes(database_client, compartment_id, db_system_id):
    
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    database_client.list_db_homes, 
                                                    db_system_id=db_system_id, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='AVAILABLE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active databases in systems databases db_home
##################################################################################################################

def list_databases(database_client, compartment_id, db_home_id):
    
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    database_client.list_databases, 
                                                    db_home_id=db_home_id, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='AVAILABLE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active autonomous databases
##################################################################################################################

def list_autonomous_db(database_client, compartment_id):

    Good_States=['AVAILABLE','STOPPED']
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    database_client.list_autonomous_databases, 
                                                    compartment_id=compartment_id, 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        if (item.lifecycle_state in Good_States):
            resources.append(item)

    return resources

##################################################################################################################
# list all active mysql databases
##################################################################################################################

def list_mysql_db(mysql_client, compartment_id):

    Good_States=['ACTIVE','INACTIVE']
    resources=[]

    items=oci.pagination.list_call_get_all_results(
                                                    mysql_client.list_db_systems, 
                                                    compartment_id=compartment_id, 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        if (item.lifecycle_state in Good_States):
            resources.append(item)

    return resources

##################################################################################################################
# list all active nosql databases
##################################################################################################################

def list_nosql_db(nosql_client, compartment_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    nosql_client.list_tables, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='ACTIVE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active opensearch clusters
##################################################################################################################

def list_opensearch_clusters(opensearch_client, compartment_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    opensearch_client.list_opensearch_clusters, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='ACTIVE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active cloud Exadata infrastructure on dedicated Exadata
##################################################################################################################

def list_cloud_exadata_infrastructures(database_client, compartment_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    database_client.list_cloud_exadata_infrastructures, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='AVAILABLE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active Autonomous Exadata VM clusters in the Oracle cloud
##################################################################################################################

def list_cloud_autonomous_vm_clusters(database_client, compartment_id, cloud_exadata_infrastructure_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    database_client.list_cloud_autonomous_vm_clusters, 
                                                    compartment_id=compartment_id, 
                                                    cloud_exadata_infrastructure_id=cloud_exadata_infrastructure_id, 
                                                    lifecycle_state='AVAILABLE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active Exadata VM clusters in the Oracle cloud
##################################################################################################################

def list_cloud_vm_clusters(database_client, compartment_id, cloud_exadata_infrastructure_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    database_client.list_cloud_vm_clusters, 
                                                    compartment_id=compartment_id, 
                                                    cloud_exadata_infrastructure_id=cloud_exadata_infrastructure_id, 
                                                    lifecycle_state='AVAILABLE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active analytics instances
##################################################################################################################

def list_analytics(analytics_client, compartment_id):

    Good_States=['ACTIVE', 'INACTIVE']
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    analytics_client.list_analytics_instances,
                                                    compartment_id=compartment_id, 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        if (item.lifecycle_state in Good_States):
            resources.append(item)

    return resources

##################################################################################################################
# list all active bigdata instances
##################################################################################################################

def list_bds(bds_client, compartment_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    bds_client.list_bds_instances, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='ACTIVE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active data catalogs
##################################################################################################################

def list_catalogs(data_catalog_client, compartment_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    data_catalog_client.list_catalogs, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='ACTIVE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active data integration workspaces
##################################################################################################################

def list_workspaces(data_integration_client, compartment_id):

    Good_States=['ACTIVE', 'STOPPED']
    resources=[]
    items=oci.pagination.list_call_get_all_results( 
                                                    data_integration_client.list_workspaces, 
                                                    compartment_id=compartment_id, 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        if (item.lifecycle_state in Good_States):
            resources.append(item)

    return resources

##################################################################################################################
# list all active function applications
##################################################################################################################

def list_functions_app(function_client, compartment_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    function_client.list_applications, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='ACTIVE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active functions
##################################################################################################################

def list_functions(function_client, function_app_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    function_client.list_functions, 
                                                    application_id=function_app_id, 
                                                    lifecycle_state='ACTIVE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active container instances
##################################################################################################################

def list_container_instances(container_client, compartment_id):

    Good_States=['ACTIVE', 'INACTIVE']
    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    container_client.list_container_instances, 
                                                    compartment_id=compartment_id, 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        if (item.lifecycle_state in Good_States):
            resources.append(item)

    return resources

##################################################################################################################
# list all active artifacts
##################################################################################################################

def list_repositories(artifact_client, compartment_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    artifact_client.list_repositories, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='AVAILABLE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active meshes
##################################################################################################################

def list_meshes(mesh_client, compartment_id):

    resources=[]
    items=oci.pagination.list_call_get_all_results(
                                                    mesh_client.list_meshes, 
                                                    compartment_id=compartment_id, 
                                                    lifecycle_state='ACTIVE', 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        resources.append(item)

    return resources

##################################################################################################################
# list all active visual builder instances
##################################################################################################################

def list_vb_instances(visual_builder_client, compartment_id):

    # vb instances must be running to update tags
    resources=[]
    Good_States=['ACTIVE', 'INACTIVE']

    items=oci.pagination.list_call_get_all_results(
                                                    visual_builder_client.list_vb_instances, 
                                                    compartment_id=compartment_id, 
                                                    retry_strategy=custom_retry_strategy
                                                    ).data

    for item in items:
        if (item.lifecycle_state in Good_States):
            resources.append(item)

    return resources