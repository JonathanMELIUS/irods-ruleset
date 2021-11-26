@make(inputs=[0, 1, 2, 3, 4], outputs=[], handler=Output.STORE)
def post_ingest(ctx, project_id, username, token, collection_id, ingest_resource_host):
    """
    Actions to be performed after an ingest is completed
        Setting AVUs
        Removing AVUs
        Requesting a PID
        Removing the dropzone
        Updating the instance.json
        Closing the project collection

    Parameters
    ----------
    ctx : Context
        Combined type of a callback and rei struct.
    token: str
        The token of the dropzone to be ingested
    project_id: str
        The project id, ie P00000010
    collection_id: str
        The collection id, ie C00000004
    username: str
        The username of the person requesting the ingest
    ingest_resource_host: str
        The remote host that was ingested to, ie 'ires-dh.local
    """
    destination_collection = "/nlmumc/projects/{}/{}".format(project_id, collection_id)
    source_collection = "/nlmumc/ingest/zones/{}".format(token)

    # Set the Creator AVU
    ctx.callback.msiWriteRodsLog("{} : Setting AVUs to {}".format(source_collection, destination_collection), 0)
    email = username
    for row in row_iterator(
        "META_USER_ATTR_VALUE",
        "USER_NAME = '{}' AND META_USER_ATTR_NAME = 'email'".format(username),
        AS_LIST,
        ctx.callback,
    ):
        email = row[0]
    ctx.callback.setCollectionAVU(destination_collection, "creator", email)

    # Requesting a PID via epicPID
    handle_pid = ctx.callback.get_pid(project_id, collection_id, "")["arguments"][2]
    if handle_pid == "":
        ctx.callback.msiWriteRodsLog("Retrieving PID failed for {}, leaving blank".format(destination_collection), 0)
    else:
        # Setting the PID as AVU on the project collection
        ctx.callback.setCollectionAVU(destination_collection, "PID", handle_pid)

    # Fill the instance.json with the information needed in that instance (ie. handle PID)
    ctx.callback.update_instance(project_id, collection_id, handle_pid)

    # Copy templateSchemaVersion and templateSchemaName AVU from dropzone to the ingested collection
    templateSchemaName = ctx.callback.getCollectionAVU(source_collection, "templateSchemaName", "", "", "true")["arguments"][2]
    templateSchemaVersion = ctx.callback.getCollectionAVU(source_collection, "templateSchemaVersion", "", "", "true")["arguments"][2]
    ctx.callback.setCollectionAVU(destination_collection, "templateSchemaName", templateSchemaName)
    ctx.callback.setCollectionAVU(destination_collection, "templateSchemaVersion", templateSchemaVersion)

    # Setting the State AVU to Ingested
    ctx.callback.msiWriteRodsLog("Finished ingesting {} to {}".format(source_collection, destination_collection), 0)
    ctx.callback.setCollectionAVU(source_collection, "state", "ingested")

    # Remove the temporary sizeIngested AVU at *dstColl
    ctx.callback.remove_size_ingested_avu(destination_collection)

    # Close collection by making all access read only
    ctx.callback.closeProjectCollection(project_id, collection_id)

    # The unmounting of the physical mount point is not done in the delay() where msiRmColl on the token is done.
    # This is because of a bug in the unmount. This is kept in memory for
    # the remaining of the irodsagent session.
    # See also: https://groups.google.com/d/msg/irod-chat/rasDT-AGAVQ/Bb31VJ9SAgAJ
    try:
        ctx.callback.msiPhyPathReg(source_collection, "", "", "unmount", 0)
    except RuntimeError:
        ctx.callback.setErrorAVU(source_collection, "state", "error-post-ingestion", "Error unmounting")

    # Get environment config option for setting the delay for drop zone removal
    ingest_remove_delay = ctx.callback.msi_getenv("IRODS_INGEST_REMOVE_DELAY", "")["arguments"][1]

    ctx.callback.delayRemoveDropzone(ingest_remove_delay, source_collection, ingest_resource_host, token)
