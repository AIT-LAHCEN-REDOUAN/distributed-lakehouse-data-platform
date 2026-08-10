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

Acquire a Kerberos ticket before opening HDFS in Firefox:

- `kdestroy`
- `kinit -l 60d -r 60d demo_hdfs@CUSTOMERDNA.LOCAL`
- `klist`

### Firefox SPNEGO settings

Use Firefox with MIT Kerberos tickets and configure these preferences in `about:config`:

- `network.auth.use-sspi = false`
- `network.negotiate-auth.trusted-uris = .customerdna.local,namenode.customerdna.local,datanode-1.customerdna.local,datanode-2.customerdna.local,datanode-3.customerdna.local`
- `network.negotiate-auth.delegation-uris = .customerdna.local,namenode.customerdna.local,datanode-1.customerdna.local,datanode-2.customerdna.local,datanode-3.customerdna.local`

Important:

- use hostnames or domains only in these two Firefox values
- do not include `:9871`, `:9865`, or any other port numbers
- fully close and reopen Firefox after changing the values
- if HDFS Explorer still shows a previous error, renew the ticket and reload the page in a fresh tab

You can also use the ready reference file in this folder:

- `firefox_spnego_prefs.txt`

### Related browser access

Use hostnames, not raw IPs, for Kerberos-protected HDFS pages:

- `https://namenode.customerdna.local:9871/dfshealth.html`
- `https://namenode.customerdna.local:9871/explorer.html#/`

### Notes

- This folder stores client configuration only.
- Do not place passwords in this folder.
- Kerberos user credentials are obtained with `kinit`, not stored in `krb5.ini`.
- In the demo deployment, the browser principal `demo_hdfs@CUSTOMERDNA.LOCAL` is intentionally mapped to the local Hadoop service account `hdfs` for HDFS UI and WebHDFS browsing.
