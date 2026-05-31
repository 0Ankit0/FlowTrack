#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000/api/v1}"
PGHOST="${PGHOST:-localhost}"
PGUSER="${PGUSER:-postgres}"
PGPASSWORD="${PGPASSWORD:-postgres}"
PGDATABASE="${PGDATABASE:-flowtrack_qa}"

ADMIN_USERNAME="qa_admin"
ADMIN_EMAIL="qa-admin@example.com"
PM_USERNAME="qa_pm"
PM_EMAIL="qa-pm@example.com"
CLIENT_USERNAME="qa_client"
CLIENT_EMAIL="qa-client@example.com"
DEFAULT_PASSWORD="${QA_USER_PASSWORD:-QaPass123!}"

json_eval() {
  local payload="$1"
  local expr="$2"
  python3 - "$expr" "$payload" <<'PY'
import json
import sys

obj = json.loads(sys.argv[2])
expr = sys.argv[1]
safe_globals = {"__builtins__": {}, "next": next, "any": any}
value = eval(expr, safe_globals, {"obj": obj})
if value is None:
    print("")
elif isinstance(value, (dict, list)):
    print(json.dumps(value))
else:
    print(value)
PY
}

request() {
  local method="$1"
  local path="$2"
  local token="${3:-}"
  local data="${4:-}"

  local tmp_file
  tmp_file="$(mktemp)"

  local code
  if [[ -n "$token" && -n "$data" ]]; then
    code=$(curl -L -sS -o "$tmp_file" -w "%{http_code}" -X "$method" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      "$API_BASE$path" \
      -d "$data")
  elif [[ -n "$token" ]]; then
    code=$(curl -L -sS -o "$tmp_file" -w "%{http_code}" -X "$method" \
      -H "Authorization: Bearer $token" \
      "$API_BASE$path")
  elif [[ -n "$data" ]]; then
    code=$(curl -L -sS -o "$tmp_file" -w "%{http_code}" -X "$method" \
      -H "Content-Type: application/json" \
      "$API_BASE$path" \
      -d "$data")
  else
    code=$(curl -L -sS -o "$tmp_file" -w "%{http_code}" -X "$method" "$API_BASE$path")
  fi

  RESPONSE_BODY="$(cat "$tmp_file")"
  RESPONSE_CODE="$code"
  rm -f "$tmp_file"
}

ensure_user() {
  local username="$1"
  local email="$2"
  local first_name="$3"
  local last_name="$4"

  local payload
  payload=$(cat <<JSON
{"username":"$username","email":"$email","password":"$DEFAULT_PASSWORD","confirm_password":"$DEFAULT_PASSWORD","first_name":"$first_name","last_name":"$last_name"}
JSON
)

  request POST "/auth/signup/?set_cookie=false" "" "$payload"
  if [[ "$RESPONSE_CODE" == "200" || "$RESPONSE_CODE" == "201" || "$RESPONSE_CODE" == "400" ]]; then
    return 0
  fi

  echo "Failed to ensure user $username: HTTP $RESPONSE_CODE"
  echo "$RESPONSE_BODY"
  exit 1
}

login_access_token() {
  local username="$1"
  local payload
  payload=$(cat <<JSON
{"username":"$username","password":"$DEFAULT_PASSWORD"}
JSON
)

  request POST "/auth/login/?set_cookie=false" "" "$payload"
  if [[ "$RESPONSE_CODE" != "200" ]]; then
    echo "Login failed for $username: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi

  json_eval "$RESPONSE_BODY" "obj.get('access', '')"
}

promote_superuser() {
  PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 -c \
    "UPDATE \"user\" SET is_superuser = TRUE WHERE email = '$ADMIN_EMAIL';"
}

ensure_tenant_member() {
  local email="$1"
  local slug="$2"
  local role="${3:-MEMBER}"

  PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 <<SQL
WITH target AS (
  SELECT t.id AS tenant_id, u.id AS user_id
  FROM tenant t
  JOIN "user" u ON u.email = '$email'
  WHERE t.slug = '$slug'
), updated AS (
  UPDATE tenantmember tm
  SET role = '$role'::tenantrole,
      is_active = TRUE
  FROM target
  WHERE tm.tenant_id = target.tenant_id
    AND tm.user_id = target.user_id
  RETURNING tm.id
)
INSERT INTO tenantmember (tenant_id, user_id, role, is_active, joined_at)
SELECT target.tenant_id, target.user_id, '$role'::tenantrole, TRUE, NOW()
FROM target
WHERE NOT EXISTS (SELECT 1 FROM updated);
SQL
}

