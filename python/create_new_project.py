@make(inputs=range(13), outputs=[13], handler=Output.STORE)
def create_new_project(ctx, authorization_period_end_date, data_retention_period_end_date,
                       ingest_resource, resource, storage_quota_gb, title,
                       principal_investigator, data_steward,
                       resp_cost_center, open_access, tape_archive, tape_unarchive, metadata_schemas):
    """
    Create a new iRODS project

    Parameters
    ----------
    authorization_period_end_date : str
        The username
    data_retention_period_end_date : str
        The username
    ingest_resource : str
        The ingest resource to use during the ingestion
    resource : str
        The destination resource to store future collection
    storage_quota_gb  : str
        The storage quota in Gb
    title : str
        The project title
    principal_investigator : str
        The principal investigator(OBI:0000103) for the project
    data_steward : str
        The data steward for the project
    resp_cost_center : str
        The budget number
    open_access : str
        'true'/'false' expected values
    tape_archive : str
        'true'/'false' expected values
    tape_unarchive : str
        'true'/'false' expected values
    metadata_schemas : str
        csv string that contains the list of schema names
    """

    retry = 0
    error = -1
    new_project_path = ""
    project = ""

    # Try to create the new_project_path. Exit the loop on success (error = 0) or after too many retries.
    # The while loop adds compatibility for usage in parallelized runs of the delayed rule engine.
    while error < 0 and retry < 10:
        latest_project_number = ctx.callback.getCollectionAVU("/nlmumc/projects", "latest_project_number", "*latest_project_number", "", "true")["arguments"][2]
        new_latest = int(latest_project_number) + 1
        project = str(new_latest)
        while len(project) < 9:
            project = "0" + str(project)
        project = "P" + project

        new_project_path = "/nlmumc/projects/" + project

        retry = retry + 1
        try:
            ctx.callback.msiCollCreate(new_project_path, 0, 0)
        except RuntimeError:
            error = -1
        else:
            error = 0

    # Make the rule fail if it doesn't succeed in creating the project
    if error < 0 and retry >= 10:
        msg = "ERROR: Collection '{}' attempt no. {} : Unable to create {}".format(title, retry, new_project_path)
        ctx.callback.msiExit(str(error), msg)

    ctx.callback.setCollectionAVU(new_project_path, "authorizationPeriodEndDate", authorization_period_end_date)
    ctx.callback.setCollectionAVU(new_project_path, "dataRetentionPeriodEndDate", data_retention_period_end_date)
    ctx.callback.setCollectionAVU(new_project_path, "ingestResource", ingest_resource)
    ctx.callback.setCollectionAVU(new_project_path, "resource", resource)
    ctx.callback.setCollectionAVU(new_project_path, "storageQuotaGb", storage_quota_gb)
    ctx.callback.setCollectionAVU(new_project_path, "title", title)
    ctx.callback.setCollectionAVU(new_project_path, "OBI:0000103", principal_investigator)
    ctx.callback.setCollectionAVU(new_project_path, "dataSteward", data_steward)
    ctx.callback.setCollectionAVU(new_project_path, "responsibleCostCenter", resp_cost_center)
    ctx.callback.setCollectionAVU(new_project_path, "enableOpenAccessExport", open_access)
    ctx.callback.setCollectionAVU(new_project_path, "enableArchive", tape_archive)
    ctx.callback.setCollectionAVU(new_project_path, "enableUnarchive", tape_unarchive)
    ctx.callback.setCollectionAVU(new_project_path, "collectionMetadataSchemas", metadata_schemas)
    ctx.callback.setCollectionAVU(new_project_path, "enableContributorEditMetadata", "false")

    archive_dest_resc = ""
    for result in row_iterator("RESC_NAME",
                               "META_RESC_ATTR_NAME = 'archiveDestResc' AND META_RESC_ATTR_VALUE = 'true'",
                               AS_LIST,
                               ctx.callback):
        archive_dest_resc = result[0]
    if archive_dest_resc == "":
        ctx.callback.msiExit("-1", "ERROR: The attribute 'archiveDestResc' has no value in iCAT")

    ctx.callback.setCollectionAVU(new_project_path, "archiveDestinationResource", archive_dest_resc)

    # Set recursive permissions
    ctx.callback.msiSetACL("default", "write", "service-pid", new_project_path)
    ctx.callback.msiSetACL("default", "read", "service-disqover", new_project_path)
    ctx.callback.msiSetACL("recursive", "inherit", "", new_project_path)

    current_user = ctx.callback.get_client_username('')["arguments"][0]
    # If the user calling this function is someone other than 'rods' (so a project admin)
    # we need to add rods as a owner on this project and remove the person calling this method
    # from the ACLs
    if current_user != "rods":
        ctx.callback.msiSetACL("default", "own", "rods", new_project_path)
        ctx.callback.msiSetACL("default", "null", current_user, new_project_path)

    return {"project_path": new_project_path, "project_id": project}
