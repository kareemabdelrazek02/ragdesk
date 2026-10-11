# Web Application Security Checklist

SQL injection happens when user input is concatenated into a database query. The fix is to use parameterized queries or prepared statements and never build SQL strings from raw input.

Broken access control, including insecure direct object references, lets a user reach records that belong to someone else by changing an identifier in the URL. Every request must check on the server that the current user is authorized for the requested object.

Session cookies should be marked HttpOnly, Secure and SameSite, and session identifiers must be rotated after login to prevent session fixation.

Security monitoring complements secure code. A SIEM collects logs from servers and applications, correlates events, and raises alerts that analysts triage. Endpoint detection and response tools watch process behavior on individual machines.
