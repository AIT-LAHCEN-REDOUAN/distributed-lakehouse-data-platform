## Windows Kerberos Client Config

Use this folder as the stable source for the Windows Kerberos client configuration used by the CustomerDNA demo.

### Recommended installer choice

In the MIT Kerberos for Windows setup screen:

- choose `Select a directory`
- select this folder:
  `D:\github\Master_PFE_Project\CustomerDNA AI\src\deployments\distributed_pc_control_plane\windows_kerberos_client`

### Main config file

- `krb5.ini`

### Recommended runtime setup on Windows

If Windows or Firefox does not automatically pick up the file, set:

- `KRB5_CONFIG=D:\github\Master_PFE_Project\CustomerDNA AI\src\deployments\distributed_pc_control_plane\windows_kerberos_client\krb5.ini`

### Related browser access

Use hostnames, not raw IPs, for Kerberos-protected HDFS pages:

- `https://namenode.customerdna.local:9871/dfshealth.html`
- `https://namenode.customerdna.local:9871/explorer.html#/`

### Notes

- This folder stores client configuration only.
- Do not place passwords in this folder.
- Kerberos user credentials are obtained with `kinit`, not stored in `krb5.ini`.
