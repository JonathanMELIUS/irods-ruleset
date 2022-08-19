import json
import subprocess


def test_get_collection_attribute_value():
    rule = '/rules/tests/run_test.sh -r get_collection_attribute_value -a "/nlmumc/projects/P000000010/C000000001,title"'
    ret = subprocess.check_output(rule, shell=True)

    avu = json.loads(ret)
    assert avu['value'] == "(MDL) Placeholder collection"


def test_get_collection_size():
    rule = '/rules/tests/run_test.sh -r get_collection_size -a "/nlmumc/projects/P000000010/C000000001,B,none"'
    ret = subprocess.check_output(rule, shell=True)

    size = json.loads(ret)
    assert size == 393.0


def test_get_collection_size_per_resource():
    rule = '/rules/tests/run_test.sh -r get_collection_size_per_resource -a "P000000010"'
    ret = subprocess.check_output(rule, shell=True)

    collection_sizes = json.loads(ret)
    assert collection_sizes["C000000001"][0]["relativeSize"] == 100.0
    assert collection_sizes["C000000001"][0]["resourceId"].isdigit() is True
    assert collection_sizes["C000000001"][0]["resourceName"] == "arcRescSURF01"
    assert collection_sizes["C000000001"][0]["size"] == "393"


def test_get_collection_tree():
    rule = '/rules/tests/run_test.sh -r get_collection_tree -a "P000000010/C000000001"'
    ret = subprocess.check_output(rule, shell=True)

    collection = json.loads(ret)
    assert len(collection) == 1
    assert collection[0]["ctime"] is not None  # TODO regex against this format 2022-08-16 16:12:54
    assert collection[0]["mtime"] is not None
    assert collection[0]["name"] == "filebeat.yml"
    assert collection[0]["offlineResource"] is True
    assert collection[0]["path"] == "P000000010/C000000001/filebeat.yml"
    assert collection[0]["rescname"] == "arcRescSURF01"
    assert collection[0]["size"] == "393"
    assert collection[0]["type"] == "file"


def test_list_collections():
    rule = '/rules/tests/run_test.sh -r list_collections -a "/nlmumc/projects/P000000010"'
    ret = subprocess.check_output(rule, shell=True)

    collections = json.loads(ret)
    assert len(collections) == 1
    assert collections[0]["PID"] == "21.T12996/P000000010C000000001"
    assert collections[0]["creator"] == "irods_bootstrap@docker.dev"
    assert collections[0]["id"] == "C000000001"
    assert collections[0]["numFiles"] == 1
    # assert collections[0]["numUserFiles"] == -3
    assert collections[0]["size"] == 393.0
    assert collections[0]["title"] == "(MDL) Placeholder collection"


def test_set_acl():
    # Give read access to auser to /nlmumc/projects/P000000010/C000000001
    rule_set_read = '/rules/tests/run_test.sh -r set_acl -a "default,read,auser,/nlmumc/projects/P000000010/C000000001"'
    subprocess.check_output(rule_set_read, shell=True)

    # Check if auser can read /nlmumc/projects/P000000010/C000000001
    rule_list_collections = '/rules/tests/run_test.sh -r list_collections -a "/nlmumc/projects/P000000010" -u auser'
    ret = subprocess.check_output(rule_list_collections, shell=True)
    collections = json.loads(ret)
    assert len(collections) == 1

    # Revoke read access of auser to /nlmumc/projects/P000000010/C000000001
    rule_set_null = '/rules/tests/run_test.sh -r set_acl -a "default,null,auser,/nlmumc/projects/P000000010/C000000001"'
    subprocess.check_output(rule_set_null, shell=True)

    # Check if auser cannot read /nlmumc/projects/P000000010/C000000001
    ret = subprocess.check_output(rule_list_collections, shell=True)
    collections = json.loads(ret)
    assert len(collections) == 0