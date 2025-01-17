# Call with
#
# irule -r irods_rule_engine_plugin-python-instance -F /rules/tests/test_metadata_edit_allowed.r "*project_path='/nlmumc/projects/P000000015'" | python -m json.tool

def main(rule_args, callback, rei):
    project_path = global_vars["*project_path"][1:-1]

    # Python-iRODS: When calling a rule without input arguments you need to provide a (empty or nonsense) string, which will contain the output.
    output = callback.check_edit_metadata_permission(project_path, '')

    # Retrieving the rule outcome is done with '["arguments"][0]'
    callback.writeLine("stdout", output["arguments"][1])



INPUT *project_path=""
OUTPUT ruleExecOut
