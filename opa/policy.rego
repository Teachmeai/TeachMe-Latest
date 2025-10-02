package authz

default allow := false

allow if {
  input.role == "teacher"
}

allow if {
  input.role == "super_admin"
}

allow if {
  input.role == "organization_admin"
}