import json
import sys
import jsonavu
import session_vars
from genquery import (row_iterator, paged_iterator, AS_DICT, AS_LIST)
from jsonschema import validate
from jsonschema.exceptions import *
import requests
import re

# Global vars
activelyUpdatingAVUs = False

# This rule stores a given json string as AVU's to an object
# Argument 0: The object (/nlmumc/projects/P000000003/C000000001/metadata.xml, /nlmumc/projects/P000000003/C000000001/, user@mail.com, demoResc
# Argument 1: The object type -d for data object
#                             -R for resource
#                             -C for collection
#                             -u for user
# Argument 2:  the JSON root according to https://github.com/MaastrichtUniversity/irods_avu_json.
# Argument 3:  the JSON string (make sure the quotes are escaped)  {\"k1\":\"v1\",\"k2\":{\"k3\":\"v2\",\"k4\":\"v3\"},\"k5\":[\"v4\",\"v5\"],\"k6\":[{\"k7\":\"v6\",\"k8\":\"v7\"}]}
#
def setJSONtoObj(rule_args, callback, rei):
    object = rule_args[0]
    input_type = rule_args[1]
    json_root = rule_args[2]
    json_string = rule_args[3]

    try:
        data = json.loads(json_string)
    except ValueError, e:
        callback.writeLine("serverLog", "Invalid json provided")
        callback.msiExit("-1101000", "Invalid json provided")

    # check if validation is required
    validation_required = False
    json_schema_url = ""
    # Get all avu's with attribute $id
    ret_val = callback.getAVUfromObj(object, input_type, '$id', "")
    ids = json.loads(ret_val['arguments'][3])
    for element in ids:
        if element['u'] == json_root:
            validation_required = True
            json_schema_url = element['v']

    if validation_required :
        r = requests.get(json_schema_url)
        schema = r.json()
        try:
            validate(instance=data, schema=schema)
        except ValidationError, e:
            callback.writeLine("serverLog", "JSON Instance could not be validated against JSON-schema " + str(e.message))
            callback.msiExit("-1101000", "JSON Instance could not be validated against JSON-schema : "+ str(e.message))

    # load global variable activelyUpdatingAVUs and set this to true. At this point we are actively updating AVU and want to disable some of the checks.
    global activelyUpdatingAVUs
    activelyUpdatingAVUs = True

    ret_val = callback.msi_rmw_avu(input_type, object, "%", "%", json_root + "_%")
    if ret_val['status'] == False and ret_val['code'] != -819000:
        callback.writeLine("stdout", "msi failed with: " + ret_val['code'])

    avu = jsonavu.json2avu(data, json_root)

    for i in avu:
        ret_val = callback.msi_add_avu(input_type, object, i["a"], i["v"], i["u"])

    #Set global variable activelyUpdatingAVUsthis to false. At this point we are done updating AVU and want to enable some of the checks.
    activelyUpdatingAVUs = False

