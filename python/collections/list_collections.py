@make(inputs=[0], outputs=[1], handler=Output.STORE)
def list_collections(ctx, project_path):
    """
    Get a listing of the all project's collections

    Parameters
    ----------
    ctx : Context
        Combined type of a callback and rei struct.
    project_path: str
        Project absolute path

    Returns
    -------
    list
        a json list of collections objects
    """
    # Initialize the collections dictionary
    project_collections = []

    proj_size = float(0)
    for proj_coll in row_iterator("COLL_NAME", "COLL_PARENT_NAME = '" + project_path + "'", AS_LIST, ctx.callback):
        # Calculate size for entire project
        coll_size = float(ctx.callback.get_collection_size(proj_coll[0], "B", "none", "")["arguments"][3])
        proj_size = proj_size + coll_size

        # Initialize the collections dictionary
        project_collection = {}

        project_collection["id"] = proj_coll[0].split("/")[4]

        # Get AVUs
        project_collection["size"] = coll_size
        project_collection["title"] = ctx.callback.getCollectionAVU(proj_coll[0], "title", "", "", FALSE_AS_STRING)["arguments"][2]
        project_collection["creator"] = ctx.callback.getCollectionAVU(proj_coll[0], "creator", "", "", FALSE_AS_STRING)["arguments"][2]
        project_collection["PID"] = ctx.callback.getCollectionAVU(proj_coll[0], "PID", "", "", FALSE_AS_STRING)["arguments"][2]
        project_collection["numFiles"] = ctx.callback.getCollectionAVU(proj_coll[0], "numFiles", "", "", FALSE_AS_STRING)["arguments"][
            2
        ]

        project_collections.append(project_collection)

    return project_collections
