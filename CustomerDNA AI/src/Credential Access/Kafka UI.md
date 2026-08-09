# Kafka UI

- URL: `https://localhost:18085`
- Application login: `Not enabled in the demo`
- Password: `Not applicable`

Notes:

- Access is limited by where the control plane is hosted.
- This UI is intended for demo supervision of brokers, topics, and message flow.
- The local TLS gateway uses an internal demo certificate authority, so the browser may show a certificate warning on first access.
- If the startup script remaps the port because `18085` is busy, read the active value from `control_plane_pc/runtime/compose.generated.env`.
