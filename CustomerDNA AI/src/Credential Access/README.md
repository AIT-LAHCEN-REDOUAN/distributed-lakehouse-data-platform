# CustomerDNA Demo Credential Access

This folder centralizes the demo credentials and connection details for the secured CustomerDNA platform.

Usage rules for this folder:

- These files are for the demo and jury walkthrough only.
- They are not production-grade secret storage.
- If any password is changed in deployment `.env` files, update the matching file here immediately.
- SSH operating-system passwords are not stored here unless the VM owner explicitly decides to add them manually.
- Some local browser endpoints are now exposed through a TLS gateway with an internal demo certificate authority, so first access may show a certificate warning.
