# coding: utf-8

##################################################################################################################
# name: OCI-TagCompute.py
# task: tag resources using display_name of each resource in order to get cost per display_name
#
# author: Florian Bonneville
# version: 1.0 - june 13th 2023
# 
# ***********************************************************************
# oci search for all resources using this tag :
# ***********************************************************************
# query all resources where
#                         definedTags.namespace == 'My_Namespace' 
#                      && definedTags.key == 'display_name'
#
# or
#
# query all resources where
#                         definedTags.namespace == 'My_Namespace' 
#                      && definedTags.key == 'display_name' 
#                      && definedTags.value == 'SERVICE_NAME'
#
# ***********************************************************************
#
# disclaimer: this is not an official Oracle application,  
# it does not supported by Oracle Support
##################################################################################################################

import oci
import copy
import argparse
import datetime
from modules.identity import * 
from modules.resources import *
from modules.tagging import *
from modules.utils import *

ScriptName = 'OCI-TagByName'
starting = datetime.datetime.now()

##################################################################################################################
# get command line arguments
##################################################################################################################

parser=argparse.ArgumentParser()

# default authentication uses instance_principals

parser.add_argument('-cs', action='store_true', default=False, dest='is_delegation_token', help='Use CloudShell Delegation Token for authentication')
parser.add_argument('-cf', action='store_true', default=False, dest='is_config_file', help='Use local OCI config file for authentication')
parser.add_argument('-cfp', default='~/.oci/config', dest='config_file_path', help='Path to your OCI config file, default: ~/.oci/config')
parser.add_argument('-cp', default='DEFAULT', dest='config_profile', help='config file section to use, default: DEFAULT')
parser.add_argument('-tlc', default='', dest='target_comp', help='compartment ocid to analyze, default is your root compartment')
parser.add_argument('-rg', default='', dest='target_region', help='region to analyze, default: all regions')
parser.add_argument('-tn', default='', dest='TagNamespace', help='name of the TagNamespace owning your TagKey',required=True)
parser.add_argument('-tk', default='', dest='TagKey', help='name of the TagKey to apply',required=True)
parser.add_argument('-c', action='store_true', default=False, dest='compute', help='Tag Compute resources')
parser.add_argument('-s', action='store_true', default=False, dest='storage', help='Tag Object Storage resources')
parser.add_argument('-n', action='store_true', default=False, dest='network', help='Tag Network resources')
parser.add_argument('-d', action='store_true', default=False, dest='database', help='Tag Database resources')
parser.add_argument('-a', action='store_true', default=False, dest='analytics', help='Tag Analytics resources')
parser.add_argument('-dev', action='store_true', default=False, dest='development', help='Tag Development resources')
parser.add_argument('-all', action='store_true', default=False, dest='all_services', help='Tag all supported resources')

cmd = parser.parse_args()

##################################################################################################################
# clear shell screen
##################################################################################################################

clear()

##################################################################################################################
# check arguments
##################################################################################################################

if cmd.all_services:
    cmd.compute = True
    cmd.storage = True
    cmd.network = True
    cmd.database = True
    cmd.analytics = True
    cmd.development = True

##################################################################################################################
# print header
##################################################################################################################

print()
print(green(f"{'*'*79:79}"))
print(green(f"{'*'*5:10} {'Analysis:':20} {'started':20} {ScriptName:20} {'*'*5:5}"))

##################################################################################################################
# oci authentication
##################################################################################################################

config, signer, oci_tname=create_signer(cmd.config_file_path, 
                                        cmd.config_profile, 
                                        cmd.is_delegation_token, 
                                        cmd.is_config_file)
tenancy_id=config['tenancy']

##################################################################################################################
# init oci service clients
##################################################################################################################

identity_client=oci.identity.IdentityClient(config=config, signer=signer)
search_client = oci.resource_search.ResourceSearchClient(config=config, signer=signer)

##################################################################################################################
# set target compartments & regions
##################################################################################################################

