#!/usr/bin/env python3
# Import/Export for NSX

################################################################################
### Copyright 2020-2023 VMware, Inc.
### Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved
### SPDX-License-Identifier: BSD-2-Clause
################################################################################

# For git BASH on Windows, you can use something like this 
# #!/C/Users/usr1/AppData/Local/Programs/Python/Python38/python.exe

"""

Welcome to Import/Export for NSX ! 

VMware Cloud on AWS API Documentation is available at: https://code.vmware.com/apis/920/vmware-cloud-on-aws
CSP API documentation is available at https://console.cloud.vmware.com/csp/gateway/api-docs
vCenter API documentation is available at https://code.vmware.com/apis/366/vsphere-automation


You can install python 3.8 from https://www.python.org/downloads/windows/ (Windows) or https://www.python.org/downloads/mac-osx/ (MacOs).

You can install the dependent python packages locally with:
pip3 install requests or pip3 install requests -t . --upgrade
pip3 install configparser or pip3 install configparser -t . --upgrade
pip3 install PTable or pip3 install PTable -t . --upgrade
pip3 install boto3

Or you can install all the requirement above with:
pip3 install -r requirements.txt

With git BASH on Windows, you might need to use 'python -m pip install' instead of pip3 install

"""
import boto3
import sys
MIN_PYTHON = (3,10)
assert sys.version_info >= MIN_PYTHON, f"Python {'.'.join([str(n) for n in MIN_PYTHON])} or newer is required."

import argparse
import requests                          # need this for Get/Post/Delete
import configparser                     # parsing config file
import time
import glob
import maskpass
from pathlib import Path
from prettytable import PrettyTable
import json
import os
#import vcenter
from VMCImportExport import VMCImportExport
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def yes_or_no(question):
    """ Forces user to respond, 'y' or 'n', returns True or False """
    while "the answer is invalid":
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False

