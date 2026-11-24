# DermAI - Role-Based Access

Roles follow the SRS: Patient (general user), Dermatologist (clinician), Medical Researcher, Data Scientist (ML engineer) and Administrator. No additional roles were invented; "doctor" corresponds to the SRS role Dermatologist / Clinician.

## How roles are given
- Registration creates a **Patient**. Users cannot choose a staff role for themselves.
- An **Administrator** assigns or removes roles in the application (Users and Roles page) or through the API. A user can hold several roles. An administrator cannot remove their own Administrator role.
- The very first administrator must be created directly in the database, because only an administrator can assign roles through the API:
```
INSERT INTO roles (role_id, role_name, description)
SELECT gen_random_uuid(), 'Administrator', 'Administrator role.'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE role_name = 'Administrator');
INSERT INTO user_roles (user_id, role_id)
SELECT u.user_id, r.role_id FROM users u, roles r
WHERE u.email = '<email>' AND r.role_name = 'Administrator'
AND NOT EXISTS (SELECT 1 FROM user_roles ur WHERE ur.user_id = u.user_id AND ur.role_id = r.role_id);
```

## Access matrix (enforced by the backend; the interface only hides what a role cannot use)
| Function | Patient | Dermatologist | Medical Researcher | Data Scientist | Administrator |
|---|---|---|---|---|---|
| Upload and capture images, run analysis, own history, reports, compare, case notes | yes (own data) | yes (own data) | yes (own data) | yes (own data) | yes (own data) |
| Model version and class list (`/insights/model-info`) | yes | yes | yes | yes | yes |
| Saved evaluation metrics (`/insights/model-metrics`, Research Insights page) | no | yes | yes | yes | yes |
| Clinician dashboard (`/dashboard/clinician`: counts, class distribution, recent analyses) | no | yes | no | no | yes |
| Research dashboard (`/dashboard/research`: de-identified aggregates only) | no | no | yes | yes | yes |
| Administrator dashboard (`/dashboard/admin`) | no | no | no | no | yes |
| User list and role management (`/admin/users`, `/roles/users/{id}`) | no | no | no | no | yes |

Every role can only open its own cases, images, analyses and reports; ownership is checked on the server (another user's record returns 404). Clinician access is limited to aggregate figures and a recent-analyses list; opening other users' cases is not granted (open policy decision, see the architecture document).

## Evidence
`backend/tests/test_role_access.py`: patient denied on all staff endpoints and able to read model info; dermatologist, researcher, data scientist and administrator allowed exactly their endpoints; research dashboard contains no identifiers; administrator assigns and revokes a role and the target user's access changes immediately; self-removal of the Administrator role is refused; all endpoints return 401 without a token.

## Limitations
- Roles are read from the database on each request; the interface refreshes roles when the page loads.
- Role self-service, approval workflow and audit logging of role changes are not implemented.