if cmd.target_comp:
    top_level_compartment_id=cmd.target_comp
    compartment_name = get_compartment_name(identity_client, top_level_compartment_id)
    print(green(f"{'*'*5:10} {'Compartment:':20} {'filtered':20} {compartment_name[:18]:20} {'*'*5:5}"))
else:
    top_level_compartment_id=tenancy_id
    compartment_name = get_compartment_name(identity_client, top_level_compartment_id)
    print(green(f"{'*'*5:10} {'Compartment:':20} {'tenancy':20} {compartment_name[:18]:20} {'*'*5:5}"))

my_compartments=get_compartment_list(identity_client, top_level_compartment_id)
print(green(f"{'*'*5:10} {'Compartments:':20} {'analyzed':20} {len(my_compartments):<20} {'*'*5:5}"))

if cmd.target_region:
    print(green(f"{'*'*5:10} {'Region:':20} {'filtered':20} {cmd.target_region:20} {'*'*5:5}"))
else:
    print(green(f"{'*'*5:10} {'Regions:':20} {'analyzed':20} {'all_regions':20} {'*'*5:5}"))

all_regions=get_region_subscription_list(identity_client, tenancy_id, cmd.target_region)

if not cmd.target_region:
    print(green(f"{'*'*5:10} {'Regions:':20} {'subscribed':20} {len(all_regions):<20} {'*'*5:5}"))

##################################################################################################################
# check TagNamespace and TagKey
##################################################################################################################

check_tags(identity_client, search_client, cmd.TagNamespace, cmd.TagKey)

##################################################################################################################
# print header
##################################################################################################################

print(green(f"{'*'*79:79}\n"))
print(f"{'REGION':15}  {'AD':6}  {'COMPARTMENT':20}  {'RESOURCE_TYPE':15}  {'RESOURCE_NAME':20}\n")

##################################################################################################################
# set custom retry strategy
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
# start analysis
##################################################################################################################