# --------------------------------------------
# ---------------- Main ----------------------
# --------------------------------------------
def main(args):
    CONFIG_FILE_PATH="./config_ini/config.ini"
    VMC_CONFIG_FILE_PATH="./config_ini/vmc.ini"
    AWS_CONFIG_FILE_PATH="./config_ini/aws.ini"

    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                    epilog="Welcome to sddc_import_export!\n"
                                    "Examples:\n\n"
                                    "Export an SDDC:\n"
                                    "python sddc_import_export.py -o export\n\n"
                                    "Import an SDDC:\n"
                                    "python sddc_import_export.py -o import\n\n"
                                    "Import an SDDC from a zipfile:\n"
                                    "python sddc_import_export.py -o import -i json/2020-12-15_10-33-43_json-export.zip\n\n")
    ap.add_argument("-o","--operation", required=True, choices=['export','check-vmc-ini', 'list-t1s', 'list-domains','import'], help="export begins an NSX-T export. import begins an NSX-T import. check-vmc-ini displays the currently configured Org and SDDC for export operations with token authentication. list-t1s lists all T1 gateways. list-domains lists all NSX-T domains.")
    #ap.add_argument("-t", "--test-name", required=False, nargs='+', choices=['create-cgw-groups','delete-cgw-groups','delete-all-cgw-groups'])
    #ap.add_argument("-n", "--num-objects", required=False, type=int, default=1000)
    #ap.add_argument("-sn", "--start-num", required=False, type=int, default=0)
    ap.add_argument("-et","--export-type", required=False, choices=['os','s3'],help="os for a regular export, s3 for export to S3 bucket")
    ap.add_argument("-ef","--export-folder",required=False,help="Export folder location")
    # import_group = ap.add_mutually_exclusive_group()
    # import_group.add_argument("-i","--import-file-path", required=False,help="A full path to a previously exported zip")
    # import_group.add_argument("-iff","--import-first-file", required=False,help="Imports the first zipfile found in the specified path")
    ap.add_argument("-st", "--source-refresh-token", required=False, help="An API refresh token for the source SDDC")
    # ap.add_argument("-dt", "--dest-refresh-token", required=False, help="An API refresh token for the destination SDDC")
    ap.add_argument("-so","--source-org-id", required=False,help="The source organization ID")
    # ap.add_argument("-do","--dest-org-id", required=False,help="The destination organization ID")
    ap.add_argument("-ss","--source-sddc-id", required=False,help="The source SDDC ID")
    # ap.add_argument("-ds","--dest-sddc-id", required=False,help="The destination SDDC ID")
    ap.add_argument("-s3aid","--aws-s3-export-access-id", required=False,help="AWS Access ID for export to S3")
    ap.add_argument("-s3ase","--aws-s3-export-access-secret", required=False,help="AWS Secret for export to S3")
    ap.add_argument("-s3b","--aws-s3-export-bucket", required=False,help="AWS bucket name for export to S3")
    # ap.add_argument("-rss","--role-sync-source-user-email", required=False, help="The source email address used as a template for syncing roles")
    # ap.add_argument("-rsd","--role-sync-dest-user-emails", required=False, help="The dest email addresses used as a target for syncing roles, formatted as a set")
    ap.add_argument("-t1name", "--t1-api-name", required=False, help="The relative path of the T1 gateway that you want to retrieve.")
    ap.add_argument("-domain", "--nsx-domain-name", required=False, help="The NSX domain name")

    args = ap.parse_args(args)

    if args.operation:
        intent_name = args.operation
    else:
        intent_name = ""

    # if args.import_file_path:
    #     import_file_path = args.import_file_path
    # else:
    #     import_file_path = ""

    # if args.import_first_file:
    #     import_first_file = args.import_first_file
    # else:
    #     import_first_file = ""

    ioObj = VMCImportExport(CONFIG_FILE_PATH,VMC_CONFIG_FILE_PATH, AWS_CONFIG_FILE_PATH)

    # Check environment variables to override the values in vmc.ini
    if ioObj.auth_mode == "token":
        if 'EXP_source_refresh_token' in os.environ:
            ioObj.source_refresh_token = os.environ['EXP_source_refresh_token']
            print('Loaded source refresh token from environment variable')

        if 'EXP_dest_refresh_token' in os.environ:
            ioObj.source_refresh_token = os.environ['EXP_dest_refresh_token']
            print('Loaded destination refresh token from environment variable')   

        if 'EXP_source_org_id' in os.environ:
            ioObj.source_org_id = os.environ['EXP_source_org_id']
            print('Loaded source org ID from environment variable')

        if 'EXP_source_sddc_id' in os.environ:
            ioObj.source_sddc_id = os.environ['EXP_source_sddc_id']
            print('Loaded source SDDC ID from environment variable')

        if 'EXP_dest_org_id' in os.environ:
            ioObj.dest_org_id = os.environ['EXP_dest_org_id']
            print('Loaded dest org ID from environment variable')

        if 'EXP_dest_sddc_id' in os.environ:
            ioObj.dest_sddc_id = os.environ['EXP_dest_sddc_id']
            print('Loaded dest SDDC ID from environment variable')

    if ioObj.auth_mode == "local":
        if 'EXP_srcNSXmgrURL' in os.environ:
            ioObj.srcNSXmgrURL = os.environ['EXP_srcNSXmgrURL']
            print(f"Loaded source NSX manager URL from environment variable: {os.environ['EXP_srcNSXmgrURL']}")

        if 'EXP_srcNSXmgrUsername' in os.environ:
            ioObj.srcNSXmgrUsername = os.environ['EXP_srcNSXmgrUsername']
            print(f"Loaded source NSX manager username from environment variable: {os.environ['EXP_srcNSXmgrUsername']}")

        if 'EXP_srcNSXmgrPassword' in os.environ:
            ioObj.srcNSXmgrPassword = os.environ['EXP_srcNSXmgrPassword']
            print(f"Loaded source NSX manager password from environment variable: {'*' * len(os.environ['EXP_srcNSXmgrPassword'])}")
    else:
        print(f"Not loading local NSX environment variables because auth_mode={ioObj.auth_mode}")

    # Check the optional command-line arguments to override the values in vmc.ini
    if args.source_refresh_token:
        ioObj.source_refresh_token = args.source_refresh_token
        print('Loaded source refresh token from command line')

    if args.export_type:
        ioObj.export_type = args.export_type
        print('Loaded export mode from command line')

    if args.export_folder:
        ioObj.export_folder = args.export_folder
        ioObj.export_path = Path(ioObj.export_folder)
        print('Loaded export folder from command line')

    # if args.dest_refresh_token:
    #     ioObj.dest_refresh_token = args.dest_refresh_token
    #     print('Loaded dest refresh token from command line')

    if args.source_org_id:
        ioObj.source_org_id = args.source_org_id
        print('Loaded source org ID from command line')

    # if args.dest_org_id:
    #     ioObj.dest_org_id = args.dest_org_id
    #     print('Loaded dest org ID from command line')

    if args.source_sddc_id:
        ioObj.source_sddc_id = args.source_sddc_id
        print('Loaded source SDDC ID from command line')

    # if args.dest_sddc_id:
    #     ioObj.dest_sddc_id = args.dest_sddc_id
    #     print('Loaded dest SDDC ID from command line')

    if args.aws_s3_export_access_id:
        ioObj.aws_s3_export_access_id = args.aws_s3_export_access_id
        print('Loaded AWS S3 export Access ID from command line')

    if args.aws_s3_export_access_secret:
        ioObj.aws_s3_export_access_secret = args.aws_s3_export_access_secret
        print('Loaded AWS S3 export Secret from command line')

    if args.aws_s3_export_bucket:
        ioObj.aws_s3_export_bucket = args.aws_s3_export_bucket
        print('Loaded AWS S3 export bucket from command line')

    # if args.role_sync_source_user_email:
    #     ioObj.RoleSyncSourceUserEmail = args.role_sync_source_user_email
    #     print('Loaded role sync source user email from command line')

    # if args.role_sync_dest_user_emails:
    #     ioObj.RoleSyncDestUserEmails = args.role_sync_dest_user_emails.split(',')
    #     print('Loaded role sync dest user emails from command line')

    if args.t1_api_name:
        ioObj.t1_api_name = args.t1_api_name
        print(f'Loaded CGW API name from command line: {args.t1_api_name}')

    if args.nsx_domain_name:
        ioObj.nsx_domain_name = args.nsx_domain_name
        print(f'Loaded NSX domain name from command line: {args.nsx_domain_name}')

    print(f"Current authentication mode: {ioObj.auth_mode}")

    # If env variables are not populated, prompt user for input
    if ioObj.auth_mode == "token":
        while ioObj.source_refresh_token == "":
            print("Source refresh token was not found in the environment variables.")
            ioObj.source_refresh_token = input("Enter source refresh token: ")

        while ioObj.source_org_id == "":
            print("Source org_id was not found in the environment variables.")
            ioObj.source_org_id = input("Enter source org ID: ")

        while ioObj.source_sddc_id == "":
            print("Source sddc_id was not found in the environment variables.")
            ioObj.source_sddc_id = input("Enter source sddc ID: ")                     

    if ioObj.auth_mode == "local":
        while ioObj.srcNSXmgrURL == "":
            print("Source NSX manager URL was not found in the environment variables.")
            ioObj.srcNSXmgrURL = input("Enter source NSX manager URL: ")

        while ioObj.srcNSXmgrUsername == "":
            print("Source NSX manager username was not found in the environment variables.")
            ioObj.srcNSXmgrUsername = input("Enter source NSX manager username: ")

        while ioObj.srcNSXmgrPassword == "":
            print("Source NSX manager password was not found in the environment variables.")
            ioObj.srcNSXmgrPassword = maskpass.askpass(prompt="Enter source NSX manager password: ", mask="*")

    # Variable added so we can have an intent run multiple operations
    no_intent_found = True

    ################################ Warning ######################################
    ## Changing the order of ifchecks on intent name can have unexpected          #
    ## side effects. If you want to do both an export and import in a single      #
    ## run of the script, it only makes sense to run the export first.            #
    ## Moving the import section above the export section would break this intent #
    ###############################################################################

    if intent_name == "rolesync":
        no_intent_found = False
        ioObj.vmc_auth.getAccessToken(ioObj.source_refresh_token)
        if (ioObj.vmc_auth.access_token == ""):
            print("Unable to retrieve source access token. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()
        print (f'Looking up template user {ioObj.RoleSyncSourceUserEmail}')
        retval = ioObj.searchOrgUser(ioObj.source_org_id,ioObj.RoleSyncSourceUserEmail)
        if retval is False:
            print("API error searching for source object")
        else:
            if len(ioObj.user_search_results_json['results']) > 0:
                template_user_json = ioObj.user_search_results_json['results'][0]
                template_user_roles = template_user_json['serviceRoles']
                retval = ioObj.convertServiceRolePayload(template_user_roles)
                payload = {}
                payload = ioObj.convertedServiceRolePayload
                ioObj.vmc_auth.getAccessToken(ioObj.dest_refresh_token)
                if (ioObj.vmc_auth.access_token == ""):
                    print("Unable to retrieve source access token. Server response:{}".format(ioObj.lastJSONResponse))
                    sys.exit()
                if ioObj.import_mode == "live":
                    if ioObj.import_mode_live_warning is True:
                        continue_live = yes_or_no("Script is running in live mode - changes will be made to your destination SDDC. Continue in live mode?")
                        if continue_live is False:
                            ioObj.import_mode = "test"
                            print("Import mode set to test")
                        else:
                            print("Live import will proceed")
                retval = ioObj.syncRolesToDestinationUsers()
            else:
                print('No source object found.')

    if intent_name == "export-vcenter":
        no_intent_found = False
        if ioObj.export_vcenter_folders:
            srcvc = vcenter.vCenter(ioObj.srcvCenterURL,ioObj.srcvCenterUsername,ioObj.srcvCenterPassword,ioObj.srcvCenterSSLVerify)
            srcdc = srcvc.get_datacenter(ioObj.srcvCenterDatacenter)
            print('Exporting folder paths from source vCenter...')
            srcdc.export_folder_paths(ioObj.export_path / ioObj.vcenter_folders_filename)
            print('Export complete.')

    if intent_name == "testbed":
        no_intent_found = False
        if args.test_name:
            test_name = args.test_name
        else:
            print('test-name argument is required')
            sys.exit()

        print('Testbed mode:',ioObj.import_mode)

        ioObj.vmc_auth.getAccessToken(ioObj.dest_refresh_token)
        if (ioObj.vmc_auth.access_token == ""):
            print("Unable to retrieve access token. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        ioObj.getNSXTproxy(ioObj.dest_org_id,ioObj.dest_sddc_id)
        if (ioObj.proxy_url == ""):
            print("Unable to retrieve proxy. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        retval = ioObj.loadDestOrgData()
        if retval == False:
            print("Unable to load Dest Org Data. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        retval = ioObj.loadDestSDDCData()
        if retval == False:
            print("Unable to load Dest SDDC Data. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        if ioObj.dest_sddc_state != 'READY':
            print("Unable to import, expected SDDC",ioObj.dest_sddc_name,"state READY, found state", ioObj.dest_sddc_state)
            sys.exit()

        print(f'Managing testbed objects for {ioObj.dest_org_display_name} ({ioObj.dest_org_id}), SDDC {ioObj.dest_sddc_name} ({ioObj.dest_sddc_id}), SDDC version {ioObj.dest_sddc_version}')
        for t in test_name:
            if t == 'create-cgw-groups':
                if args.num_objects < 1:
                    print('num-objects argument must be a positive integer.')
                elif args.start_num < 0:
                    print('start-num argument must be a positive integer or 0')
                else:
                    print(f'Generating a testbed of {args.num_objects} CGW groups')
                    for i in range(args.start_num,args.num_objects+args.start_num):
                        grp_name = f'cgw-test-group-{i:04}'
                        print(grp_name)
                        retval = ioObj.createSDDCCGWGroup(grp_name, ioObj.findRandomTestbedVM())

            if t == 'delete-all-cgw-groups':
                print('Deleting all CGW groups...')
                if ioObj.import_mode == 'live':
                    if ioObj.import_mode_live_warning:
                        continue_live = yes_or_no("WARNING - Script is running in live mode - ALL CGW GROUPS WILL BE DELETED. Continue in live mode?")
                        if continue_live is False:
                            ioObj.import_mode = 'test'

                retval = ioObj.deleteAllSDDCCGWGroups()

            if t == 'delete-cgw-groups':
                if args.num_objects < 1:
                    print('num-objects argument must be a positive integer.')
                elif args.start_num < 0:
                    print('start-num argument must be a positive integer or 0')
                else:
                    print(f'Deleting testbed of {args.num_objects} CGW groups')
                    if ioObj.import_mode == 'live':
                        if ioObj.import_mode_live_warning:
                            continue_live = yes_or_no("WARNING - Script is running in live mode - CGW groups will be deleted. Continue in live mode?")
                            if continue_live is False:
                                ioObj.import_mode = 'test'

                    for i in range(args.start_num,args.num_objects+args.start_num):
                        grp_name = f'cgw-test-group-{i:04}'
                        retval = ioObj.deleteSDDCCGWGroup(grp_name)

    if intent_name == "import-vcenter":
        no_intent_found = False
        if ioObj.import_vcenter_folders:
            destvc = vcenter.vCenter(ioObj.destvCenterURL,ioObj.destvCenterUsername,ioObj.destvCenterPassword,ioObj.destvCenterSSLVerify)
            destdc = destvc.get_datacenter(ioObj.destvCenterDatacenter)
            print('Importing folder paths into destination vCenter...')
            if ioObj.import_mode == 'live':
                test_mode = False
            else:
                test_mode = True
            destdc.import_folder_paths(ioObj.import_path / ioObj.vcenter_folders_filename,test_mode=test_mode)
            print('Import complete.')

    if intent_name == "export-nsx":
        no_intent_found = False
        print("Beginning on-prem export...")

        print("Beginning Services export...")
        retval = ioObj.exportOnPremServices()
        if retval is True:
            print("Services exported.")
        else:
            print("Services export error: {}".format(ioObj.lastJSONResponse))

        retval = ioObj.exportOnPremGroups()
        if retval is True:
                print("Groups exported.")
        else:
                print("Groups export error: {}".format(ioObj.lastJSONResponse))

        retval = ioObj.exportOnPremDFWRule()
        if retval is True:
                print("DFW rules exported.")
        else:
                print("DFW rules error: {}".format(ioObj.lastJSONResponse))

        print("Thanks for using the export function")

    if intent_name == "import-nsx":
        no_intent_found = False
        print('Import mode:', ioObj.import_mode)

        ioObj.vmc_auth.getAccessToken(ioObj.dest_refresh_token)
        if (ioObj.vmc_auth.access_token == ""):
            print("Unable to retrieve access token. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        ioObj.getNSXTproxy(ioObj.dest_org_id,ioObj.dest_sddc_id)
        if (ioObj.proxy_url == ""):
            print("Unable to retrieve proxy. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        retval = ioObj.loadDestOrgData()
        if retval == False:
            print("Unable to load Dest Org Data. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit() 

        retval = ioObj.loadDestSDDCData()
        if retval == False:
            print("Unable to load Dest SDDC Data. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        if ioObj.dest_sddc_state != 'READY':
            print("Unable to import, expected SDDC",ioObj.dest_sddc_name,"state READY, found state", ioObj.dest_sddc_state)
            sys.exit()

        print(f'Importing data into org {ioObj.dest_org_display_name} ({ioObj.dest_org_id}), SDDC {ioObj.dest_sddc_name} ({ioObj.dest_sddc_id}), SDDC version {ioObj.dest_sddc_version}')
        #print(getSDDCS(ioObj.strProdURL,ioObj.dest_org_id, ioObj.access_token))

        if ioObj.import_mode == "live":
            if ioObj.import_mode_live_warning is True:
                continue_live = yes_or_no("Script is running in live mode - changes will be made to your destination SDDC. Continue in live mode?")
                if continue_live is False:
                    ioObj.import_mode = "test"
                    print("Import mode set to test")
                else:
                    print("Live import will proceed")

        print("Beginning Services import...")
        ioObj.importOnPremServices()


        print("Beginning Group import...")
        retval = ioObj.importOnPremGroup()

        if ioObj.dfw_import is True:
            print("Beginning DFW import...")
            ioObj.importOnPremDFWRule()

        print("Import has been concluded. Thank you for using Import/Export for NSX.")

    if intent_name == "check-vmc-ini":
        no_intent_found = False

        ioObj.vmc_auth.getAccessToken(ioObj.source_refresh_token)
        if (ioObj.vmc_auth.access_token == ""):
            print("Unable to retrieve access token. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        ioObj.getNSXTproxy(ioObj.source_org_id,ioObj.source_sddc_id)
        if (ioObj.proxy_url == ""):
            print("Unable to retrieve proxy. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        retval = ioObj.loadSourceOrgData()
        if retval == False:
            print("Unable to load Source Org Data. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        retval = ioObj.loadSourceSDDCData()
        if retval == False:
            print("Unable to load Source SDDC Data. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()
        
        retval = ioObj.connectNSX()
        if retval == False:
            print(f'Unable to connect to Source NSX-T Manager.')
            sys.exit(1)

        print(f'Export configuration: Org {ioObj.source_org_display_name} ({ioObj.source_org_id}), SDDC {ioObj.source_sddc_name} ({ioObj.source_sddc_id}), SDDC version {ioObj.source_sddc_version}, NSX-T Manager reachable.')

        ioObj.vmc_auth.getAccessToken(ioObj.dest_refresh_token)
        if (ioObj.vmc_auth.access_token == ""):
            print("Unable to retrieve access token. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        ioObj.getNSXTproxy(ioObj.dest_org_id,ioObj.dest_sddc_id)
        if (ioObj.proxy_url == ""):
            print("Unable to retrieve proxy. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        retval = ioObj.loadDestOrgData()
        if retval == False:
            print("Unable to load Dest Org Data. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        retval = ioObj.loadDestSDDCData()
        if retval == False:
            print("Unable to load Dest SDDC Data. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()
        
        retval = ioObj.connectNSX()
        if retval == False:
            print(f'Unable to connect to Destination NSX-T Manager.')
            sys.exit(1)

        print(f'Import configuration: Org {ioObj.dest_org_display_name} ({ioObj.dest_org_id}), SDDC {ioObj.dest_sddc_name} ({ioObj.dest_sddc_id}), SDDC version {ioObj.dest_sddc_version}, NSX-T Manager reachable.')


    if intent_name == "export" or intent_name == "export-import" or intent_name == "list-t1s" or intent_name == "list-domains":
        no_intent_found = False

        if ioObj.auth_mode == "token":

            ioObj.vmc_auth.getAccessToken(ioObj.source_refresh_token)
        
            if (ioObj.vmc_auth.access_token == ""):
                print("Unable to retrieve access token. Server response:{}".format(ioObj.lastJSONResponse))
                sys.exit()

            ioObj.getNSXTproxy(ioObj.source_org_id,ioObj.source_sddc_id)
            if (ioObj.proxy_url == ""):
                print("Unable to retrieve proxy. Server response:{}".format(ioObj.lastJSONResponse))
                sys.exit()

            retval = ioObj.loadSourceOrgData()
            if retval == False:
                print("Unable to load Source Org Data. Server response:{}".format(ioObj.lastJSONResponse))
                sys.exit()

            retval = ioObj.loadSourceSDDCData()
            if retval == False:
                print("Unable to load Source SDDC Data. Server response:{}".format(ioObj.lastJSONResponse))
                sys.exit()

            retval = ioObj.loadSourceSDDCNSXData()
            if retval == False:
                print(f'Unable to load Source SDDC NSX Data. Server response: {ioObj.lastJSONResponse}')
                sys.exit()

            print(f'Exporting data from org {ioObj.source_org_display_name} ({ioObj.source_org_id}), SDDC {ioObj.source_sddc_name} ({ioObj.source_sddc_id}), SDDC version {ioObj.source_sddc_version}')
            #print(getSDDCS(ioObj.strProdURL,ioObj.source_org_id, ioObj.access_token))
        else:
            if len(ioObj.srcNSXmgrURL) == 0 or len(ioObj.srcNSXmgrUsername) == 0 or len(ioObj.srcNSXmgrPassword) == 0:
                print("srcNSXmgrURL, srcNSXmgrUsername, and srcNSXmgrPassword are required properties when auth_mode is set to local")
                sys.exit()

            print(f'Exporting data from NSX-T manager {ioObj.srcNSXmgrURL}')
            success = ioObj.source_nsx_mgr_authenticate()
            if success is False:
                print("NSX-T manager authentication failed.")
                sys.exit()

        if intent_name == "list-t1s":
            json_response = ioObj.get_t1_gateways()
            if json_response is None:
                print("Unable to retrieve T1 gateways.")
            elif json_response['result_count'] == 0:
                print("No Tier-1 routers found")
            else:
                if os.name == 'nt':
                    py_cmd = "python"
                else:
                    py_cmd = "python3"

                for t1 in json_response['results']:
                    
                    print(f"T1 name: {t1['display_name']}, path: {t1['path']}, relative path: {t1['relative_path']}, T0 path: {t1['tier0_path']}")
                    print(f"         Export syntax: {py_cmd} {sys.argv[0]} -o export --cgw-api-name \"{t1['relative_path']}\"")

            return
        
        if intent_name == "list-domains":
            json_response = ioObj.get_domains()
            if json_response is None:
                print("Unable to retrieve domains.")

            for domain in json_response:
                print(f"Domain: {domain['id']}, path: {domain['path']}, unique_id: {domain['unique_id']}")
            return

        # Delete old JSON files
        if ioObj.export_type == 'os' and ioObj.export_purge_before_run is True:
            print('Deleting old JSON export files...')
            retval = ioObj.purgeJSONfiles()
            if retval is False:
                stop_script = yes_or_no("Errors purging old files. Continue running script?")
                if stop_script is True:
                    sys.exit()

        # Run all selected export functions

        if ioObj.auth_mode == "token":
            retval = ioObj.exportSourceSDDCData()
            if retval is True:
                print("Source SDDC Info exported.")
            else:
                print("Could not export Source SDDC Info")

        if (ioObj.cgw_export is True) or (ioObj.mgw_export is True) or (ioObj.dfw_export is True):
            print("Beginning Services export...")
            retval = ioObj.exportSDDCServices()
            if retval is True:
                print("SDDC services exported.")
            else:
                print("SDDC services export error: {}".format(ioObj.lastJSONResponse))

            print("Beginning Tags export...")
            retval = ioObj.exportSDDCTags()
            if retval is True:
                print("SDDC tags exported.")
            else:
                print("SDDC tags export error: {}".format(ioObj.lastJSONResponse))

            print("Beginning Domains export...")
            retval = ioObj.export_domains()
            if retval is True:
                print("Domains exported.")
            else:
                print("Domains export error: {}".format(ioObj.lastJSONResponse))

            print("Beginning Gateway Policies export...")
            retval = ioObj.export_gateway_policies()
            if retval is True:
                print("Gateway Policies exported.")
            else:
                print("Gateway policy export error: {}".format(ioObj.lastJSONResponse))

            print("Beginning VMs export...")
            retval = ioObj.exportSDDCVMs()
            if retval is True:
                print("SDDC VMs exported.")
            else:
                print("SDDC VMs export error: {}".format(ioObj.lastJSONResponse))

            print("Beginning VM VIFs export...")
            retval = ioObj.exportSDDCVMVIFs()
            if retval is True:
                print("SDDC VM VIFs exported.")
            else:
                print("SDDC VM VIFs export error: {}".format(ioObj.lastJSONResponse))

        if ioObj.mgw_export is True:
            print("Beginning MGW export...")
            retval = ioObj.exportSDDCMGWGroups()
            if retval is True:
                print("MGW groups exported.")
            else:
                print("MGW groups export error: {}".format(ioObj.lastJSONResponse))

            retval = ioObj.exportSDDCMGWRule()
            if retval is True:
                print("MGW rules exported.")
            else:
                print("MGW export error: {}".format(ioObj.lastJSONResponse))
        else:
            print("MGW export skipped.")

        if ioObj.cgw_export is True:
            print("Beginning CGW export...")
            retval = ioObj.exportSDDCCGWGroups()
            if retval is True:
                print("CGW groups exported.")
            else:
                print("CGW groups export error: {}".format(ioObj.lastJSONResponse))

            if ioObj.nsx_endpoint_type == "vmc":
                retval = ioObj.exportSDDCCGWRule()
                if retval is True:
                    print("CGW rules exported.")
                else:
                    print("CGW export error: {}".format(ioObj.lastJSONResponse))    
            else:
                policy_json = ioObj.get_gateway_policies()
                if policy_json:
                    for policy in policy_json:
                        print(f"Exporting policy {policy['id']}")
                        retval = ioObj.exportSDDCCGWRule(gateway_policy_id=policy['id'])
                else:
                    print("No gateway policies were found, unable to export firewall rules.")

                retval = ioObj.export_t1_gateways()
                if retval is True:
                    print("T1 gateways exported.")
                else:
                    print("T1 gateway export error: {}".format(ioObj.lastJSONResponse))  

        else:
            print("CGW export skipped.")

        if ioObj.mcgw_export is True and ioObj.nsx_endpoint_type == "vmc":
            print("Beginning Multi-T1 CGW export...")
            retval = ioObj.export_mcgw_config()
            if retval is True:
                print("Multi-T1 CGW Config exported")
            else:
                print(f'Multi-T1 CGW export error: {ioObj.lastJSONResponse}')
        else:
            print(f"Multi-T1 CGW export skipped: mcgw_export={ioObj.mcgw_export}, auth_mode={ioObj.auth_mode}")

        if ioObj.mcgw_static_routes_export is True and ioObj.nsx_endpoint_type == "vmc":
            print("Beginning Multi-T1 Static Routes Export")
            retval = ioObj.export_mcgw_static_routes()
            if retval is True:
                print("Multi-T1 Static Routes exported")
            else:
                print(f"Multi-T1 static routes export error: {ioObj.lastJSONResponse}")
        else:
            print(f"Multi-T1 static routes export skipped: mcgw_static_routes_export={ioObj.mcgw_static_routes_export}, auth_mode={ioObj.auth_mode}")

        if ioObj.mcgw_fw_export is True and ioObj.nsx_endpoint_type == "vmc":
            print("Beginning Multi-T1 North/South Firewall Policy and Rule Export")
            retval = ioObj.export_mcgw_fw()

            if retval is True:
                print("Multi-T1 FW Policy and Rules exported")
            else:
                print(f"Multi-T1 FW Policy and Rules export error: {ioObj.lastJSONResponse}")
        else:
            print(f"Multi-T1 Firewall Policy and Rules export skipped: mcgw_fw_export={ioObj.mcgw_fw_export}, auth_mode={ioObj.auth_mode}")

        if ioObj.mpl_export is True and ioObj.nsx_endpoint_type == "vmc":
            print("Beginning Connected VPC Managed Prefix List export")
            retval = ioObj.export_mpl()
            if retval is True:
                print("Connected VPC Managed Prefix List settings exported")
            else:
                print(f'Connected VPC Managed Prefix List export error: {ioObj.lastJSONResponse}')
        else:
            print(f"Connected VPC Managed Prefix List export skipped: mpl_export={ioObj.mpl_export}, auth_mode={ioObj.auth_mode}")

        if ioObj.ral_export is True and ioObj.nsx_endpoint_type == "vmc":
            print('Beginning Route Aggegration list export')
            retval = ioObj.export_ral()
            if retval is True:
                print("SDDC Route Aggregation list exported")
            else:
                print(f"SDDC Route Aggregation list export error: {ioObj.lastJSONResponse}")
        else:
            print(f"SDDC Route Aggregation list export skipped: ral_export={ioObj.ral_export}, auth_mode={ioObj.auth_mode}")

        if ioObj.route_config_export is True and ioObj.nsx_endpoint_type == "vmc":
            print('Beginning SDDC route configuration export')
            retval = ioObj.export_route_config()
            if retval is True:
                print("SDDC Route Configuration exported")
            else:
                print(f"SDDC Route Configuration export error: {ioObj.lastJSONResponse}")
        else:
            print(f"SDDC Route Configuration export skipped: route_config_export={ioObj.route_config_export}, auth_mode={ioObj.auth_mode}")

        if ioObj.network_export is True:
            print("Beginning network segments export...")
            retval = ioObj.exportSDDCCGWnetworks()
            if retval is True:
                print("Networks exported.")
            else:
                print("Networks export error: {}".format(ioObj.lastJSONResponse))
        else:
            print("Network segment export skipped.")
        
        if ioObj.flex_segment_export is True  and ioObj.nsx_endpoint_type == "vmc":
            print("Beginning flexible segment export...")
            retval = ioObj.export_flexible_segments()
            retval2 = ioObj.export_flexible_segment_disc_bindings()
            if retval is True and retval2 is True:
                print("Flexible segment and segment discovery bindings exported.")
            else:
                print(f"Flexible segment export error: {ioObj.lastJSONResponse}")
        else:
            print(f"Flexible segment and segment discovery profile bindings export skipped: flex_segment_export={ioObj.flex_segment_export}, auth_mode={ioObj.auth_mode}")

        if ioObj.dfw_export is True:
            print("Beginning DFW export...")
            retval = ioObj.exportSDDCDFWRule()
            if retval is True:
                print("DFW rules exported.")
            else:
                print("DFW rules error: {}".format(ioObj.lastJSONResponse))
        else:
            print("DFW rules export skipped.")

        if ioObj.public_export is True and ioObj.nsx_endpoint_type == "vmc":
            print("Beginning Public IP export...")
            retval = ioObj.exportSDDCListPublicIP()
            if retval is True:
                print("Public IP exported.")
            else:
                print("Public IP export error: {}".format(ioObj.lastJSONResponse))
        else:
            print(f"Public IP export skipped. nsx_endpoint_type={ioObj.nsx_endpoint_type}")

        if ioObj.nat_export is True and ioObj.nsx_endpoint_type == "vmc":
            print("Beginning NAT export...")
            retval = ioObj.exportSDDCNat()
            if retval is True:
                print("NAT rules exported.")
            else:
                print("NAT rules export error: {}".format(ioObj.lastJSONResponse))
        else:
            print("NAT rules export skipped.")

        if ioObj.nsx_adv_fw_export is True and ioObj.nsx_endpoint_type == "vmc":
            if (ioObj.cgw_export is False or ioObj.network_export is False):
                print("NSX Advanced Firewall export is enabled, but CGW export is not.")
                print("Please enable export of Compute Gateway settings to capture all CGW Groups AND Segments, else import of NSX AF settings and rules may fail.")
            print("Beginning NSX Advanced Firewall export...")
            retval = ioObj.export_advanced_firewall()
            if retval is True:
                print("NSX Advanced Firewall exported.")
            else:
                print("NSX Advanced Firewall export error: {}.".format(ioObj.lastJSONResponse))
        else:
            print(f"NSX Advanced Firewall export skipped: nsx_adv_fw_export={ioObj.nsx_adv_fw_export}, auth_mode={ioObj.auth_mode}")


        if ioObj.service_access_export is True and ioObj.nsx_endpoint_type == "vmc":
            print("Beginning Service Access export...")
            retval = ioObj.exportServiceAccess()
            if retval is True:
                print("Service access exported.")
            else:
                print("Service access export error: {}.".format(ioObj.lastJSONResponse))
        else:
            print(f"Service access export skipped: nsx_adv_fw_export={ioObj.service_access_export}, auth_mode={ioObj.auth_mode}")

        if ioObj.vpn_export is True and ioObj.nsx_endpoint_type == "vmc":
            print("Beginning VPN export...")
            retval = ioObj.exportVPN()
            if retval is True:
                print("VPN exported.")
            else:
                print("VPN export error.")
        else:
            print(f"VPN export skipped: vpn_export={ioObj.vpn_export}, auth_mode={ioObj.auth_mode}")

        if ioObj.tier1_vpn_export is True and ioObj.nsx_endpoint_type == "vmc":
            print("Beginning export of Tier-1 VPNs")
            retval = ioObj.export_tier1_vpn()
            if retval is True:
                print("Tier-1 VPNs exported")
            else:
                print("Tier-1 VPN export error")
        else:
            print(f"Tier-1 VPN export skipped: tier1_vpn_export={ioObj.tier1_vpn_export}, auth_mode={ioObj.auth_mode}")
        
        if ioObj.nsx_l7_fqdn_export is True and ioObj.nsx_endpoint_type == "vmc":
            print('Beginning NSX Layer 7 FQDN profile export')
            retval = ioObj.export_fqdn_attribute()
            if retval is True:
                print('FQDN profiles exported')
            else:
                print('FQDN profile export failed')
        else:
            print(f'FQDN profile export skipped: nsx_l7_fqdn_export={ioObj.nsx_l7_fqdn_export}, auth_mode={ioObj.auth_mode} ')
        
        if ioObj.nsx_l7_context_profile_export is True and ioObj.nsx_endpoint_type == "vmc":
            print('Beginning NSX Layer 7 context profile export')
            retval - ioObj.export_l7_cp()
            if retval is True:
                print('NSX L7 Context Profile export successful')
            else:
                print('NSX L7 Context Profile export error')
        else:
            print(f'NSX L7 Context Profile export skipped: nsx_l7_context_profile_export={ioObj.nsx_l7_context_profile_export}, auth_mode={ioObj.auth_mode} ')

        if ioObj.export_history is True:
            retval = ioObj.zipJSONfiles()
            if retval is False:
                print('JSON files were not successfully zipped.')
            else:
                print('JSON files successfully zipped into', ioObj.export_zip_name)
                if ioObj.export_type == 's3':
                    print('Uploading to s3 bucket',ioObj.aws_s3_export_bucket)
                    if len(ioObj.aws_s3_export_access_id) == 0:
                        #Blank access ID - running in Lambda mode, do not pass the key and secret, the Lambda role will grant access to the bucket
                        s3 = boto3.client('s3')
                    else:
                        s3 = boto3.client('s3',aws_access_key_id=ioObj.aws_s3_export_access_id,aws_secret_access_key=ioObj.aws_s3_export_access_secret)
                    try:
                        fname = ioObj.export_folder + '/' + ioObj.export_zip_name
                        with open(fname, "rb") as f:
                            response = s3.upload_fileobj(f,ioObj.aws_s3_export_bucket,ioObj.export_zip_name)
                        print('S3 upload successful')
                    except Exception as e:
                        print('Failed to upload file.')
                        print(e)

                if ioObj.export_purge_after_zip == True:
                    print('export_purge_after_zip flag is true, deleting JSON files')
                    retval = ioObj.purgeJSONfiles()
                    if retval is False:
                        print('Unable to purge JSON files.')

            retval = ioObj.purgeJSONzipfiles()
            if retval is True:
                print('Zipfile maintenance completed with no errors.')

        print("Export has been concluded. Thank you for using Import/Export for NSX.")

    if intent_name == "import" or intent_name == "export-import":
        no_intent_found = False

        # User passed a folder name to use as the import source
        # Find the first zipfile in the folder and save it to import_file_path
        # This will make the program run just as if the calling function had passed in a full zipfile
        # path via import_file_path

        if ioObj.nsx_endpoint_type == "nsx":
            print("Import is only supported for VMware Cloud on AWS")
            return

        if ioObj.sync_mode is True:
            if ioObj.public_import is True or ioObj.nat_import is True:
                print("When sync mode is enabled, public IP import and NAT import should be disabled. Syncing public IPs and NAT configuration is not currently supported. If you are importing into an empty SDDC, it is safe to continue. If your destination SDDC has existing public IPs and NATs, you should cancel the import.")
                stop_script = yes_or_no("Do you want to cancel the import?")
                if stop_script is True:
                    print("You can disable public IP and NAT imports for this single run of the import process. You will still need to change config.ini for any future imports.")
                    stop_script = yes_or_no("Do you want to disable public IP and NAT imports? Answering yes will disable those features and continue with the import. Answering no will stop the script.")
                    if stop_script is True:
                        print("Disabling public IP and NAT imports...")
                        ioObj.public_import = False
                        ioObj.nat_import = False
                    else:
                        sys.exit()

        # if import_first_file != "":
        #     files = glob.glob(import_first_file + '/*.zip')
        #     if len(files) > 0:
        #         import_file_path = files[0]
        #         print('Found',import_file_path,'in folder.')
        #     else:
        #         print('Found no zipfiles in',import_first_file)

        # User passed a zipfile path to use as the import source
        # if import_file_path != "":
        #     ioObj.import_folder = os.path.dirname(import_file_path)
        #     ioObj.import_path = Path(ioObj.import_folder)
        #     ioObj.export_folder = os.path.dirname(import_file_path) 
        #     ioObj.export_path = Path(ioObj.export_folder)
        #     retval = ioObj.purgeJSONfiles()
        #     if retval is False:
        #         stop_script = yes_or_no("Errors purging old files. Stop running script?")
        #         if stop_script is True:
        #             sys.exit()
        #     retval = ioObj.unzipJSONfiles(import_file_path)
        #     if retval is False:
        #         stop_script = yes_or_no("Could not unzip archive. Stop running script?")
        #         if stop_script is True:
        #             sys.exit()
        #     else:
        #         print('Extracted JSON from zip archive',import_file_path,"- continuing with import.")
        #         print('Loaded import and export folder from command line:', ioObj.import_path )

        print('Import mode:',ioObj.import_mode)

        ioObj.vmc_auth.getAccessToken(ioObj.dest_refresh_token)
        if (ioObj.vmc_auth.access_token == ""):
            print("Unable to retrieve access token. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        ioObj.getNSXTproxy(ioObj.dest_org_id,ioObj.dest_sddc_id)
        if (ioObj.proxy_url == ""):
            print("Unable to retrieve proxy. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        retval = ioObj.loadDestOrgData()
        if retval == False:
            print("Unable to load Dest Org Data. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit() 

        retval = ioObj.loadDestSDDCData()
        if retval == False:
            print("Unable to load Dest SDDC Data. Server response:{}".format(ioObj.lastJSONResponse))
            sys.exit()

        if ioObj.dest_sddc_state != 'READY':
            print("Unable to import, expected SDDC",ioObj.dest_sddc_name,"state READY, found state", ioObj.dest_sddc_state)
            sys.exit()

        print(f'Importing data into org {ioObj.dest_org_display_name} ({ioObj.dest_org_id}), SDDC {ioObj.dest_sddc_name} ({ioObj.dest_sddc_id}), SDDC version {ioObj.dest_sddc_version}')
        #print(getSDDCS(ioObj.strProdURL,ioObj.dest_org_id, ioObj.access_token))

        if ioObj.import_mode == "live":
            if ioObj.import_mode_live_warning is True:
                continue_live = yes_or_no("Script is running in live mode - changes will be made to your destination SDDC. Continue in live mode?")
                if continue_live is False:
                    ioObj.import_mode = "test"
                    print("Import mode set to test")
                else:
                    print("Live import will proceed")

        if ioObj.enable_ipv6 is True:
            ipv6_enable_status = ioObj.enable_sddc_ipv6()
            if ipv6_enable_status is True:
                print(f'IPv6 enabled on {ioObj.dest_sddc_name}')
            else:
                print(f'IPv6 not enabled on {ioObj.dest_sddc_name}')
        else:
            print('IPv6 enablement skipped')
        
        if ioObj.cluster_rename is True:
            print('Cluster rename beginning...')
            ioObj.rename_sddc_clusters()
        else:
            print('Cluster rename skipped')

        if ioObj.network_import is True:
            print("Beginning CGW network import...")
            import_table = ioObj.importCGWNetworks()
            print('Import results:\n')
            print(import_table)
            if ioObj.network_dhcp_static_binding_import is True:
                ioObj.importCGWDHCPStaticBindings()

        if ioObj.services_import is True:
            print("Beginning Services import...")
            ioObj.importSDDCServices()
        else:
            print("Warning - Service import set to False, skipping...")

        if ioObj.compute_groups_import is True:
            print("Beginning Compute Groups import...")
            retval = ioObj.importSDDCCGWGroup()
            if len(ioObj.cgw_groups_import_error_dict) > 0:
                print("Error summary:")
                for key in ioObj.cgw_groups_import_error_dict:
                    print(f'{ioObj.cgw_groups_import_error_dict[key]["display_name"]} ({key}) - {ioObj.cgw_groups_import_error_dict[key]["error_message"]}')
        else:
            print("Warning - Compute Groups import set to False, skipping...")

        if ioObj.management_groups_import is True:
            retval = ioObj.importSDDCMGWGroup()
        else:
            print("Warning - Management Groups import set to False, skipping...")

        if ioObj.cgw_import is True:
            print("Beginning CGW import...")
            if ioObj.services_import is False:
                print('Service import is set to false, this can cause import errors if service objects are missing.')
            if ioObj.compute_groups_import is False:
                print('Compute groups import is set to false, this can cause import errors if compute group objects are missing.')
            ioObj.importSDDCCGWRule()

        if ioObj.mgw_import is True:
            print("Beginning MGW import...")
            if ioObj.services_import is False:
                print('Service import is set to false, this can cause import errors if service objects are missing.')
            if ioObj.management_groups_import is False:
                print('Management groups import is set to false, this can cause import errors if compute group objects are missing.')
            ioObj.importSDDCMGWRule()

        if ioObj.mcgw_import is True:
            print("Beginning Tier-1 Gateway import...")
            if ioObj.services_import is False:
                print('Service import is set to false, this can cause import errors if service objects are missing.')
            if ioObj.compute_groups_import is False:
                print('Compute groups import is set to false, this can cause import errors if compute group objects are missing.')
            ioObj.import_mcgw()

        if ioObj.mcgw_static_routes_import is True:
            print("Beginning Tier-1 Gateway Static Route import...")
            if ioObj.services_import is False:
                print('Service import is set to false, this can cause import errors if service objects are missing.')
            if ioObj.compute_groups_import is False:
                print(
                    'Compute groups import is set to false, this can cause import errors if compute group objects are missing.')
            if ioObj.mcgw_import is False:
                print('Tier-1 Gateway import is set to false, this can cause import error is Tier-1 Gateway objects are missing.')
            ioObj.import_mcgw_static_routes()

        if ioObj.mcgw_fw_import is True:
            print('Beginning Tier-1 Gateway Firewall policy and rules import...')
            if ioObj.services_import is False:
                print('Service import is set to false, this can cause import errors if service objects are missing.')
            if ioObj.compute_groups_import is False:
                print(
                    'Compute groups import is set to false, this can cause import errors if compute group objects are missing.')
            if ioObj.mcgw_import is False:
                print('Tier-1 Gateway import is set to false, this can cause import error is Tier-1 Gateway objects are missing.')
            ioObj.import_mcgw_fw()

        if ioObj.mpl_import is True:
            print("Beginning import of Connected VPC Managed Prefix List configuration")
            ioObj.import_mpl()
        else:
            print("Connected VPC Managed Prefix List import skipped...")

        if ioObj.ral_import is True:
            print('Beginning import of SDDC Route Aggregation Lists...')
            if ioObj.mpl_import is False:
                print("Managed Prefix List import is set to false.  If MPL is not enabled, Route Aggregation lists will not be imported successfully")
            ioObj.import_ral()

        if ioObj.route_config_import is True:
            print('Beginning import of SDDC Route Configurations...')
            if ioObj.mpl_import is False:
                print("Managed Prefix List import is set to false.  If MPL is not enabled, Route Configuration will not be imported successfully")
            if ioObj.ral_import is False:
                print('Import of Route Configurations may be impacted by missing Route Aggregations lists')
            ioObj.import_route_config()
        
        if ioObj.flex_segment_import is True:
            print("Beginning import of flexible segments...")
            import_table = ioObj.import_flex_segments()
            print("Import results:\n")
            print(import_table)
            ioObj.import_flex_seg_disc_binding_map()

        if ioObj.public_import is True:
            print("Beginning Public IP import...")
            ioObj.importSDDCPublicIPs()

        if ioObj.nat_import is True:
            if ioObj.public_import is False:
                print("Public IP import set to false, skipping and disabling NAT import")
                ioObj.nat_import = False
            else:
                print("Beginning NAT import...")
                ioObj.importSDDCNats()

        if ioObj.service_access_import is True:
            print("Beginning Service Access import...")
            ioObj.importServiceAccess()

        if ioObj.vpn_import is True:
            print("Beginning VPN import...")
            ioObj.importVPN()

        if ioObj.nsx_l7_fqdn_import is True:
            print('Beginning import of custom FQDN attributes')
            ioObj.import_fqdn_attributes()
        
        if ioObj.nsx_l7_context_profile_import is True:
            print('Beginning NSX Layer7 Context Profile import')
            ioObj.import_l7_cp()

        if ioObj.nsx_adv_fw_import is True:
            if (ioObj.cgw_import is False):
                print("NSX Advanced Firewall export is enabled, but CGW export is not.")
                print("Please enable export of Compute Gateway settings to capture all CGW Groups and segments, else import of NSX AF settings and rules may fail.")

            print("Beginning NSX advanced firewall import...")
            ioObj.import_advanced_firewall()
        
        if ioObj.dfw_import is True:
            print("Beginning DFW import...")
            if ioObj.services_import is False:
                print('Service import is set to false, this can cause import errors if service objects are missing.')
            if ioObj.compute_groups_import is False:
                print('Compute groups import is set to false, this can cause import errors if compute group objects are missing.')
            ioObj.importSDDCDFWRule()

        print("Import has been concluded. Thank you for using Import/Export for NSX")

    if no_intent_found:
        print("\nWelcome to sddc_import_export!")
        print("\nHere are the currently supported commands: ")
        print("\nTo export your source SDDC to JSON")
        print("export")
        print("\nTo list all Tier-1 gateways: ")
        print("list-t1s")
        print("\nTo list all NSX-T domains: ")
        print("list-domains")


if __name__ == '__main__':
    main(sys.argv[1:])