ensure_tenant() {
  local token="$1"
  local name="$2"
  local slug="$3"
  local description="$4"

  request GET "/tenants/?limit=100" "$token"
  if [[ "$RESPONSE_CODE" != "200" ]]; then
    echo "Failed to list tenants: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi

  local tenant_id
  tenant_id=$(json_eval "$RESPONSE_BODY" "next((i.get('id') for i in obj.get('items', []) if i.get('slug') == '$slug'), '')")
  if [[ -n "$tenant_id" ]]; then
    echo "$tenant_id"
    return
  fi

  local payload
  payload=$(cat <<JSON
{"name":"$name","slug":"$slug","description":"$description"}
JSON
)

  request POST "/tenants/" "$token" "$payload"
  if [[ "$RESPONSE_CODE" != "200" && "$RESPONSE_CODE" != "201" ]]; then
    echo "Failed to create tenant $slug: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi

  json_eval "$RESPONSE_BODY" "obj.get('id', '')"
}

find_role_id() {
  local token="$1"
  local role_name="$2"

  request GET "/roles?limit=100" "$token"
  if [[ "$RESPONSE_CODE" != "200" ]]; then
    echo "Failed to list roles: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi

  json_eval "$RESPONSE_BODY" "next((i.get('id') for i in obj.get('items', []) if i.get('name') == '$role_name'), '')"
}

ensure_user_role() {
  local token="$1"
  local user_id="$2"
  local role_id="$3"

  request GET "/users/$user_id/roles" "$token"
  if [[ "$RESPONSE_CODE" != "200" ]]; then
    echo "Failed to get user roles for $user_id: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi

  local has_role
  has_role=$(json_eval "$RESPONSE_BODY" "any(i.get('id') == '$role_id' for i in obj.get('roles', []))")
  if [[ "$has_role" == "True" ]]; then
    return
  fi

  local payload
  payload=$(cat <<JSON
{"user_id":"$user_id","role_id":"$role_id"}
JSON
)

  request POST "/users/assign-role" "$token" "$payload"
  if [[ "$RESPONSE_CODE" != "200" ]]; then
    echo "Failed to assign role $role_id to $user_id: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi
}

ensure_project() {
  local token="$1"
  local tenant_id="$2"
  local name="$3"

  request GET "/projects/?tenant_id=$tenant_id&limit=100" "$token"
  if [[ "$RESPONSE_CODE" != "200" ]]; then
    echo "Failed to list projects: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi

  local project_id
  project_id=$(json_eval "$RESPONSE_BODY" "next((i.get('id') for i in obj.get('items', []) if i.get('name') == '$name'), '')")
  if [[ -n "$project_id" ]]; then
    echo "$project_id"
    return
  fi

  local payload
  payload=$(cat <<JSON
{"tenant_id":"$tenant_id","name":"$name","description":"QA seeded project for regression workflows","status":"active","health":"green"}
JSON
)

  request POST "/projects/" "$token" "$payload"
  if [[ "$RESPONSE_CODE" != "200" && "$RESPONSE_CODE" != "201" ]]; then
    echo "Failed to create project: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi

  json_eval "$RESPONSE_BODY" "obj.get('id', '')"
}

ensure_ticket() {
  local token="$1"
  local tenant_id="$2"
  local project_id="$3"
  local title="$4"

  request GET "/tickets/?tenant_id=$tenant_id&limit=100" "$token"
  if [[ "$RESPONSE_CODE" != "200" ]]; then
    echo "Failed to list tickets: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi

  local ticket_id
  ticket_id=$(json_eval "$RESPONSE_BODY" "next((i.get('id') for i in obj.get('items', []) if i.get('title') == '$title'), '')")
  if [[ -n "$ticket_id" ]]; then
    echo "$ticket_id"
    return
  fi

  local payload
  payload=$(cat <<JSON
{"tenant_id":"$tenant_id","project_id":"$project_id","title":"$title","description":"QA seeded ticket to test board, lifecycle, and reporting workflows.","type":"bug","severity":"high"}
JSON
)

  request POST "/tickets/" "$token" "$payload"
  if [[ "$RESPONSE_CODE" != "200" && "$RESPONSE_CODE" != "201" ]]; then
    echo "Failed to create ticket: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi

  json_eval "$RESPONSE_BODY" "obj.get('id', '')"
}