# This rule return a json string from AVU's set to an object
# Argument 0: The object (/nlmumc/projects/P000000003/C000000001/metadata_cedar.jsonld, /nlmumc/projects/P000000003/C000000001/, user@mail.com, demoResc
# Argument 1: The object type -d for data object
#                             -R for resource
#                             -C for collection
#                             -u for user
# Argument 2:  the JSON root according to https://github.com/MaastrichtUniversity/irods_avu_json.
#
# OUTPUT:  json string from AVU's set to an object
def getJSONfromObj(rule_args, callback, rei):
    object = rule_args[0]
    input_type = rule_args[1]
    json_root = rule_args[2]
    result = rule_args[3]
    result_list = []

    # data object
    if input_type == '-d' or input_type == '-D':
        ret_val = callback.msiSplitPath(object, "", "")
        data_object = ret_val['arguments'][2]
        collection = ret_val['arguments'][1]
        rows = row_iterator(
            ["META_DATA_ATTR_NAME", "META_DATA_ATTR_VALUE", "META_DATA_ATTR_UNITS"],
            "COLL_NAME = '" + collection + "' AND DATA_NAME = '" + data_object + "'",
            AS_DICT,
            callback)
        for row in rows:
            result_list.append({
                "a": row["META_DATA_ATTR_NAME"],
                "v": row["META_DATA_ATTR_VALUE"],
                "u": row["META_DATA_ATTR_UNITS"]
            })
    # collection
    elif input_type == '-c' or input_type == '-C':
        rows = row_iterator(
            ["META_COLL_ATTR_NAME", "META_COLL_ATTR_VALUE", "META_COLL_ATTR_UNITS"],
            "COLL_NAME = '" + object + "'",
            AS_DICT,
            callback)
        for row in rows:
            result_list.append({
                "a": row["META_COLL_ATTR_NAME"],
                "v": row["META_COLL_ATTR_VALUE"],
                "u": row["META_COLL_ATTR_UNITS"]
            })
    # resource
    elif input_type == '-r' or input_type == '-R':
        rows = row_iterator(
            ["META_RESC_ATTR_NAME", "META_RESC_ATTR_VALUE", "META_RESC_ATTR_UNITS"],
            "RESC_NAME = '" + object + "'",
            AS_DICT,
            callback)
        for row in rows:
            result_list.append({
                "a": row["META_RESC_ATTR_NAME"],
                "v": row["META_RESC_ATTR_VALUE"],
                "u": row["META_RESC_ATTR_UNITS"]
            })
    # user
    elif input_type == '-u' or input_type == '-U':
        rows = row_iterator(
            ["META_USER_ATTR_NAME", "META_USER_ATTR_VALUE", "META_USER_ATTR_UNITS"],
            "USER_NAME = '" + object + "'",
            AS_DICT,
            callback)
        for row in rows:
            result_list.append({
                "a": row["META_USER_ATTR_NAME"],
                "v": row["META_USER_ATTR_VALUE"],
                "u": row["META_USER_ATTR_UNITS"]
            })
    else:
        callback.writeLine("serverLog", "type should be -d, -C, -R or -u")

    if json_root == '':
        result = json.dumps(result_list)
    else:
        data_back = jsonavu.avu2json(result_list, json_root)
        result = json.dumps(data_back)
    rule_args[3] = result

# This rule return a json string from AVU's set to an object
# Argument 0: The object (/nlmumc/projects/P000000003/C000000001/metadata_cedar.jsonld, /nlmumc/projects/P000000003/C000000001/, user@mail.com, demoResc
# Argument 1: The object type -d for data object
#                             -R for resource
#                             -C for collection
#                             -u for user
# Argument 2:  if you want only items with specific attribute name you can set a filter here
#
# OUTPUT:  json string with AVU's set to an object
def getAVUfromObj(rule_args, callback, rei):
    object = rule_args[0]
    input_type = rule_args[1]
    filter = rule_args[2]
    result = rule_args[3]
    result_list = []
    # data object
    if input_type == '-d' or input_type == '-D':
        ret_val = callback.msiSplitPath(object, "", "")
        data_object = ret_val['arguments'][2]
        collection = ret_val['arguments'][1]
        rows = row_iterator(
            ["META_DATA_ATTR_NAME", "META_DATA_ATTR_VALUE", "META_DATA_ATTR_UNITS"],
            "COLL_NAME = '" + collection + "' AND DATA_NAME = '" + data_object + "'",
            AS_DICT,
            callback)
        for row in rows:
            if filter == '':
                result_list.append({
                    "a": row["META_DATA_ATTR_NAME"],
                    "v": row["META_DATA_ATTR_VALUE"],
                    "u": row["META_DATA_ATTR_UNITS"]
                })
            else:
                if row["META_DATA_ATTR_NAME"] == filter:
                    result_list.append({
                        "a": row["META_DATA_ATTR_NAME"],
                        "v": row["META_DATA_ATTR_VALUE"],
                        "u": row["META_DATA_ATTR_UNITS"]
                    })

    # collection
    elif input_type == '-c' or input_type == '-C':
        rows = row_iterator(
            ["META_COLL_ATTR_NAME", "META_COLL_ATTR_VALUE", "META_COLL_ATTR_UNITS"],
            "COLL_NAME = '" + object + "'",
            AS_DICT,
            callback)
        for row in rows:
            if filter == '':
                result_list.append({
                    "a": row["META_COLL_ATTR_NAME"],
                    "v": row["META_COLL_ATTR_VALUE"],
                    "u": row["META_COLL_ATTR_UNITS"]
                })
            else:
                if row["META_COLL_ATTR_NAME"] == filter:
                    result_list.append({
                        "a": row["META_COLL_ATTR_NAME"],
                        "v": row["META_COLL_ATTR_VALUE"],
                        "u": row["META_COLL_ATTR_UNITS"]
                    })
    # resource
    elif input_type == '-r' or input_type == '-R':
        rows = row_iterator(
            ["META_RESC_ATTR_NAME", "META_RESC_ATTR_VALUE", "META_RESC_ATTR_UNITS"],
            "RESC_NAME = '" + object + "'",
            AS_DICT,
            callback)
        for row in rows:
            if filter == '':
                result_list.append({
                    "a": row["META_RESC_ATTR_NAME"],
                    "v": row["META_RESC_ATTR_VALUE"],
                    "u": row["META_RESC_ATTR_UNITS"]
                })
            else:
                if row["META_RESC_ATTR_NAME"] == filter:
                    result_list.append({
                        "a": row["META_RESC_ATTR_NAME"],
                        "v": row["META_RESC_ATTR_VALUE"],
                        "u": row["META_RESC_ATTR_UNITS"]
                    })
    # user
    elif input_type == '-u' or input_type == '-U':
        rows = row_iterator(
            ["META_USER_ATTR_NAME", "META_USER_ATTR_VALUE", "META_USER_ATTR_UNITS"],
            "USER_NAME = '" + object + "'",
            AS_DICT,
            callback)
        for row in rows:
            if filter == '':
                result_list.append({
                    "a": row["META_USER_ATTR_NAME"],
                    "v": row["META_USER_ATTR_VALUE"],
                    "u": row["META_USER_ATTR_UNITS"]
                })
            else:
                if row["META_USER_ATTR_NAME"] == filter:
                    result_list.append({
                        "a": row["META_USER_ATTR_NAME"],
                        "v": row["META_USER_ATTR_VALUE"],
                        "u": row["META_USER_ATTR_UNITS"]
                    })
    else:
        callback.writeLine("serverLog", "type should be -d, -C, -R or -u")

    result = json.dumps(result_list)
    rule_args[3] = result



