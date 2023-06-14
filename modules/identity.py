# coding: utf-8

import oci
import os 
from modules.utils import *

##################################################################################################################
# get tenancy name
##################################################################################################################

def get_tenancy(tenancy_id, config, signer):
    identity = oci.identity.IdentityClient(config=config, signer=signer)
    try:
        tenancy = identity.get_tenancy(tenancy_id)
        #print(tenancy.data)

    except Exception as e:
        print(red(e))
        raise SystemExit    

    return tenancy.data.name, tenancy.data.home_region_key

##################################################################################################################
# create signer for Authentication
# input - config_profile and is_instance_principals and is_delegation_token
# output - config and signer objects
##################################################################################################################

def create_signer(config_file_path, config_profile, is_delegation_token, is_config_file):

    # --------------------------------
    # Config File authentication
    # --------------------------------
    if is_config_file:
        try:
            config = oci.config.from_file(file_location=config_file_path, profile_name=config_profile)
            oci.config.validate_config(config) # raise an error if error in config

            signer = oci.signer.Signer(
                tenancy=config['tenancy'],
                user=config['user'],
                fingerprint=config['fingerprint'],
                private_key_file_location=config.get('key_file'),
                pass_phrase=oci.config.get_config_value_or_default(config, 'pass_phrase'),
                private_key_content=config.get('key_content')
            )

            print(green(f"{'*'*5:10} {'Login:':20} {'success':20} {'config file':20} {'*'*5:5}"))
            print(green(f"{'*'*5:10} {'Login:':20} {'profile':20} {config_profile:20} {'*'*5:5}"))
            
            oci_tname, oci_tregion = get_tenancy(config['tenancy'], config, signer)
            print(green(f"{'*'*5:10} {'Tenancy:':20} {oci_tname:20} {'home region: '+ oci_tregion:20} {'*'*5:5}"))

            return config, signer, oci_tname
            
        except:
            print(red('\n****'))
            print(red("Authentication Error: check your Config file/profile"))
            print(red(f"config_file: {config_file_path}"))
            print(red(f"config_profile: {config_profile}"))
            print(red('****\n'))
            raise SystemExit

    # --------------------------------
    # Delegation Token authentication
    # --------------------------------
    elif is_delegation_token:

        try:
            # ------------------------------------------------------------------------------
            # check if env variables OCI_CONFIG_FILE, OCI_CONFIG_PROFILE exist and use them
            # ------------------------------------------------------------------------------
            env_config_file = os.environ.get('OCI_CONFIG_FILE')
            env_config_section = os.environ.get('OCI_CONFIG_PROFILE')
            config = oci.config.from_file(env_config_file, env_config_section)
            delegation_token_location = config['delegation_token_file']
            oci.config.validate_config(config) # raise an error if error in config

            with open(delegation_token_location, 'r') as delegation_token_file:
                delegation_token = delegation_token_file.read().strip()
                signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)

            print(green(f"{'*'*5:10} {'Login:':20} {'success':20} {'delegation token':20} {'*'*5:5}"))
            print(green(f"{'*'*5:10} {'Login:':20} {'token':20} {delegation_token_location:20} {'*'*5:5}"))

            oci_tname, oci_tregion = get_tenancy(config['tenancy'], config, signer)
            print(green(f"{'*'*5:10} {'Tenancy:':20} {oci_tname:20} {'home region: '+ oci_tregion:20} {'*'*5:5}"))

            return config, signer, oci_tname

        except:
            print (red("Authentication Error: {Error obtaining delegation_token_file}"))
            raise SystemExit

    # -----------------------------------
    # Instance Principals authentication
    # -----------------------------------
    else:
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
            # print(signer.region)
            # print(signer.tenancy_id)
            oci_tname, oci_tregion = get_tenancy(config['tenancy'], config, signer)

            #oci.config.validate_config(config) # raise an error if error in config
            print(green(f"{'*'*5:10} {'Login:':20} {'success':20} {'instance principals':20} {'*'*5:5}"))
            print(green(f"{'*'*5:10} {'Tenancy:':20} {oci_tname:20} {'home region: '+ oci_tregion:20} {'*'*5:5}"))

            return config, signer, oci_tname

        except:
            print(red('\n****'))
            print (red(f"Authentication Error: Instance Principals"))
            print(red('****\n'))
            raise SystemExit

##################################################################################################################
# get all compartments in the tenancy using OCI search (not used hereby)
##################################################################################################################

def get_compartments(search_client):
    print('   Retrieving compartments...',end=' '*15+'\r',flush=True)    
    search = oci.resource_search.models.StructuredSearchDetails(
        query="query compartment resources",
        type='Structured',
        matching_context_type=oci.resource_search.models.SearchDetails.MATCHING_CONTEXT_TYPE_NONE)
    
    compartments = oci.pagination.list_call_get_all_results(search_client.search_resources, search).data # no limits return
    print('   Compartments retrieved...',end=' '*15+'\r',flush=True)    

    return compartments