ensure_release() {
  local token="$1"
  local tenant_id="$2"
  local project_id="$3"
  local ticket_id="$4"

  request GET "/releases/?tenant_id=$tenant_id" "$token"
  if [[ "$RESPONSE_CODE" != "200" ]]; then
    echo "Failed to list releases: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi

  local version="v0.1.0-qa"
  local release_id
  release_id=$(json_eval "$RESPONSE_BODY" "next((i.get('id') for i in obj if i.get('version') == '$version'), '')")
  if [[ -n "$release_id" ]]; then
    echo "$release_id"
    return
  fi

  local payload
  payload=$(cat <<JSON
{"project_id":"$project_id","version":"$version","status":"planned","release_type":"planned","ticket_ids":["$ticket_id"],"notes":"QA seeded release for end-to-end verification."}
JSON
)

  request POST "/releases/" "$token" "$payload"
  if [[ "$RESPONSE_CODE" != "200" && "$RESPONSE_CODE" != "201" ]]; then
    echo "Failed to create release: HTTP $RESPONSE_CODE"
    echo "$RESPONSE_BODY"
    exit 1
  fi

  json_eval "$RESPONSE_BODY" "obj.get('id', '')"
}

echo "Seeding QA users..."
ensure_user "$ADMIN_USERNAME" "$ADMIN_EMAIL" "QA" "Admin"
ensure_user "$PM_USERNAME" "$PM_EMAIL" "QA" "PM"
ensure_user "$CLIENT_USERNAME" "$CLIENT_EMAIL" "QA" "Client"

echo "Promoting admin user to superuser..."
promote_superuser

echo "Logging in users..."
ADMIN_TOKEN="$(login_access_token "$ADMIN_USERNAME")"
PM_TOKEN="$(login_access_token "$PM_USERNAME")"
CLIENT_TOKEN="$(login_access_token "$CLIENT_USERNAME")"

request GET "/users/me/" "$ADMIN_TOKEN"
ADMIN_ID="$(json_eval "$RESPONSE_BODY" "obj.get('id', '')")"
request GET "/users/me/" "$PM_TOKEN"
PM_ID="$(json_eval "$RESPONSE_BODY" "obj.get('id', '')")"
request GET "/users/me/" "$CLIENT_TOKEN"
CLIENT_ID="$(json_eval "$RESPONSE_BODY" "obj.get('id', '')")"

echo "Creating tenants..."
TENANT_A_ID="$(ensure_tenant "$ADMIN_TOKEN" "QA Delivery Org" "qa-delivery" "Tenant for PM and delivery workflows")"
TENANT_B_ID="$(ensure_tenant "$ADMIN_TOKEN" "QA Client Org" "qa-client" "Tenant for client and requester workflows")"

echo "Assigning IAM roles..."
ROLE_PM_ID="$(find_role_id "$ADMIN_TOKEN" "project_manager")"
ROLE_CLIENT_ID="$(find_role_id "$ADMIN_TOKEN" "client_requester")"
if [[ -n "$ROLE_PM_ID" ]]; then
  ensure_user_role "$ADMIN_TOKEN" "$PM_ID" "$ROLE_PM_ID"
fi
if [[ -n "$ROLE_CLIENT_ID" ]]; then
  ensure_user_role "$ADMIN_TOKEN" "$CLIENT_ID" "$ROLE_CLIENT_ID"
fi

echo "Ensuring tenant memberships..."
ensure_tenant_member "$PM_EMAIL" "qa-delivery" "MEMBER"
ensure_tenant_member "$CLIENT_EMAIL" "qa-client" "MEMBER"
ensure_tenant_member "$CLIENT_EMAIL" "qa-delivery" "MEMBER"

echo "Creating seeded flowtrack records..."
PROJECT_ID="$(ensure_project "$PM_TOKEN" "$TENANT_A_ID" "QA Migration Project")"
TICKET_ID="$(ensure_ticket "$PM_TOKEN" "$TENANT_A_ID" "$PROJECT_ID" "QA regression smoke ticket")"
RELEASE_ID="$(ensure_release "$PM_TOKEN" "$TENANT_A_ID" "$PROJECT_ID" "$TICKET_ID")"

cat <<EOF
QA seed complete.
- Admin user: $ADMIN_USERNAME / $DEFAULT_PASSWORD
- PM user: $PM_USERNAME / $DEFAULT_PASSWORD
- Client user: $CLIENT_USERNAME / $DEFAULT_PASSWORD
- Tenant A: $TENANT_A_ID
- Tenant B: $TENANT_B_ID
- Project: $PROJECT_ID
- Ticket: $TICKET_ID
- Release: $RELEASE_ID
EOF