for region in all_regions:
    config['region']=region.region_name
    core_client=oci.core.ComputeClient(config=config, signer=signer)
    blk_storage_client=oci.core.BlockstorageClient(config=config, signer=signer)
    object_client=oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    fss_client=oci.file_storage.FileStorageClient(config=config, signer=signer)
    loadbalancer_client=oci.load_balancer.LoadBalancerClient(config=config, signer=signer)
    networkloadbalancer_client=oci.network_load_balancer.NetworkLoadBalancerClient(config=config, signer=signer)
    networkfw_client=oci.network_firewall.NetworkFirewallClient(config=config, signer=signer)
    database_client=oci.database.DatabaseClient(config=config, signer=signer)
    mysql_client=oci.mysql.DbSystemClient(config=config, signer=signer)
    nosql_client=oci.nosql.NosqlClient(config=config, signer=signer)
    opensearch_client=oci.opensearch.OpensearchClusterClient(config=config, signer=signer)
    analytics_client=oci.analytics.AnalyticsClient(config=config, signer=signer)
    bds_client=oci.bds.BdsClient(config=config, signer=signer)
    data_catalog_client=oci.data_catalog.DataCatalogClient(config=config, signer=signer)
    data_integration_client=oci.data_integration.DataIntegrationClient(config=config, signer=signer)
    function_client=oci.functions.FunctionsManagementClient(config=config, signer=signer)
    container_client=oci.container_instances.ContainerInstanceClient(config=config, signer=signer)
    artifact_client=oci.artifacts.ArtifactsClient(config=config, signer=signer)
    mesh_client=oci.service_mesh.ServiceMeshClient(config=config, signer=signer)
    visual_builder_client=oci.visual_builder.VbInstanceClient(config=config, signer=signer)

    if cmd.target_region == '' or region.region_name in cmd.target_region:
        identity_client=oci.identity.IdentityClient(config=config, signer=signer)
        ADs=list_ads(identity_client, tenancy_id)

        for compartment in my_compartments:
            
            print('   {}: Analyzing compartment: {}'.format(region.region_name, compartment.name[0:18]),end=' '*15+'\r',flush=True)

            if cmd.compute:
                ##########################################
                # get compute instances
                ##########################################
                all_instances=list_instances(core_client, compartment.id)

                for instance in all_instances:
                    service='instance'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, instance.display_name[0:18]),end=' '*15+'\r',flush=True)

                        # 1- retrieve instance tags
                        defined_tags_dict = copy.deepcopy(instance.defined_tags)

                        # 2- add key/value to defined_tags_dict
                        # 2a- if tagnamespace already exists in defined_tags_dict:
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = instance.display_name

                        # 2b- else when tagnamespace doesn't exist in defined_tags_dict
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: instance.display_name}})
                        
                        tag_resources(service, core_client, instance.id, defined_tags_dict)
                        print(yellow(f"{region.region_name:15}  {instance.availability_domain[-4:]:6}  {compartment.name[0:18]:20}  {service:15}  {instance.display_name[0:18]:20}"))

                        ##########################################
                        # get attached boot volume
                        ##########################################
                        instance_bootvolattach=list_instances_bootvol(core_client, instance.availability_domain, compartment.id, instance.id)

                        for bootvolattach in instance_bootvolattach:
                            service='bootvolume'
                            print('   {}: Tagging {}: {}'.format(service, region.region_name, bootvolattach.display_name[0:18]),end=' '*15+'\r',flush=True)
                            
                            bootvol=blk_storage_client.get_boot_volume(bootvolattach.boot_volume_id).data

                            defined_tags_dict = copy.deepcopy(bootvol.defined_tags)
                            try:
                                defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = instance.display_name
                            except:
                                defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: instance.display_name}})

                            tag_resources(service, blk_storage_client, bootvol.id, defined_tags_dict)
                            print(yellow(f"{region.region_name:15}  {bootvol.availability_domain[-4:]:6}  {compartment.name[0:18]:20}  {service:15}  {bootvol.display_name[0:18]:20}"))

                        ##########################################
                        # get boot volume backups
                        ##########################################
                        boot_volume_backups=list_boot_volume_backups(blk_storage_client, compartment.id, bootvol.id)

                        for boot_volume_backup in boot_volume_backups:
                            service='boot_backup'
                            print('   {}: Tagging {}: {}'.format(service, region.region_name, boot_volume_backup.display_name[0:18]),end=' '*15+'\r',flush=True)

                            bootvolbkp=blk_storage_client.get_boot_volume_backup(boot_volume_backup.id).data

                            defined_tags_dict = copy.deepcopy(boot_volume_backup.defined_tags)
                            try:
                                defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = instance.display_name
                            except:
                                defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: instance.display_name}})

                            tag_resources(service, blk_storage_client, boot_volume_backup.id, defined_tags_dict)
                            print(yellow(f"{region.region_name:15}  {'-':6}  {compartment.name[0:18]:20}  {service:15}  {bootvolbkp.display_name[0:18]:20}"))

                        ##########################################
                        # get attached block volumes
                        ##########################################
                        try:
                            instance_vol_attach=list_instances_volattach(core_client, instance.availability_domain, compartment.id, instance.id)

                            for vol_attach in instance_vol_attach:
                                service='volume'
                                print('   {}: Tagging {}: {}'.format(service, region.region_name, vol_attach.display_name[0:18]),end=' '*15+'\r',flush=True)

                                volume=blk_storage_client.get_volume(vol_attach.volume_id).data

                                defined_tags_dict = copy.deepcopy(volume.defined_tags)
                                try:
                                    defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = instance.display_name
                                except:
                                    defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: instance.display_name}})

                                tag_resources(service, blk_storage_client, volume.id, defined_tags_dict)
                                print(yellow(f"{region.region_name:15}  {volume.availability_domain[-4:]:6}  {compartment.name[0:18]:20}  {service:15}  {volume.display_name[0:18]:20}"))

                            ##########################################
                            # get block volume backups
                            ##########################################
                            volume_backups=list_volume_backups(blk_storage_client, compartment.id, volume.id)

                            for volume_backup in volume_backups:
                                service='volume_backup'
                                print('   {}: Tagging {}: {}'.format(service, region.region_name, volume_backup.display_name[0:18]),end=' '*15+'\r',flush=True)

                                volbkp=blk_storage_client.get_volume_backup(volume_backup.id).data

                                defined_tags_dict = copy.deepcopy(volume_backup.defined_tags)
                                try:
                                    defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = instance.display_name
                                except:
                                    defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: instance.display_name}})

                                tag_resources(service, blk_storage_client, volume_backup.id, defined_tags_dict)
                                print(yellow(f"{region.region_name:15}  {'-':6}  {compartment.name[0:18]:20}  {service:15}  {volbkp.display_name[0:18]:20}"))
                        except:
                            pass # pass if no block volumes or backups found

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{instance.display_name}\n ocid:{instance.id}\n {e}\n'))
                        pass

            if cmd.storage:
                ##########################################
                # get buckets
                ##########################################
                namespace_name=object_client.get_namespace().data
                resources=list_buckets(object_client,namespace_name, compartment.id)

                for resource in resources:
                    service='bucket'

                    try:
                        working_bucket=object_client.get_bucket(namespace_name,resource.name).data

                        print('   {}: Tagging {}: {}'.format(service, region.region_name, working_bucket.name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(working_bucket.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.name}})

                        tag_resources(service, object_client, working_bucket.id, defined_tags_dict, working_bucket.name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {working_bucket.name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{working_bucket.name}\n ocid:{working_bucket.id}\n {e}\n'))
                        pass
                
                ##########################################
                # get fss
                ##########################################
                for ad in ADs:
                    resources=list_fss(fss_client, ad, compartment.id)

                    for resource in resources:
                        service='fss'

                        try:
                            print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)
                            
                            defined_tags_dict = copy.deepcopy(resource.defined_tags)
                            try:
                                defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                            except:
                                defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})

                            tag_resources(service, fss_client, resource.id, defined_tags_dict, resource.display_name)
                            print(yellow(f"{region.region_name:15}  {resource.availability_domain[-4:]:6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                        except Exception as e:
                            print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                            pass

            if cmd.network:
                ##########################################
                # get load balancers
                ##########################################
                resources=list_load_balancers(loadbalancer_client, compartment.id)

                for resource in resources:
                    service='loadbalancer'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                        
                        tag_resources(service, loadbalancer_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                ##########################################
                # get network load balancers
                ##########################################
                resources=list_network_load_balancers(networkloadbalancer_client, compartment.id)

                for resource in resources:
                    service='ntwloadbalancer'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                        
                        tag_resources(service, networkloadbalancer_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                ##########################################
                # get network firewalls
                ##########################################
                resources=list_network_firewalls(networkfw_client, compartment.id)

                for resource in resources:
                    service='networkfw'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                        
                        tag_resources(service, networkfw_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

            if cmd.database:
                ##########################################
                # get database systems
                ##########################################
                resources=list_dbsystems(database_client, compartment.id)

                for resource in resources:
                    service='dbsystem'

                    try:
                        try:
                            print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                            defined_tags_dict = copy.deepcopy(resource.defined_tags)
                            try:
                                defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                            except:
                                defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                            
                            tag_resources(service, database_client, resource.id, defined_tags_dict, resource.display_name)
                            print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                        except Exception as e:
                            print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                            pass

                        ##########################################
                        # get db_homes in database systems
                        ##########################################
                        dbhomes=list_db_homes(database_client, compartment.id, resource.id)

                        for dbhome in dbhomes:
                            service='dbhome'
                            
                            ##########################################
                            # get databases in db_homes
                            ##########################################
                            databases=list_databases(database_client, compartment.id, dbhome.id)

                            for database in databases:
                                service='dbsys_db'

                                try:
                                    print('   {}: Tagging {}: {}'.format(service, region.region_name, database.db_name[0:18]),end=' '*15+'\r',flush=True)

                                    defined_tags_dict = copy.deepcopy(database.defined_tags)
                                    try:
                                        defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                                    except:
                                        defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})

                                    tag_resources(service, database_client, database.id, defined_tags_dict, resource.display_name)
                                    print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {database.db_name[0:18]:20}"))

                                except Exception as e:
                                    print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{database.db_name}\n ocid:{database.id}\n {e}\n'))
                                    pass

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass
                        
                ##########################################
                # get autonomous databases
                ##########################################
                resources=list_autonomous_db(database_client, compartment.id)

                for resource in resources:
                    service='autonomous'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                        
                        tag_resources(service, database_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                ##########################################
                # get cloud exadata infrastructures
                ##########################################
                resources=list_cloud_exadata_infrastructures(database_client, compartment.id)

                for resource in resources:
                    service='exa_infra'

                    try:
                        try:
                            print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                            defined_tags_dict = copy.deepcopy(resource.defined_tags)
                            try:
                                defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                            except:
                                defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                            
                            tag_resources(service, database_client, resource.id, defined_tags_dict)
                            print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                        except Exception as e:
                            print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                            pass

                        ##########################################
                        # get cloud_autonomous_vm_clusters
                        ##########################################
                        cloud_autonomous_vm_clusters=list_cloud_autonomous_vm_clusters(database_client, compartment.id, resource.id)

                        for cloud_autonomous_vm_cluster in cloud_autonomous_vm_clusters:
                            service='auto_vm_cluster'

                            try:
                                print('   {}: Tagging {}: {}'.format(service, region.region_name, cloud_autonomous_vm_cluster.display_name[0:18]),end=' '*15+'\r',flush=True)

                                defined_tags_dict = copy.deepcopy(cloud_autonomous_vm_cluster.defined_tags)
                                try:
                                    defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                                except:
                                    defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                                
                                tag_resources(service, database_client, cloud_autonomous_vm_cluster.id, defined_tags_dict)
                                print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {cloud_autonomous_vm_cluster.display_name[0:18]:20}"))

                            except Exception as e:
                                print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{cloud_autonomous_vm_cluster.display_name}\n ocid:{cloud_autonomous_vm_cluster.id}\n {e}\n'))
                                pass

                        ##########################################
                        # get cloud_vm_clusters
                        ##########################################
                        cloud_vm_clusters=list_cloud_vm_clusters(database_client, compartment.id, resource.id)

                        for cloud_vm_cluster in cloud_vm_clusters:
                            service='cloud_vm_cluster'

                            try:
                                print('   {}: Tagging {}: {}'.format(service, region.region_name, cloud_vm_cluster.display_name[0:18]),end=' '*15+'\r',flush=True)

                                defined_tags_dict = copy.deepcopy(cloud_vm_cluster.defined_tags)
                                try:
                                    defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                                except:
                                    defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                                
                                tag_resources(service, database_client, cloud_vm_cluster.id, defined_tags_dict)
                                print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {cloud_vm_cluster.display_name[0:18]:20}"))

                            except Exception as e:
                                print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{cloud_vm_cluster.display_name}\n ocid:{cloud_vm_cluster.id}\n {e}\n'))
                                pass

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{cloud_vm_cluster.display_name}\n ocid:{cloud_vm_cluster.id}\n {e}\n'))
                        pass

                ##########################################
                # get MySQL databases
                ##########################################
                resources=list_mysql_db(mysql_client, compartment.id)

                # MySQL instances must be running to update tag
                # script starts inactive/untagged instances, apply tags and stops
                stop_after_tag = False

                for resource in resources:
                    service='mysql'
                    
                    mysql_inst=mysql_client.get_db_system(resource.id).data

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, mysql_inst.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(mysql_inst.defined_tags)

                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = mysql_inst.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: mysql_inst.display_name}})

                        # if != means tag is missing
                        if defined_tags_dict != mysql_inst.defined_tags:
                                
                            if (mysql_inst.lifecycle_state == 'INACTIVE'):
                                stop_after_tag = True

                                print('   Starting MySQL: {}'.format(mysql_inst.display_name),end=' '*40 +'\r',flush=True)

                                mysql_client.start_db_system(
                                                            mysql_inst.id, 
                                                            retry_strategy=custom_retry_strategy
                                                            )
                                
                                wait_response = oci.wait_until(
                                                                mysql_client, 
                                                                mysql_client.get_db_system(mysql_inst.id),
                                                                'lifecycle_state', 
                                                                'ACTIVE', 
                                                                max_wait_seconds=600, 
                                                                retry_strategy=custom_retry_strategy
                                                                ).data

                            tag_resources(service, mysql_client, mysql_inst.id, defined_tags_dict, mysql_inst.display_name)
                            
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {mysql_inst.display_name[0:18]:20}"))

                        # stop instance previously stopped
                        if stop_after_tag == True:
                                print('   Stopping MySQL: {}'.format(mysql_inst.display_name),end=' '*40 +'\r',flush=True)
                                stop_db_system_details=oci.mysql.models.StopDbSystemDetails(shutdown_type="SLOW")
                                mysql_client.stop_db_system(mysql_inst.id, stop_db_system_details, retry_strategy=custom_retry_strategy)
                                wait_response = oci.wait_until(mysql_client, mysql_client.get_db_system(mysql_inst.id), 'lifecycle_state', 'UPDATING', max_wait_seconds=600).data

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{mysql_inst.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                ##########################################
                # get NoSQL databases
                ##########################################
                resources=list_nosql_db(nosql_client, compartment.id)

                for resource in resources:
                    service='nosql'
                    
                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.name}})
                        
                        tag_resources(service, nosql_client, resource.id, defined_tags_dict, resource.name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                ##########################################
                # get OpenSearch clusters
                ##########################################
                resources=list_opensearch_clusters(opensearch_client, compartment.id)

                for resource in resources:
                    service='opensearch'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                        
                        tag_resources(service, opensearch_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

            if cmd.analytics:
                ##########################################
                # get analytics instances
                ##########################################
                resources=list_analytics(analytics_client, compartment.id)
 
                for resource in resources:
                    service='analytics'
                    resource=analytics_client.get_analytics_instance(resource.id).data

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.name}})
                        
                        tag_resources(service, analytics_client, resource.id, defined_tags_dict, resource.name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                ##########################################
                # get big data instances
                ##########################################
                resources=list_bds(bds_client, compartment.id)

                for resource in resources:
                    service='bigdata'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                        
                        tag_resources(service, bds_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                ##########################################
                # get data catalogs
                ##########################################
                resources=list_catalogs(data_catalog_client, compartment.id)

                for resource in resources:
                    service='datacatalog'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})

                        tag_resources(service, data_catalog_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                ##########################################
                # get data integration catalogs
                ##########################################
                resources=list_workspaces(data_integration_client, compartment.id)

                for resource in resources:
                    service='dataintegration'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})

                        tag_resources(service, data_integration_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

            if cmd.development:
                ##########################################
                # get function applications
                ##########################################
                resources=list_functions_app(function_client, compartment.id)
 
                for resource in resources:
                    service='function_app'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                        
                        tag_resources(service, function_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                    ##########################################
                    # get function instances
                    ##########################################
                    fn_apps=list_functions(function_client, resource.id)
    
                    for fn_app in fn_apps:
                        service='function'

                        try:
                            print('   {}: Tagging {}: {}'.format(service, region.region_name, fn_app.display_name[0:18]),end=' '*15+'\r',flush=True)

                            defined_tags_dict = copy.deepcopy(fn_app.defined_tags)
                            try:
                                defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                            except:
                                defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                            
                            tag_resources(service, function_client, fn_app.id, defined_tags_dict, fn_app.display_name)
                            print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {fn_app.display_name[0:18]:20}"))

                        except Exception as e:
                            print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{fn_app.display_name}\n ocid:{fn_app.id}\n {e}\n'))
                            pass

                ##########################################
                # get container instances
                ##########################################
                resources=list_container_instances(container_client, compartment.id)
 
                for resource in resources:
                    service='container'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                        
                        tag_resources(service, container_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                ##########################################
                # get artifact repositories
                ##########################################
                resources=list_repositories(artifact_client, compartment.id)
 
                for resource in resources:
                    service='artifact'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                        
                        tag_resources(service, artifact_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                ##########################################
                # get mesh instances
                ##########################################
                resources=list_meshes(mesh_client, compartment.id)
 
                for resource in resources:
                    service='mesh'

                    try:
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, resource.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(resource.defined_tags)
                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = resource.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: resource.display_name}})
                        
                        tag_resources(service, mesh_client, resource.id, defined_tags_dict, resource.display_name)
                        print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {resource.display_name[0:18]:20}"))

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{resource.display_name}\n ocid:{resource.id}\n {e}\n'))
                        pass

                ##########################################
                # get visual builder instances
                ##########################################
                resources=list_vb_instances(visual_builder_client, compartment.id)

                # VB instances must be running to update tag
                # script starts inactive/untagged instances, apply tags and stops
                stop_after_tag = False

                for resource in resources:
                    service='visual_builder'

                    vb_inst=visual_builder_client.get_vb_instance(resource.id).data

                    try:                
                        print('   {}: Tagging {}: {}'.format(service, region.region_name, vb_inst.display_name[0:18]),end=' '*15+'\r',flush=True)

                        defined_tags_dict = copy.deepcopy(vb_inst.defined_tags)

                        try:
                            defined_tags_dict[cmd.TagNamespace][cmd.TagKey] = vb_inst.display_name
                        except:
                            defined_tags_dict.update({cmd.TagNamespace: {cmd.TagKey: vb_inst.display_name}})

                        # if != means tag is missing
                        if defined_tags_dict != vb_inst.defined_tags:

                            if (vb_inst.lifecycle_state == 'INACTIVE'):
                                stop_after_tag = True

                                print('   Starting Visual Builder: {}'.format(vb_inst.display_name),end=' '*40 +'\r',flush=True)

                                visual_builder_client.start_vb_instance(
                                                                        vb_inst.id, 
                                                                        retry_strategy=custom_retry_strategy
                                                                        )

                                wait_response = oci.wait_until(
                                                                visual_builder_client, 
                                                                visual_builder_client.get_vb_instance(vb_inst.id), 
                                                                'lifecycle_state', 
                                                                'ACTIVE', 
                                                                max_wait_seconds=600, 
                                                                retry_strategy=custom_retry_strategy
                                                                ).data


                            tag_resources(service, visual_builder_client, vb_inst.id, defined_tags_dict, vb_inst.display_name)
                            wait_response = oci.wait_until(visual_builder_client, visual_builder_client.get_vb_instance(vb_inst.id), 'lifecycle_state', 'ACTIVE', max_wait_seconds=600).data
                            print(yellow(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {vb_inst.display_name[0:18]:20}"))
                        else:
                            print(magenta(f"{region.region_name:15}  {' - ':6}  {compartment.name[0:18]:20}  {service:15}  {vb_inst.display_name[0:18]:20}"))
                            pass

                        # stop instance previously stopped
                        if stop_after_tag == True:
                                print('   Stopping Visual Builder: {}'.format(vb_inst.display_name),end=' '*40 +'\r',flush=True)
                                visual_builder_client.stop_vb_instance(vb_inst.id, retry_strategy=custom_retry_strategy)
                                wait_response = oci.wait_until(visual_builder_client, visual_builder_client.get_vb_instance(vb_inst.id), 'lifecycle_state', 'UPDATING', max_wait_seconds=600).data

                    except Exception as e:
                        print(red(f'\n region:{region.region_name}\n compartment:{compartment.name}\n name:{vb_inst.display_name}\n ocid:{vb_inst.id}\n {e}\n'))
                        pass


print(' '*40)
ended = datetime.datetime.now()
print(f"\nExecution time: {ended-starting}\n")