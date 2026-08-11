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

For the most reliable demo flow, launch Firefox through the helper script in this folder:

- `launch_project_firefox.ps1`

This avoids the common problem where:

- `kinit` works in PowerShell
- but Firefox was started from a normal desktop shortcut
- so the browser process does not inherit the Kerberos config you just set

Acquire a Kerberos ticket before opening HDFS in Firefox:

- `kdestroy`
- `kinit -l 60d -r 60d demo_hdfs@CUSTOMERDNA.LOCAL`
- `klist`

### Firefox SPNEGO settings

Use Firefox with MIT Kerberos tickets and configure these preferences in `about:config`:

- `network.auth.use-sspi = false`
- `network.negotiate-auth.using-native-gsslib = false`
- `network.negotiate-auth.gsslib = C:\Program Files (x86)\MIT\Kerberos\bin\gssapi32.dll`
- `network.negotiate-auth.trusted-uris = .customerdna.local,namenode.customerdna.local,datanode-1.customerdna.local,datanode-2.customerdna.local,datanode-3.customerdna.local`
- `network.negotiate-auth.delegation-uris = .customerdna.local,namenode.customerdna.local,datanode-1.customerdna.local,datanode-2.customerdna.local,datanode-3.customerdna.local`

Important:

- use hostnames or domains only in these two Firefox values
- do not include `:9871`, `:9865`, or any other port numbers
- use the MIT Kerberos GSS library path exactly as shown above for this demo workstation
- fully close and reopen Firefox after changing the values
- when testing HDFS secure browsing, prefer the dedicated launcher script so Firefox starts in a Kerberos-aware project session
- if HDFS Explorer still shows a previous error, renew the ticket and reload the page in a fresh tab
- if you test with `curl.exe --negotiate` on Windows, remember it may still fall back to NTLM/SSPI and is not the primary validation path for this Firefox-based demo

You can also use the ready reference file in this folder:

- `firefox_spnego_prefs.txt`

### Related browser access

Use hostnames, not raw IPs, for Kerberos-protected HDFS pages:

- `https://namenode.customerdna.local:9871/dfshealth.html`
- `https://namenode.customerdna.local:9871/explorer.html#/`

Recommended startup order for the browser demo:

1. open a fresh PowerShell window
2. run `kdestroy`
3. run `kinit -l 60d -r 60d demo_hdfs@CUSTOMERDNA.LOCAL`
4. verify with `klist`
5. run `.\launch_project_firefox.ps1`
6. inside that dedicated Firefox window, open:
   - `https://namenode.customerdna.local:9871/dfshealth.html`
   - then `https://namenode.customerdna.local:9871/explorer.html#/`

### Notes

- This folder stores client configuration only.
- Do not place passwords in this folder.
- Kerberos user credentials are obtained with `kinit`, not stored in `krb5.ini`.
- In the demo deployment, the browser principal `demo_hdfs@CUSTOMERDNA.LOCAL` is intentionally mapped to the local Hadoop service account `hdfs` for HDFS UI and WebHDFS browsing.
