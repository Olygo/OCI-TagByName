# OCI-TagByName

**TagByName** retrieves the "display_name" of supported services and subsequently applies a "defined_tag" to the resource and its associated sub-resources, using the "display_name" as a reference for the tag key. As a result, you can easily obtain the cost per resource name in OCI Cost Analysis..

# Features 
- **TagByName** searches for supported resources, retrieves display name and apply desired defined tag such as key/value:
	-  namespace: MyTags
	-  key: display_name
	-  value: *name-of-the-resource*

- **Supported services** :
	- compute instances
		- attached boot volume
			- boot volume backups
		- attached block volumes
			- block volume backups
	- object storage
	- file storage
	- load balancers
	- network load balancers
	- network firewalls
	- database systems
		- databases
	- autonomous databases
	- cloud exadata infrastructures
		- cloud_autonomous_vm_clusters
		- cloud_vm_clusters
	- MySQL databases
	- NoSQL databases
	- OpenSearch clusters
	- analytics instances
	- big data instances
	- data catalogs 
	- data integration catalogs
	- function applications
		- function instances
	- container instances
	- artifact repositories
	- mesh instances
	- visual builder instances


- **Parameters for execution:**

Default authentication uses [Instance Principals](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/Content/Identity/Tasks/callingservicesfrominstances.htm), meaning you can run this script from an OCI virtual machine without having to provide any details or credentials


| Argument -| Parameter          | Description                                                            |
| --------- | ------------------ | ---------------------------------------------------------------------- |
| -cs       |                    | authenticate through CloudShell Delegation Token                       |
| -cf       |                    | authenticate through local OCI config_file                             |
| -cfp      | config_file_path   | change OCI config_file path, default: ~/.oci/config                    |
| -cp       | config_profile     | indicate config file section to use, default: DEFAULT                  |
| -tn       | tag_namespace      | tag_namespace hosting your tag_key, no default                         |
| -tk       | tag_key            | tag key to apply, no default                                           |
| -tlc      | compartment_ocid   | scan only a specific compartment, default: scan from root compartment  |
| -exc      | compartment_ocid   | exclude compartment ocid from analysis, default is none                |
| -rg       | region_name        | scan only a specific region, default: scan all regions                 |
| -c        |                    | tag compute resources                                                  |
| -s        |                    | tag storage resources                                                  |
| -n        |                    | tag network resources                                                  |
| -d        |                    | tag database resources                                                 |
| -a        |                    | tag analytics resources                                                |
| -dev      |                    | tag development resources                                              |
| -all      |                    | tag all supported resources                                            |
| -h        | --help             | show this help message and exit                                        |


# How to use
##### Default authentication:
	
	python3 OCI-TagByName.py -all -tn MyTags -tk display_name

By default **OCI-TagByName** tries to authenticate using Instance Principals

##### Authenticate with local_config_file:
	
	python3 ./OCI-TagByName.py -all -cf -tn MyTags -tk display_name

##### Authenticate with custom local_config_file & profile:
	
	python3 ./OCI-TagByName.py -all -cf -cfp /home/opc/myconfig -cp MyDomain -tn MyTags -tk display_name

##### Authenticate in cloud_shell:
	
	python3 ./OCI-TagByName.py -all -cs -tn MyTags -tk display_name

##### custom parameters example:
	
	python3 ./OCI-TagByName.py -all -cf -rg eu-paris-1 -tlc ocid1.compartment.oc1..aaaaaaaaurxxxx -tn MyTags -tk display_name

##### Script output
![Script Output](https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/ArOLIb0vUtXvhlffPSXKqA1V7pkm4l_Ecrj7pqEXWJ6tL-BSGg41CWqsIEeUMOa9/n/olygo/b/git_images/o/OCI-TagByName/output.png)

##### Instance tag
![Tag Instance](https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/ArOLIb0vUtXvhlffPSXKqA1V7pkm4l_Ecrj7pqEXWJ6tL-BSGg41CWqsIEeUMOa9/n/olygo/b/git_images/o/OCI-TagByName/tagInstance.png)

##### Related resources are also tagged (here storage & backups)
![Tag Resource](https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/ArOLIb0vUtXvhlffPSXKqA1V7pkm4l_Ecrj7pqEXWJ6tL-BSGg41CWqsIEeUMOa9/n/olygo/b/git_images/o/OCI-TagByName/tagBoot.png)

##### Filter cost analysis using defined tag: display_name:XXXXX
![Cost Analysis](https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/ArOLIb0vUtXvhlffPSXKqA1V7pkm4l_Ecrj7pqEXWJ6tL-BSGg41CWqsIEeUMOa9/n/olygo/b/git_images/o/OCI-TagByName/CostAnalysis1.png)

##### See costs associated to all the resources attached to my instance (compute, storage, backup):
![Cost Analysis](https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/ArOLIb0vUtXvhlffPSXKqA1V7pkm4l_Ecrj7pqEXWJ6tL-BSGg41CWqsIEeUMOa9/n/olygo/b/git_images/o/OCI-TagByName/CostAnalysis2.png)

##### Search all resources using display_name tags:
![Cost Analysis](https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/ArOLIb0vUtXvhlffPSXKqA1V7pkm4l_Ecrj7pqEXWJ6tL-BSGg41CWqsIEeUMOa9/n/olygo/b/git_images/o/OCI-TagByName/search.png)

# Quick install on Oracle Linux 7.9

	curl https://raw.githubusercontent.com/Olygo/OCI-TagByName/main/install.sh | bash

- install dependencies
- clone git repo locally
- schedule cron everyday at 11PM

##### - /!\ cron job runs script using Instance Principals authentication

# Install script into (free-tier) Autonomous Linux Instance

- Use an existing VCN or create a dedicated vcn (preferred) in a public or a private subnet (preferred if vpn or fastconnect)
- Create a free-tier compute instance using the Autonomous Linux 7.9 image
- Create a Dynamic Group called OCI_Scripting and add the OCID of your instance to the group, using this command:
```
	ANY {instance.id = 'OCID_of_your_Compute_Instance'}
```	

- Create a root level policy, giving your dynamic group permission to manage all-resources in tenancy:
```
	allow dynamic-group OCI_Scripting to manage all-resources in tenancy
```
- Login to your instance using an SSH connection
	- run the following commands:

```
  - sudo yum update -y
  - sudo yum install git -y
  - python3 -m pip install pip wheel oci oci-cli --user -U
  - git clone https://github.com/Olygo/OCI-TagByName.git
  - cd ./OCI-TagByName
```

## Questions ?
**_olygo.git@gmail.com_**


## Disclaimer
**Please test properly on test resources, before using it on production resources to prevent unwanted outages or unwanted bills.**