# This rule stores a given json-schema as AVU's to an object
# Argument 0: The object (/nlmumc/projects/P000000003/C000000001/metadata.xml, /nlmumc/projects/P000000003/C000000001/, user@mail.com, demoResc
# Argument 1: The object type -d for data object
#                             -R for resource
#                             -C for collection
#                             -u for user
# Argument 2:   Url to the JSON-Schema example https://api.myjson.com/bins/17vejk
# Argument 3:   the JSON root according to https://github.com/MaastrichtUniversity/irods_avu_json.

def setJSONschematoObj(rule_args, callback, rei):
    object = rule_args[0]
    input_type = rule_args[1]
    json_schema_url = rule_args[2]
    json_root = rule_args[3]

    #check if this root has been used before
    ret_val = callback.getAVUfromObj(object, input_type, '', "")
    all_avu = json.loads(ret_val['arguments'][3])
    # From these avu's extract the unit (root)
    root_list = []
    for element in all_avu:
        # Regular expression pattern for unit field
        pattern = re.compile('^([a-zA-Z0-9_]+)_([0-9]+)_([osbnze])((?<=o)[0-9]+)?((?:#[0-9]+?)*)')
        # Match unit to extract all info
        unit = pattern.match(str(element['u']))
        # This AVU may be unrelated to the JSON
        if not unit:
            continue
        root = unit.group(1)
        root_list.append(root)
    callback.writeLine("serverLog", "root_list" + str(root_list))
    if json_root in root_list:
        callback.writeLine("serverLog", "Root " + json_root + " is already in use")
        callback.msiExit("-1101000", "Root " + json_root + " is already in use")

    # Delete existing $id AVU for this json root
    callback.msi_rmw_avu(input_type, object, '$id', "%", json_root)
    #Set new $id AVU
    callback.msi_add_avu(input_type, object, '$id', json_schema_url, json_root)


#def acPreProcForModifyAVUMetadata(rule_args, callback, rei):
#    callback.writeLine("serverLog", "Python acPreProcForModifyAVUMetadata")
#    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))

