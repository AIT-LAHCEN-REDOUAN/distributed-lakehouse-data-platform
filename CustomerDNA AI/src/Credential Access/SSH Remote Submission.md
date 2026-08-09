# SSH Remote Submission

- Remote host: `10.10.252.12`
- Remote user: `redouan`
- Private key path inside control-plane containers: `/opt/customerdna/.ssh/id_ed25519`
- Local source file: `src/deployments/distributed_pc_control_plane/control_plane_pc/ssh/id_ed25519`
- Operating-system password: `Not stored in this folder`

Purpose:

- Allows the control plane to submit Spark jobs remotely to VM2
- Keeps Spark driver execution off the unstable local workstation network path
