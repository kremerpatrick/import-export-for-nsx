# 1. Import/Export for NSX

## 1.1. Table of Contents
<!-- TOC -->

- [1. Import/Export for NSX](#1-importexport-for-nsx)
  - [1.1. Table of Contents](#11-table-of-contents)
  - [1.2. Overview](#12-overview)
  - [1.3. Getting Started](#13-getting-started)
    - [1.3.1. Install Python](#131-install-python)
    - [1.3.2. Download code](#132-download-code)
    - [1.3.3. Install Python modules and packages](#133-install-python-modules-and-packages)
    - [1.3.4. Update vmc.ini](#134-update-vmcini)
      - [1.3.4.1 Token mode](#1341-token-mode)
      - [1.3.4.2 Local mode](#1342-local-mode)
      - [1.3.4.3 NSX endpoint type](#1343-nsx-endpoint-type)
    - [1.3.5. Update config.ini](#135-update-configini)
  - [1.4. Running the script](#14-running-the-script)
    - [1.4.1. Export](#141-export)
    - [1.4.2 Export history](#142-export-history)
    - [1.4.9. Running S3 export as a Lambda function](#149-running-s3-export-as-a-lambda-function)

<!-- /TOC -->
## 1.2. Overview

The Import/Export for NSX tool enables customers to export an on-prem or VMware Cloud on AWS NSX configuration to a zipfile. You can use this zipped export as an input for [Amazon Q Developer: Transform for VMware](https://aws.amazon.com/blogs/migration-and-modernization/getting-started-with-amazon-q-developer-transform-for-vmware/), which will automatically convert NSX to AWS native networking constructs.

## 1.3. Getting Started

This product supports VMware Cloud on AWS and on-prem NSX with NSX Local Managers. There is not currently support for Global NSX Managers.

### 1.3.1. Install Python

This tool is dependent on Python3, you can find installation instructions for your operating system in the Python [documentation](https://wiki.python.org/moin/BeginnersGuide/Download). Python 3.10 or greater is required.

### 1.3.2. Download code

If you know git, clone the repo with:

```bash
git clone https://github.com/awslabs/import-export-for-nsx.git
```

If you do not know git, you can download a zipfile from [Releases](https://github.com/awslabs/import-export-for-nsx/releases)

### 1.3.3. Install Python modules and packages

You do not have to do a virtual environment configuration, but it a good practice to follow. Using Python's virtual environment functionality will prevent any libraries used in this program from overwriting versions already on your workstation.

First, change into the code directory that you downloaded/cloned above.

On Mac/Linux, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, run:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```



When you navigate to the nsx_import_export folder, you will find a requirements.txt file that list all your Python packages. They can all be installed by running the following command on Linux/Mac:

```bash
pip3 install -r requirements.txt
```

On Windows, run:

```powershell
python -m pip install -r requirements.txt
```

### 1.3.4. Update vmc.ini

There are two authentication modes set in `vmc.ini`: `auth_mode = token` and `auth_mode = local`.

#### 1.3.4.1 Token mode

Token mode uses a VMware Cloud on AWS API token to authenticate over the Internet to the VMware Cloud on AWS service. It can only be used with VMware Cloud on AWS, and not any other NSX-T endpoint. If you use token mode, you must fill in the refresh token and org/SDDC ID fields in `vmc.ini`.

For token mode, access to the VMware Cloud on AWS API is dependent on a refresh token. To generate a token for your account, see the [Generate API Tokens](https://docs.vmware.com/en/VMware-Cloud-services/services/Using-VMware-Cloud-Services/GUID-E2A3B1C1-E9AD-4B00-A6B6-88D31FCDDF7C.html) help article. Both `VMware Cloud on AWS Administrator` and `VMware Cloud on AWS NSX Cloud Admin` roles are required.

Token mode supports the environment variables `EXP_source_refresh_token`, `EXP_source_org_id`, and `EXP_source_sddc_id`.  If you set these environment variables, you do not need to save them in `vmc.ini`. If you do not want to use the ini file or environment variables, you can leave them blank. The program will prompt you to input the required values when you execute it.

Windows:

```powershell
$env:EXP_source_refresh_token = "xxxxx"
$env:EXP_source_org_id = "xxxxx"
$env:EXP_source_sddc_id = "xxxxx"
```

Linux/Mac:

```bash
EXP_source_refresh_token="xxxxx"
export EXP_source_refresh_token
EXP_source_org_id="xxxxx"
export EXP_source_org_id
EXP_source_sddc_id="xxxxx"
export EXP_source_sddc_id
```

The Org ID and SDDC ID that are required for token mode can be found on the Support tab of your SDDC.

```bash
# Refresh tokens generated in the VMC console. Users have a separate token in each org
source_refresh_token    = XXXXXXXXXXXXXXX
dest_refresh_token      = XXXXXXXXXXXXXXX

# Organization and SDDC IDs are easily found in the support tab of any SDDC
source_org_id           = XXXXXXXXXXXXXXX
source_sddc_id          = XXXXXXXXXXXXXXX
dest_org_id             = XXXXXXXXXXXXXXX
dest_sddc_id            = XXXXXXXXXXXXXXX
```

#### 1.3.4.2 Local mode

You can use local mode to authenticate directly against the NSX-T manager in VMware Cloud on AWS. If you have any other NSX-T deployment, you *must* use local mode. If you have an NSX federation deployed and you use a Global Manager, you cannot use a Global Manager URL with this tool. You will have to retrieve each Local Manager URL and export each one in separate runs of this tool.

If you use local mode, you can fill in the `srcNSXmgrURL`, `srcNSXmgrUsername`, `srcNSXmgrPassword` fields in `vcenter.ini`. If you do not want credentials persisted in plaintext, you can use the methods shown below.

> Note: You must use the *private* URL for direct VMC-A NSX manager access with local mode. Local mode will not work if you use the public NSX URL. The private URL can be found under the `Access NSX Manager via internal network (Private)` section of the NSX Information tab in VMware Cloud on AWS. The URL will be in the following format: `https://nsxmanager.sddc-1.2.3.4.vmwarevmc.com`. Do not include any of the subdirectory paths, webpage names, or query strings - use only the URL including `https://`.


Local mode supports environment variables `EXP_srcNSXmgrURL`, `EXP_srcNSXmgrUsername`, and `EXP_srcNSXmgrPassword`. If you set these environment variables, you do not need to save these values in `vcenter.ini`.

> Note: You can use the read-only NSX `audit` user for export operations when using local mode.

Windows:

```powershell
$env:EXP_srcNSXmgrURL = "https://nsxmgr.fqdn.com"
$env:EXP_srcNSXmgrUsername = "admin"
$env:EXP_srcNSXmgrPassword = "password-for-admin"
```

Linux/Mac:

```bash
EXP_srcNSXmgrURL="https://nsxmgr.fqdn.com"
export EXP_srcNSXmgrURL
EXP_srcNSXmgrUsername="admin"
export EXP_srcNSXmgrUsername
EXP_srcNSXmgrPassword="password-for-admin"
export EXP_srcNSXmgrPassword
```

If you do not want to use environment variables, you can leave them blank. If values are not found in vcenter.ini, and not found in environment variables, the program will then prompt you to enter values as shown below.

```bash
Current authentication mode: local
Source NSX manager URL was not found in the environment variables.
Enter source NSX manager URL: http://nsxmgr.fqdn.com
Source NSX manager username was not found in the environment variables.
Enter source NSX manager username: admin
Source NSX password was not found in the environment variables.
Enter source NSX manager password: ******************************
```

If you use local mode, the only other setting in `vmc.ini` that you need to consider is `nsx_endpoint_type`

#### 1.3.4.3 Global Managers

If you enabled Local Mode as shown in the previous section, you have the option of enabling Global Manager mode. This is only necessary if you are running an [NSX Federation](https://techdocs.broadcom.com/us/en/vmware-cis/nsx/vmware-nsx/4-2/installation-guide/getting-started-with-federation.html) with Global Manager. Local mode with Global Manager supports environment variables `EXP_Global_srcNSXmgrURL`, `EXP_Global_srcNSXmgrUsername`, and `EXP_Global_srcNSXmgrPassword`. If you set these environment variables, you do not need to save these values in `vcenter.ini`.


Windows:

```powershell
$env:EXP_Global_srcNSXmgrURL = "https://globalmgr.fqdn.com"
$env:EXP_Global_srcNSXmgrUsername = "admin"
$env:EXP_Global_srcNSXmgrPassword = "password-for-admin"
```

Linux/Mac:

```bash
EXP_Global_srcNSXmgrURL="https://globalmgr.fqdn.com"
export EXP_Global_srcNSXmgrURL
EXP_Global_srcNSXmgrUsername="admin"
export EXP_Global_srcNSXmgrUsername
EXP_Global_srcNSXmgrPassword="password-for-admin"
export EXP_Global_srcNSXmgrPassword
```

#### 1.3.4.4 NSX endpoint type

`vmc.ini` contains a variable named `nsx_endpoint_type`. It can be set to one of two values:

- vmc - Use this if your NSX-T endpoint is a VMware Cloud on AWS SDDC
- nsx - Use this for any other NSX-T endpoint

### 1.3.5. Update config.ini

Config.ini contains configuration sections for import and export.

There are True/False flags that can be set for each configuration option. The default configuration enables all options.

For example, in this section of the configuration, the compute gateway networks would be exported, but the public IP and NAT associations would not be exported.

```bash
# Export the networks configured on the compute gateway?
network_export  = True
network_export_filename = cgw-networks.json

# Export the list of public IP addresses?
public_export = False
public_export_filename = public.json

# Export the NAT rules, including Public IP addresses?
nat_export = False
nat_export_filename = natrules.json
```

## 1.4. Running the script

### 1.4.1. Export

Export will export your existing configuration from your source SDDC/NSX manager to a set of files that can be subsequently used for import.

For a VMware Cloud on AWS endpoint, run the following command to export:

Windows

```powershell
python ./nsx_import_export.py -o export
```

Linux/Mac

```bash
python3 nsx_import_export.py -o export
```

On MacOS, you may have to specify the Python version in your command. For example, if you install Python 3.12, you might have execute `python3.12` instead of `python3`, as `python3` may default to the MacOS default of Python 3.8. You can resolve this by either typing the command as:

 ```bash
 python3 nsx_import_export.py -o export
 ```

 Alternatively, you could create an alias in your `~/.profile` and use the alias as your command.

 ```bash
 # ~/.profile
 alias python='python3.1.2'
 ```

If all of the export options are enabled, this will export a set of files:

- Services.json
- cgw_groups.json
- cgw-networks.json
- cgw.json
- dfw_details.json
- dfw.json
- dhcp-static-bindings.json
- flex_seg_disc_prof.json
- flex_seg.json
- mcgw_fw.json
- mcgw_static_routes.json
- mcgw.json
- mgw_groups.json
- mgw.json
- mpl.json
- natrules.json
  nsx_adv_fw_policies.json
- nsx_adv_fw_profiles.json
- nsx_adv_fw_rules.json
- nsx_adv_fw_settings.json
- nsx_adv_fw_sigs.json
- public_ip_old_new.json
- public.json
- ral.json
- route_config.json
- s3-service_access.json
- sddc_info.json
- service_access.json
- services.json
- tags.json
- t1vpn.json
- t1vpn_service.json
- t1vpn_le.json
- vms.json
- vm-vifs.json
- vpn-bgp.json
- vpn-dpd.json
- vpn-ike.json
- vpn-l2.json
- vpn-l3.json
- vpn-local-bgp.json
- vpn-tunnel.json

Export is read-only and will not make any changes to your source NSX.

### 1.4.2 Export history

A config.ini flag named 'export_history' allows for the JSON files to be zipped for archival purposes. A related configuration option named 'max_export_history_files' lets you control how many zipped archive files are retained. By default, this is enabled and set to a retention of 1. The zipped file will be in the `/json` folder and in the format `nsx_yyyy-mm-dd_hh-mm-ss_json-export.json`.

### 1.4.9. Running S3 export as a Lambda function

Install all required packages to a folder

```bash
mkdir python_req
cd python_req
pip3 install --target . -r ../requirements.txt
```

Zip python_req and upload it to a Lambda layer

Change export_folder in config.ini to /tmp, because /tmp is the only writable folder in Lambda

Ensure you have configured aws.ini with your S3 bucket settings

Ensure that you have granted the execution role write permissions to your S3 bucket

Add the following files individually to the function code, or zip them up and upload all at once:

- config_ini/*
- invoke_lambda.py
- nsx_import_export.py
- VMCImportExport.py

Change the Handler runtime settings to invoke_lambda.lambda_handler

Execute your Lambda function. Although it is possible to configure values in the config_ini files that you upload to the function code, it might be preferable to pass the required values via command line argument. See [invoke_lambda.py](invoke_lambda.py) for an example.
