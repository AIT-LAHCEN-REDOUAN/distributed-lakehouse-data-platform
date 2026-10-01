# Control Plane SSH Key Folder

Place the private key used by Airflow to reach `VM2` for remote Spark submission in this folder.

Expected default file:

- `id_ed25519`

The matching public key must be added to `~/.ssh/authorized_keys` for the deployment user on `VM2`.

Do not commit private keys.