# This function checks if a UNIT change should be allowed. If UNIT is part of an existing json changing should not be allowed.
# Only in the case we we are actively updating AVU trough setJSONtoObj
# Argument 0:   The object (/nlmumc/projects/P000000003/C000000001/metadata.xml, /nlmumc/projects/P000000003/C000000001/, user@mail.com, demoResc
# Argument 1:   The object type -d for data object
#                             -R for resource
#                             -C for collection
#                             -u for user
# Argument 2:   The existing value for unit
# Output 0:     Boolean
def allowAVUChange(object, object_type, unit, callback):
    global activelyUpdatingAVUs
    # Check if we are activelyUpdatingAVUs from setJSONtoObj. In that case we do not want the filtering below
    if not activelyUpdatingAVUs:
        # Get all avu's with attribute $id
        ret_val = callback.getAVUfromObj(object, object_type, '$id', "")
        ids = json.loads(ret_val['arguments'][3])
        # From these avu's extract the unit (root)
        root_list = []
        for element in ids:
            root_list.append(element['u'])
        # Get the unit from the avu that is currently added.
        unit = str(unit)
        for root in root_list:
            # if the unit start with one of the roots, disallow the operation
            if unit.startswith(root + "_"):
                return False
    return True
####

def pep_database_set_avu_metadata_pre(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_set_avu_metadata_pre")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))
    object_name = rule_args[4]
    object_type = rule_args[3]
    object_unit = rule_args[7]
    if not allowAVUChange(object_name, object_type, object_unit, callback):
        callback.msiOprDisallowed()

def pep_database_set_avu_metadata_post(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_set_avu_metadata_post")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))

def pep_database_set_avu_metadata_except(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_set_avu_metadata_except")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))

#####

def pep_database_add_avu_metadata_wild_pre(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_add_avu_metadata_wild_pre")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))
    object_name = rule_args[5]
    object_type = rule_args[4]
    object_unit = rule_args[8]
    if not allowAVUChange(object_name, object_type, object_unit, callback):
        callback.msiOprDisallowed()

def pep_database_add_avu_metadata_wild_post(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_add_avu_metadata_wild_post")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))

def pep_database_add_avu_metadata_wild_except(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_add_avu_metadata_wild_except")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))

####

def pep_database_add_avu_metadata_pre(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_add_avu_metadata_pre")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))
    object_name = rule_args[5]
    object_type = rule_args[4]
    object_unit = rule_args[8]
    if not allowAVUChange(object_name, object_type, object_unit, callback):
        callback.msiOprDisallowed()


def pep_database_add_avu_metadata_post(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_add_avu_metadata_post")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))


def pep_database_add_avu_metadata_except(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_add_avu_metadata_except")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))

####

def pep_database_mod_avu_metadata_prep(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_mod_avu_metadata_prep")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))
    object_name = rule_args[4]
    object_type = rule_args[3]
    object_old_unit = rule_args[7]
    object_new_unit = rule_args[10]
    #If old unit starts with one of the roots disallow
    if not allowAVUChange(object_name, object_type, object_old_unit, callback):
        callback.msiOprDisallowed()
    # If new unit starts with one of the roots disallow
    if not allowAVUChange(object_name, object_type, object_new_unit, callback):
        callback.msiOprDisallowed()


def pep_database_mod_avu_metadata_post(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_mod_avu_metadata_post")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))


def pep_database_mod_avu_metadata_except(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_mod_avu_metadata_except")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))

####

def pep_database_del_avu_metadata_pre(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_del_avu_metadata_pre")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))
    object_name = rule_args[5]
    object_type = rule_args[4]
    object_unit = rule_args[8]
    if not allowAVUChange(object_name, object_type, object_unit, callback):
        callback.msiOprDisallowed()


def pep_database_del_avu_metadata_post(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_del_avu_metadata_post")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))


def pep_database_del_avu_metadata_except(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_del_avu_metadata_except")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))

####

def pep_database_copy_avu_metadata_pre(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_copy_avu_metadata_pre")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))


def pep_database_copy_avu_metadata_post(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_copy_avu_metadata_post")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))


def pep_database_copy_avu_metadata_except(rule_args, callback, rei):
    callback.writeLine("serverLog", "Python pep_database_copy_avu_metadata_except")
    callback.writeLine("serverLog", "Length of arguments is: " + str(len(rule_args)))