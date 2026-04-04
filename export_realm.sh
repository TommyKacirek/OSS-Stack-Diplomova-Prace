#!/bin/bash
# Export Keycloak 'Lab' realm to project root
echo "Exporting Keycloak 'Lab' realm..."
kaca_pass="kaca"
echo "$kaca_pass" | sudo -S docker exec keycloak /opt/keycloak/bin/kc.sh export --realm Lab --file /tmp/lab-realm.json --users skip
echo "$kaca_pass" | sudo -S docker cp keycloak:/tmp/lab-realm.json ./keycloak_lab_realm_export.json
echo "Export complete: ./keycloak_lab_realm_export.json"
