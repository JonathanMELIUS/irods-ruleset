@make(inputs=[0, 1, 2], outputs=[], handler=Output.STORE)
def update_instance_snapshot(ctx, project_collection_full_path, schema_url, handle):
    """
    Update an already ingested 'instance.json' file and 'schema.json' file

    Parameters
    ----------
    ctx : Context
        Combined type of a callback and rei struct.
    project_collection_full_path : str
        The absolute path of the collection; e.g: /nlmumc/projects/P000000014/C000000001/
    schema_url : str
        The schema URL to value to replace in the instance; e.g: http://mdr.local.dh.unimaas.nl/hdl/P000000014/C000000001/schema.1
    handle: str
        The (versioned) handle PID for the collection
    """

    # Reading the instance.json and parsing it
    instance_location = "{}/instance.json".format(project_collection_full_path)
    instance = read_data_object_from_irods(ctx, instance_location)
    instance_object = json.loads(instance)

    instance_object["schema:isBasedOn"] = schema_url

    new_handle = "https://hdl.handle.net/" + handle
    instance_object["1_Identifier"]["datasetIdentifier"]["@value"] = new_handle
    instance_object["@id"] = new_handle

    # Opening the instance file with read/write access
    ret_val = ctx.callback.msiDataObjOpen("objPath=" + instance_location + "++++openFlags=O_RDWR", 0)
    opened_file = ret_val["arguments"][1]
    ctx.callback.msiDataObjWrite(opened_file, json.dumps(instance_object, indent=4), 0)
    ctx.callback.msiDataObjClose(opened_file, 0)

    # Setting the PID in the schema.json file
    schema_location = "{}/schema.json".format(project_collection_full_path)
    # Reading the instance.json and parsing it
    schema = read_data_object_from_irods(ctx, schema_location)
    schema_object = json.loads(schema)
    schema_object["@id"] = schema_url

    # Opening the schema file with read/write access
    ret_val = ctx.callback.msiDataObjOpen("objPath=" + schema_location + "++++openFlags=O_RDWR", 0)
    opened_schema_file = ret_val["arguments"][1]
    ctx.callback.msiDataObjWrite(opened_schema_file, json.dumps(schema_object, indent=4), 0)
    ctx.callback.msiDataObjClose(opened_schema_file, 0)