##################################################################################################################
# get all compartments in the tenancy
##################################################################################################################

def get_compartment_list(identity_client, compartment_id):
    print('   Retrieving compartments...',end=' '*15+'\r',flush=True)
    target_compartments = []
    all_compartments = []

    try:
        top_level_compartment_response = identity_client.get_compartment(compartment_id)
        target_compartments.append(top_level_compartment_response.data)
        all_compartments.append(top_level_compartment_response.data)
    
    except oci.exceptions.ServiceError as response:
        print(red('\n****'))
        print (red(f"Error compartment_id: {compartment_id} : {response.code} - {response.message}"))
        print(red('****\n'))
        raise SystemExit

    while len(target_compartments) > 0:
        target = target_compartments.pop(0)

        child_compartment_response = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            target.id
        )
        target_compartments.extend(child_compartment_response.data)
        all_compartments.extend(child_compartment_response.data)

    active_compartments = []

    for compartment in all_compartments:
        if compartment.lifecycle_state== 'ACTIVE':
            active_compartments.append(compartment)

    return active_compartments

##################################################################################################################
# get compartment name
##################################################################################################################

def get_compartment_name(identity_client, compartment_id):
    
    compartment_name = identity_client.get_compartment(compartment_id).data.name

    return compartment_name

##################################################################################################################
# get all subscribed region in the tenancy
##################################################################################################################

def get_region_subscription_list(identity_client, tenancy_id, target_region):
    print('   Retrieving regions...',end=' '*15+'\r',flush=True)
    active_regions = identity_client.list_region_subscriptions(tenancy_id)

    # check if specified region has been subscribed
    if target_region != '':
        region_names=[]
        for region in active_regions.data:
            region_names.append(region.region_name)
        if target_region in region_names:
            pass
        else:
            print(red('\n****'))
            print(red(f'Region {target_region} not subscribed or doesn"t exist...'))
            print(red('****\n'))
            raise SystemExit

    print('   Regions retrieved...',end=' '*15+'\r',flush=True)    

    return active_regions.data

##################################################################################################################
# check if TagNamespace and TagKey exist in tenancy
##################################################################################################################

def check_tags(identity_client, search_client, cmd_TagNamespace, cmd_TagKey):

    search = oci.resource_search.models.StructuredSearchDetails(
        query="query tagnamespace resources",
        type='Structured',
        matching_context_type=oci.resource_search.models.SearchDetails.MATCHING_CONTEXT_TYPE_NONE)

    tag_namespaces = oci.pagination.list_call_get_all_results(search_client.search_resources, search).data
    all_tag_namespaces={}

    for item in tag_namespaces:
        all_tag_namespaces.update({item.display_name : item.identifier})

    # search if TagNameSpace exists in tag_namespaces
    if cmd_TagNamespace in all_tag_namespaces:

        # check tag_namespace state
        tag_namespace=identity_client.get_tag_namespace(all_tag_namespaces[cmd_TagNamespace]).data

        if tag_namespace.is_retired == False and tag_namespace.lifecycle_state == 'ACTIVE':
            print(green(f"{'*'*5:10} {'Tag Namespace:':20} {'found':20} {tag_namespace.name:20} {'*'*5:5}"))
            # retrieve tag keys
            tag_keys=identity_client.list_tags(tag_namespace.id).data
            
            for tag_key in tag_keys:

                if tag_key.name == cmd_TagKey:

                    # check tag_key state
                    if tag_key.is_retired == False and tag_key.lifecycle_state == 'ACTIVE':
                        tk=identity_client.get_tag(tag_namespace.id, tag_key.name).data
                        print(green(f"{'*'*5:10} {'Tag Key:':20} {'found':20} {tag_key.name:20} {'*'*5:5}"))

                        if tk.validator == None: # if validator is not 'null' means key is a list of predefined values 
                            return True
                        else:
                            raise SystemExit(red(f'\nInvalid Tag Value Type: {tk.validator}, must be an empty static value\n'))
                    else:
                        raise SystemExit(red(f'\nInvalid Tag Key State: Retired:True/State:INACTIVE\n'))
        else:
            raise SystemExit(red(f'\nInvalid Tag Namespace state: Retired:{tag_namespace.is_retired}/State:{tag_namespace.lifecycle_state}\n'))
    else:
        raise SystemExit(red(f'\nTag Namespace not found: {cmd_TagNamespace}\n'))

    raise SystemExit(red(f'\nTag Key not found: {cmd_TagKey}\n'))

##################################################################################################################
# get all ADs per region
##################################################################################################################

def list_ads(identity_client, tenancy_id):
    print('   Retrieving ADs...',end=' '*15+'\r',flush=True)

    try:
        ADs = identity_client.list_availability_domains(tenancy_id).data
        ADs_in_region=[]

        for ad in ADs:
            ADs_in_region.append(ad.name)
        print('   Ads retrieved...',end=' '*15+'\r',flush=True)    
   
    except Exception as e:
        print(red(e))
        quit()    

    return ADs_in_region