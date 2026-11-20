# Security policy

Desk Yantra is pre-release software for one trusted user on a loopback Linux host. No release is approved for internet exposure, multiple untrusted users or remote hosting. Only the current main branch receives fixes; there is no supported stable release yet.

Use GitHub's private vulnerability reporting on the repository Security tab if available. If unavailable, open a minimal issue requesting a private reporting channel, without exploit details, credentials, recordings or personal state. No response-time guarantee is established.

Include the affected commit, boundary crossed, prerequisites and a minimal reproduction against disposable data. Avoid testing against other users or external accounts. The release gates and known gaps are recorded in PLANNING.md; passing fixtures is not independent security review.

Pairing authorizes interface access. Host actions additionally depend on workspace grants and exact approvals. Host shell is account-wide, Docker access can control the host, and sandbox network access is currently unrestricted. Treat model responses, web pages, downloaded files and artifacts as untrusted. Keep private state and its encryption key private; an account compromise defeats local key protection.
